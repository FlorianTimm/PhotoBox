#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@author: Florian Timm
@version: 2024.03.11
"""

import atexit
from queue import Queue
import socket
import pandas as pd
from common.logger import Logger

from flask import Flask, render_template
from threading import Thread
from time import sleep
import uuid
from os import system, makedirs, path
import requests
from json import loads as json_loads
from shutil import make_archive
from glob import glob
from os.path import basename
from cv2 import imread, imwrite
from json import dump as json_dump
from time import clock_settime, clock_gettime, CLOCK_REALTIME

from master.desktop_control_thread import DesktopControlThread
from master.camera_control_thread import CameraControlThread
from master.marker_check import MarkerChecker
from master.stoppable_thread import StoppableThread
from master.button_control import ButtonControl
from master.led_control import LedControl
from master.focus_stack import focus_stack

from typing import Any, Literal, NoReturn
from numpy.typing import NDArray
from numpy import uint8
from common.typen import ArucoMarkerPos, ArucoMetaBroadcast, Metadata, Point3D, ArucoMarkerCorners
from common.conf import Conf


class Control:
    __list_of_cameras: dict[str, str] = dict()
    __detected_markers: dict[str,
                             dict[str, list[ArucoMarkerPos]]] = dict()
    __system_is_stopping = False
    __pending_photo_count: dict[str, int] = {}
    __pending_download_count: dict[str, int] = {}
    __pending_aruco_count: dict[str, int] = {}
    __pending_photo_types: dict[str, Literal["photo", "stack"]] = {}
    __cams_in_standby = True
    __desktop_message_queue: Queue[str] = Queue()
    __marker: dict[int, ArucoMarkerCorners] = {}
    __metadata: dict[str, dict[str, Metadata]] = {}
    __camera_settings: dict[str, Any] = {}

    def __init__(self,  app: Flask) -> None:
        self.__webapp = app
        self.__conf = Conf().get()

        self.__camera_settings = {
            'exposure_sync': self.__conf['kameras']['ExposureSync'],
            'exposure_value': self.__conf['kameras']['ExposureValue']
        }

        if self.__camera_settings['exposure_value'] != 0:
            self.send_to_all(
                f'settings:{{"exposure_value":{self.__camera_settings["exposure_value"]}}}')

        if not path.exists(self.__conf['server']['Folder']):
            makedirs(self.__conf['server']['Folder'])

        self.__led_control = LedControl(self)
        self.__button_control = ButtonControl(self)
        self.__load_markers()
        Logger().info("Control started!")

    def start(self):
        self.thread_webinterface = StoppableThread(
            target=self.__webapp.run, args=('0.0.0.0', int(self.__conf['server']['WebPort'])))
        self.thread_webinterface.start()

        self.thread_camera_interface = CameraControlThread(self)
        self.thread_camera_interface.start()

        self.thread_desktop_interface = DesktopControlThread(
            self, self.__desktop_message_queue)
        self.thread_desktop_interface.start()

        self.search_cameras()
        atexit.register(self.__exit_handler)

    def search_cameras(self, send_search: bool = True) -> None:
        self.__list_of_cameras = dict()
        self.__led_control.starting()
        if send_search:
            self.send_to_all('search')

    def capture_photo(self, action: Literal['photo', 'stack'] = "photo",
                      id: str = "") -> str:
        if len(self.__list_of_cameras) == 0:
            self.send_to_desktop("No cameras found!")
            return "No cameras found!"
        if id == "":
            id = str(uuid.uuid4())
        self.__led_control.photo_light()

        self.send_to_desktop(f"photoStart: {id}")

        Thread(target=self.__capture_thread, args=(action, id)).start()
        return id

    def __capture_thread(self, action: Literal['photo', 'stack'], id: str):
        if 'exposure_sync' in self.__camera_settings:
            self.sync_exposure()

        photo_count = len(self.__list_of_cameras) * \
            (4 if action == "stack" else 1)
        self.__pending_photo_count[id] = photo_count
        self.__pending_download_count[id] = photo_count
        self.__pending_aruco_count[id] = photo_count
        self.__pending_photo_types[id] = action
        self.send_to_all(f'{action}:{id}')

    def sync_exposure(self):
        self.__led_control.photo_light()
        self.send_to_all('settings:{"shutter_speed":0}')
        sleep(1)

        et = 0
        count = 0
        for ip in self.__list_of_cameras.values():
            try:
                data = requests.get(
                    f"http://{ip}:{self.__conf['kameras']['WebPort']}/meta").json()['ExposureTime']
                print(data)
                et += data
                count += 1
            except Exception as e:
                Logger().error("Error getting lux: %s", e)
        if count > 0:
            et /= count
        et = int(et)
        self.__camera_settings['exposure_value'] = et
        self.send_to_all(
            f'settings:{{"shutter_speed":{et}}}')
        Logger().info("Exposure synced: %d", et)

    def send_to_desktop(self, message: str) -> None:
        self.__desktop_message_queue.put(message)

    def send_to_all(self, msg_str: str) -> None:
        msg = msg_str.encode("utf-8")
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM,
                           socket.IPPROTO_UDP) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.sendto(msg, ("255.255.255.255", int(
                self.__conf['both']['BroadCastPort'])))

    def found_camera(self, hostname: str, ip: str) -> None:
        if hostname in self.__list_of_cameras:
            return
        self.__list_of_cameras[hostname] = ip
        self.__led_control.status_led(5)
        if self.__camera_settings['exposure_value'] != 0:
            self.send_to_all(
                f'settings:{{"exposure_value":{self.__camera_settings["exposure_value"]}}}')

    def receive_photo(self, ip: str, id_lens: str, filename: str) -> None:
        global photo_count
        Logger().info("Photo received: %s", filename)
        id = id_lens.split("_")[0]
        Logger().info("Photo received: ID %s", id)
        if id not in self.__pending_photo_count:
            Logger().info("Error: Photo not requested!")
            return
        self.__pending_photo_count[id] -= 1
        hostname = self.__get_hostname(ip)
        if len(hostname) > 0:
            hostname = hostname[0]
        else:
            Logger().info("Error: Hostname not found!")
            return
        Thread(target=self.__download_photo, args=(
            ip, id, filename, hostname)).start()
        if self.__pending_photo_count[id] == 0:
            self.__led_control.status_led(1)
            del self.__pending_photo_count[id]
            Logger().info("All photos taken!")

    def __download_photo(self, ip: str, id: str,
                         name: str, hostname: str) -> None:
        """ collect photos """
        global download_count
        Logger().info("Downloading photo...")
        folder = self.__check_folder(id)

        Logger().info("Collecting photo from  %s...", hostname)
        try:
            url = "http://" + ip + ":" + \
                self.__conf["kameras"]['WebPort'] + "/bilder/" + name
            Logger().info(url)
            r = requests.get(url, allow_redirects=True)
            open(folder + hostname + name[36:], 'wb').write(r.content)
        except Exception as e:
            Logger().info("Error collecting photo from %s: %s", hostname, e)
        self.__pending_download_count[id] -= 1
        if self.__pending_download_count[id] == 0:
            self.all_images_downloaded(id, folder)

    def all_images_downloaded(self, id, folder):
        Logger().info("Collecting photos done!")
        del self.__pending_download_count[id]
        if self.__pending_photo_types[id] == "stack":
            self.__stack_photos(id)
        self.__led_control.photo_light()
        del self.__pending_photo_types[id]
        self.zip_and_send_folder(id, folder)

    def zip_and_send_folder(self, id, folder):
        Logger().info("Zipping folder...")
        if path.exists(self.__conf['server']['Folder'] + id + '.zip'):
            Logger().info("Info: Zip already exists!")
            return
        if id in self.__pending_download_count:
            return
        if id in self.__pending_photo_count:
            return
        if id in self.__pending_aruco_count:
            return
        if id in self.__pending_photo_types:
            return
        if not path.exists(folder):
            Logger().info("Error: Folder not found!")
            return

        """
        self.send_to_desktop(
            f"aruco:{id}:{socket.gethostname()}:{self.__conf['server']['WebPort']}/bilder/{id}/aruco.json")
        self.send_to_desktop(
            f"meta:{id}:{socket.gethostname()}:{self.__conf['server']['WebPort']}/bilder/{id}/meta.json")
        self.send_to_desktop(
            f"marker:{id}:{socket.gethostname()}:{self.__conf['server']['WebPort']}/bilder/{id}/marker.json")
        self.send_to_desktop(
            f"cameras:{id}:{socket.gethostname()}:{self.__conf['server']['WebPort']}/bilder/{id}/cameras.json")
        """

        make_archive(self.__conf['server']['Folder'] + id, 'zip', folder)
        self.send_to_desktop(
            f"photoZip:{id}:{socket.gethostname()}:{self.__conf['server']['WebPort']}/bilder/{id}.zip")
        Logger().info("Zip done!")

        self.check_and_copy_usb(id + '.zip')

    def check_and_copy_usb(self, file):
        try:
            if not path.exists('/dev/sda1'):
                Logger().info("USB not found!")
                return
            if not path.exists("/mnt/usb"):
                makedirs("/mnt/usb")
            if not path.ismount('/mnt/usb'):
                system('sudo mount /dev/sda1 /mnt/usb')

            file = self.__conf['server']['Folder'] + file
            Logger().info("Copy to USB...")
            system("cp " + file + " /mnt/usb")
            system("sync")
            system("sudo umount /dev/sda1")
        except Exception as e:
            Logger().error("Error copying to USB: %s", e)
        Logger().info("Copy to USB done!")

    def __check_folder(self, id):
        folder = self.__conf['server']['Folder'] + id + "/"
        if not path.exists(folder):
            makedirs(folder)
        return folder

    def __stack_photos(self, id: str) -> None:
        folder: str = self.__check_folder(id)
        imgs: list[str] = glob(folder + "*.jpg")
        groups: dict[str, list[NDArray[uint8]]] = {}
        imgs.sort()
        for i in imgs:
            name = basename(i)
            name = name.split("_")[0]
            if name not in groups:
                groups[name] = []
            groups[name].append(imread(i))  # type: ignore
        for camera, bilder in groups.items():
            imwrite(folder + camera + ".jpg", focus_stack(bilder))

    def find_aruco(self):
        Logger().info("Searching for Aruco...")
        id = str(uuid.uuid4())
        self.send_to_all('aruco:' + id)
        self.__pending_aruco_count[id] = len(self.__list_of_cameras)

    def receive_aruco(self, data: str) -> None:
        i1: int = data.find(":")
        i2: int = data[i1+1:].find(":")
        id: str = data[:i1]

        hostname: str = data[i1+1:i1+i2+1]
        if id not in self.__detected_markers:
            self.__detected_markers[id] = {}
        if id not in self.__metadata:
            self.__metadata[id] = {}
        j: ArucoMetaBroadcast = json_loads(data[i1+i2+2:])
        aruco = j['aruco']
        meta: Metadata = j['meta']  # type: ignore
        self.__detected_markers[id][hostname] = aruco
        self.__metadata[id][hostname] = meta
        self.__pending_aruco_count[id] -= 1

        if self.__pending_aruco_count[id] == 0:
            self.__all_aruco_received(id)

    def __all_aruco_received(self, id):
        Logger().info("Aruco done!")
        folder = self.__check_folder(id)

        json_dump(self.__metadata[id], open(
            folder + 'meta.json', "w"), indent=2)

        filter = MarkerChecker(
            self.__marker, self.__detected_markers[id], self.__metadata[id])
        self.__detected_markers[id] = filter.get_filtered_positions()
        self.__marker = filter.get_corrected_coordinates()
        cameras = filter.get_cameras()

        json_dump(self.__detected_markers[id], open(
            folder + 'aruco.json', "w"), indent=2)

        marker = {}
        for pid, corners in self.__marker.items():
            marker[pid] = {}
            for corner, pos in enumerate(corners):
                if pos is None:
                    continue
                marker[pid][corner] = [pos.x,  pos.y,  pos.z]
        Logger().info("Marker: %s", marker)

        json_dump(marker, open(
            folder + 'marker.json', "w"), indent=2)

        json_dump(cameras, open(
            folder + 'cameras.json', "w"), indent=2)

        del self.__pending_aruco_count[id]
        self.zip_and_send_folder(id, folder)

    def set_marker_from_csv(self, file, save=True) -> None:
        m = pd.read_csv(file)

        for _, r in m.iterrows():
            id = int(r['id'])

            if id not in self.__marker:
                self.__marker[id] = ArucoMarkerCorners()
            c = int(r['corner'])
            self.__marker[id][c] = Point3D(r['x'], r['y'], r['z'])
        if save:
            self.__save_markers()

    def __save_markers(self, ) -> None:
        with open(self.__conf['server']['Folder'] + "marker.csv", "w") as f:
            f.write("id,corner,x,y,z\n")
            for id, corners in self.__marker.items():
                for corner, pos in enumerate(corners):
                    if pos is None:
                        continue
                    f.write(f"{id},{corner},{pos.x},{pos.y},{pos.z}\n")

    def __load_markers(self, ) -> None:
        try:
            self.set_marker_from_csv(
                self.__conf['server']['Folder'] + "marker.csv", False)
            Logger().info("Marker loaded!")
        except Exception as e:
            Logger().error("Error loading marker! %s", e)

    def switch_pause_resume(self, ):
        if self.__cams_in_standby:
            self.pause()
        else:
            self.resume()

    def pause(self, ):
        self.__cams_in_standby = False
        self.send_to_all('pause')
        Thread(target=self.__led_control.running_light).start()

    def resume(self, ):
        if not self.__cams_in_standby:
            self.__cams_in_standby = True
            self.search_cameras(False)
            self.send_to_all('resume')

    # System-Control

    def set_time(self, time: int) -> str:
        clk_id: int = CLOCK_REALTIME
        alt: float = clock_gettime(clk_id)
        neu: float = float(time)/1000.
        if neu-alt > 10:
            clock_settime(clk_id, neu)
            return "updated: " + str(neu)
        return "keeped: " + str(alt)

    def system_control(self, action: Literal['shutdown', 'reboot']) -> NoReturn:
        """ Controls the system based on the action """
        self.send_to_all(action)
        self.__led_control.switch_off()
        if action == 'shutdown':
            system("sleep 5s; sudo shutdown -h now")
            Logger().info("Shutdown Raspberry...")
        elif action == 'reboot':
            system("sleep 5s; sudo reboot")
            Logger().info("Reboot Raspberry...")
        exit(0)

    def __exit_handler(self, ):
        self.__system_is_stopping = True
        sleep(1)
        self.thread_desktop_interface.stop()
        self.thread_webinterface.stop()
        self.thread_camera_interface.stop()

    def update(self, ):
        """ Update Skript """
        self.send_to_all('update')
        self.__led_control.waiting()
        Logger().info("Update Skript...")
        system("sudo git -C /home/photo/PhotoBox pull")
        self.__led_control.photo_light()
        return "Updated"

    def restart(self, ):
        """ Restart Skript """
        self.send_to_all('restart')
        self.__led_control.waiting()

        def restart_skript():
            system("sleep 5s; sudo systemctl restart PhotoBoxMaster.service")
            exit(1)
        Thread(target=restart_skript).start()
        Logger().info("Restart Skript...")
        return render_template('wait.htm', time=15, target_url="/", title="Restarting...")

    def set_config_from_web(self, config: dict) -> None:
        if 'color' in config:
            self.__led_control.set_photo_light_color(
                (int(config['color'][1:3], 16), int(config['color'][3:5], 16), int(config['color'][5:7], 16)))
        if 'exposure_sync' in config:
            self.__camera_settings['exposure_sync'] = config['exposure_sync']
        if 'exposure_value' in config:
            self.__camera_settings['exposure_value'] = config['exposure_value']
            self.send_to_all(
                f'settings:{{"exposure_value":{config["exposure_value"]}}}')

    # Getter

    def get_config_for_web(self, ) -> dict:
        c = {}

        c['color'] = '#%02x%02x%02x' % self.__led_control.get_photo_light_color()
        c['exposure_sync'] = self.__camera_settings['exposure_sync']
        c['exposure_value'] = self.__camera_settings['exposure_value']
        return c

    def get_hostnames(self, ) -> dict[str, str]:
        return dict(sorted(self.__list_of_cameras.items()))

    def get_cams_started(self) -> bool:
        return self.__cams_in_standby

    def get_leds(self) -> LedControl:
        return self.__led_control

    def __get_hostname(self, ip: str) -> list[str]:
        return [k for k, v in self.__list_of_cameras.items() if v == ip]

    def get_marker(self):
        return self.__marker

    def is_system_stopping(self):
        return self.__system_is_stopping

    def get_cameras(self):
        return self.__list_of_cameras

    def get_detected_markers(self):
        return self.__detected_markers
