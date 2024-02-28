#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@author: Florian Timm
@version: 2024.02.28
"""

from threading import Thread
from configparser import ConfigParser
from os import system, makedirs, path
from sys import exit
from typing import TypeVar
from kameras.camera_interface import CameraInterface
import socket
from json import dumps, loads as json_loads
from typen import CamSettings, CamSettingsWithFilename

CamSet = TypeVar('CamSet', CamSettings, CamSettingsWithFilename)


class CameraControl:

    """ main script for automatic start """

    def __init__(self, conf: ConfigParser):
        """
        Constructor
        """
        print("Kamerasteuerung\n")

        # load config file

        self.conf = conf

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.sock.bind(("0.0.0.0", int(self.conf['both']['BroadCastPort'])))

        if not path.exists(self.conf['kameras']['Folder']):
            makedirs(self.conf['kameras']['Folder'])

        t = Thread(target=self.receive_broadcast)
        t.start()

    def shutdown(self):
        """ Shutdown Raspberry Pi """
        system("sleep 5s; sudo shutdown -h now")
        print("Shutdown Raspberry...")
        exit(0)

    def run(self):
        self.cam = CameraInterface(self.conf['kameras']['Folder'])
        print("Moin")

    def check_settings(self, settings: CamSet | str) -> CamSet:
        settingR: CamSet
        if isinstance(settings, str):
            settingR = json_loads(settings)
        else:
            settingR = settings
        return settingR

    def photo(self, settings: CamSettings | str):
        settingR: CamSettings
        if isinstance(settings, dict):
            settingR = settings
        else:
            try:
                settingR = json_loads(settings)
            except:
                settingR = {}
        return self.cam.make_picture(settingR)

    def set_settings(self, settings: CamSettings | str):
        settingR: CamSettings
        if isinstance(settings, dict):
            settingR = settings
        else:
            try:
                settingR = json_loads(settings)
            except:
                settingR = {}
        return self.cam.set_settings(settingR)

    def save(self, settings: CamSettingsWithFilename | str):
        settingsR: CamSettingsWithFilename
        if isinstance(settings, str):
            settingsR = json_loads(settings)
        else:
            settingsR = settings
        return self.cam.save_picture(settingsR)

    def preview(self, settings: CamSettings | str = {}):
        settings = self.check_settings(settings)
        return self.cam.make_picture(settings, preview=True)

    def focus(self, focus: float) -> str:
        return self.cam.focus(focus)

    def aruco(self) -> list[dict[str, int | float]]:
        return self.cam.aruco()

    def aruco_broadcast(self, addr, id):
        print("Aruco: " + id, addr)

        def aruco_pic():
            self.answer(addr[0], 'arucoImg:' + id + ':' + socket.gethostname())
        m = self.cam.aruco(aruco_pic)
        open(self.conf['kameras']['Folder'] + id +
             '.json', 'w').write(dumps(m, indent=2))
        self.answer(addr[0], 'arucoReady:' + id + ':' + socket.gethostname())

    def meta(self) -> dict[str, int]:
        return self.cam.meta()

    def pause(self):
        self.cam.pause()

    def resume(self):
        self.cam.resume()
        self.say_moin()

    def say_moin(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.sendto(('Moin:'+socket.gethostname()).encode("utf-8"), ('255.255.255.255', int(
                self.conf['both']['BroadCastPort'])))

    def receive_broadcast(self):
        while True:
            data, addr = self.sock.recvfrom(1024)
            data = data.decode("utf-8")
            print(addr, data)
            if data[:4] == 'Moin':
                pass
            elif data == 'search':
                self.answer(addr[0], 'Moin:'+socket.gethostname())
            elif data[0:6] == 'aruco:':
                # Thread(target=self.aruco_broadcast,
                #       args=(addr, data[6:])).start()
                self.aruco_broadcast(addr, data[6:])
            elif data[0:5] == 'focus':
                z = -1
                try:
                    z = float(data[6:])
                except:
                    pass
                print("Focus: " + str(z))
                self.focus(z)  # Autofokus
            elif data[:5] == 'photo':
                print("Einstellung", data[6:])
                self.take_photo(data, addr)
            elif data[:5] == 'stack':
                print("Fokusstack: ", data[6:])
                filename = data[6:]
                self.take_focusstack(filename, addr)
            elif data[:8] == 'settings':
                print("Einstellung", data[9:])
                jsonSettings: CamSettings
                try:
                    jsonSettings = json_loads(data[9:])
                except:
                    jsonSettings = {}
                self.set_settings(jsonSettings)
            elif data == 'preview':
                self.preview({'focus': -2})  # preview
            elif data == 'shutdown':
                self.shutdown()
            elif data == 'pause':
                self.pause()
            elif data == 'resume':
                self.resume()
            elif data == 'reboot':
                system("sleep 5s; sudo reboot")
                print("Reboot Raspberry...")
                exit(0)
            elif data == 'restart':
                system("systemctl restart PhotoBoxKamera.service")
                print("Restart Script...")
                exit(1)
            elif data == 'update':
                print("Update Script...")
                system("sudo git -C /home/photo/PhotoBox pull")
            else:
                print("Unknown command: " + data)

    def take_focusstack(self, filename, addr):
        for f in [1, 3, 4, 5]:
            cs: CamSettingsWithFilename = {
                'focus': f,
                'filename': filename + '_' + str(f) + '.jpg'}
            self.save(cs)
            self.answer(addr[0], 'photoDone:' + cs['filename'])

    def take_photo(self, data, addr):
        json: CamSettingsWithFilename
        try:
            json = json_loads(data[6:])
        except:
            json = {'filename': data[6:] + '.jpg'}
        self.save(json)
        self.answer(addr[0], 'photoDone:' + json['filename'])

    def answer(self, addr: str, msg: str):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.sendto((msg).encode("utf-8"), (addr, int(
                self.conf['both']['BroadCastPort'])))
