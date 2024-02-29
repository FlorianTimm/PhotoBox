import atexit
from queue import Queue
import socket

from flask import Flask, render_template
from threading import Thread, Timer
import configparser
from time import sleep
import uuid
from os import system, makedirs, path
import requests
from json import loads as json_loads
from shutil import make_archive
from glob import glob
from typing import Literal, NoReturn
from os.path import basename
from cv2 import imread, imwrite

import focus_stack as focus_stack
from desktop_control_thread import DesktopControlThread
from camera_control_thread import CameraControlThread
from stoppable_thread import StoppableThread
from button_control import ButtonControl
from led_control import LedControl


class Control:
    list_of_cameras: dict[str, str] = dict()
    detected_markers: dict[str,
                           dict[str, list[dict[str, int | float]]]] = dict()
    system_is_stopping = False
    pending_photo_count: dict[str, int] = {}
    pending_download_count: dict[str, int] = {}
    pending_photo_types: dict[str, Literal["photo", "stack"]] = {}
    cams_in_standby = True
    desktop_message_queue: Queue[str] = Queue()

    def __init__(self, conf: configparser.ConfigParser, app: Flask) -> None:
        self.webapp = app
        self.conf = conf

        if not path.exists(self.conf['server']['Folder']):
            makedirs(self.conf['server']['Folder'])

        self.led_control = LedControl(self.conf, self)
        self.button_control = ButtonControl(self)

    def start(self):
        self.thread_webinterface = StoppableThread(
            target=self.webapp.run, args=('0.0.0.0', int(self.conf['server']['WebPort'])))
        self.thread_webinterface.start()

        self.thread_camera_interface = CameraControlThread(self.conf, self)
        self.thread_camera_interface.start()

        self.thread_desktop_interface = DesktopControlThread(
            self.conf, self, self.desktop_message_queue)
        self.thread_desktop_interface.start()

        self.search_cameras()
        atexit.register(self.exit_handler)

    def search_cameras(self, send_search=True) -> None:
        self.list_of_cameras = dict()
        self.led_control.starting()
        if send_search:
            self.send_to_all('search')

    def capture_photo(self, action: Literal['photo', 'stack'] = "photo", id: str = "") -> str:
        if len(self.list_of_cameras) == 0:
            self.send_to_desktop("No cameras found!")
            return "No cameras found!"
        if id == "":
            id = str(uuid.uuid4())
        self.led_control.photo_light()

        self.send_to_desktop(f"photoStart: {id}")

        Thread(target=self.capture_thread, args=(action, id)).start()
        return id

    def capture_thread(self, action: Literal['photo', 'stack'], id: str):
        self.pending_photo_count[id] = len(self.list_of_cameras) * \
            (4 if action == "stack" else 1)
        self.pending_download_count[id] = len(
            self.list_of_cameras) * (4 if action == "stack" else 1)
        self.pending_photo_types[id] = action
        self.send_to_all(f'{action}:{id}')
        sleep(1 if action == "photo" else 5)
        self.led_control.status_led()

    def send_to_desktop(self, message: str) -> None:
        self.desktop_message_queue.put(message)

    def send_to_all(self, msg) -> None:
        msg = msg.encode("utf-8")
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.sendto(msg, ("255.255.255.255", int(
                self.conf['both']['BroadCastPort'])))

    def found_camera(self, hostname, ip) -> None:
        if hostname in self.list_of_cameras:
            return
        self.list_of_cameras[hostname] = ip
        self.led_control.status_led(5)

    def receive_photo(self, ip, name) -> None:
        global photo_count
        print("Photo received: " + name)
        id = name[:36]
        self.pending_photo_count[id] -= 1
        hostname = self.get_hostname(ip)
        if len(hostname) > 0:
            hostname = hostname[0]
        else:
            print("Error: Hostname not found!")
            return
        Thread(target=self.download_photo, args=(
            ip, id, name, hostname)).start()
        if self.pending_photo_count[id] == 0:
            self.led_control.status_led()
            del self.pending_photo_count[id]
            print("All photos taken!")

    def download_photo(self, ip, id, name, hostname) -> None:
        """ collect photos """
        global download_count
        print("Downloading photo...")
        folder = self.conf['server']['Folder'] + id + "/"
        if not path.exists(folder):
            makedirs(folder)

        print("Collecting photo from " + hostname + "...")
        try:
            url = "http://" + ip + ":" + \
                self.conf["kameras"]['WebPort'] + "/bilder/" + name
            print(url)
            r = requests.get(url, allow_redirects=True)
            open(folder + hostname + name[36:], 'wb').write(r.content)
        except Exception as e:
            print("Error collecting photo from " + hostname + ":", e)
        self.pending_download_count[id] -= 1
        if self.pending_download_count[id] == 0:
            print("Collecting photos done!")
            del self.pending_download_count[id]
            if self.pending_photo_types[id] == "stack":
                pass
                self.stack_photos(id)
            del self.pending_photo_types[id]
            make_archive(self.conf['server']['Folder'] + id, 'zip', folder)
            self.led_control.photo_light()
            self.send_to_desktop(
                f"photoZip:{socket.gethostname()}:{self.conf['server']['WebPort']}/bilder/{id}.zip")

    def stack_photos(self, id) -> None:
        folder: str = self.conf['server']['Folder'] + id + "/"
        imgs: list[str] = glob(folder + "*.jpg")
        groups: dict[str, list] = {}
        imgs.sort()
        for i in imgs:
            name = basename(i)
            name = name.split("_")[0]
            if not name in groups:
                groups[name] = []
            groups[name].append(imread(i))
        for camera, bilder in groups.items():
            imwrite(folder + camera + ".jpg", focus_stack.focus_stack(bilder))

    def receive_aruco(self, data: str) -> None:
        global marker
        i1: int = data.find(":")
        i2: int = data[i1+1:].find(":")
        id: str = data[:i1]

        hostname: str = data[i1+1:i1+i2+1]
        if not hostname in self.detected_markers:
            self.detected_markers[hostname] = {}
        j: list[dict[str, int | float]] = json_loads(data[i1+i2+2:])
        self.detected_markers[hostname][id] = j

    def switch_pause_resume(self, ):
        if self.cams_in_standby:
            self.pause()
        else:
            self.resume()

    def pause(self, ):
        self.cams_in_standby = False
        self.send_to_all('pause')
        Thread(target=self.led_control.running_light).start()

    def resume(self, ):
        if not self.cams_in_standby:
            self.cams_in_standby = True
            self.search_cameras(False)
            self.send_to_all('resume')

    # System-Control

    def system_control(self, action: Literal['shutdown', 'reboot']) -> NoReturn:
        """ Controls the system based on the action """
        self.send_to_all(action)
        self.led_control.switch_off()
        if action == 'shutdown':
            system("sleep 5s; sudo shutdown -h now")
            print("Shutdown Raspberry...")
        elif action == 'reboot':
            system("sleep 5s; sudo reboot")
            print("Reboot Raspberry...")
        exit(0)

    def exit_handler(self, ):
        self.system_is_stopping = True
        sleep(1)
        self.thread_desktop_interface.stop()
        self.thread_webinterface.stop()
        self.thread_camera_interface.stop()

    def update(self, ):
        """ Update Skript """
        self.send_to_all('update')
        self.led_control.waiting()
        print("Update Skript...")
        system("sudo git -C /home/photo/PhotoBox pull")
        self.led_control.photo_light()
        return "Updated"

    def restart(self, ):
        """ Restart Skript """
        self.send_to_all('restart')
        self.led_control.waiting()

        def restart_skript():
            system("sleep 5s; sudo systemctl restart PhotoBoxMaster.service")
            exit(1)
        Thread(target=restart_skript).start()
        print("Restart Skript...")
        return render_template('wait.htm', time=15, target_url="/", title="Restarting...")

    # Getter

    def get_hostnames(self, ) -> dict:
        print("get_hostnames")
        return dict(sorted(self.list_of_cameras.items()))

    def get_cams_started(self) -> bool:
        return self.cams_in_standby

    def get_leds(self) -> LedControl:
        return self.led_control

    def get_hostname(self, ip) -> list[str]:
        print(self.list_of_cameras)
        print(ip)
        return [k for k, v in self.list_of_cameras.items() if v == ip]
