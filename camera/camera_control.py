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
from typing import Any, Callable, TypeVar
from camera_interface import CameraInterface
import socket
from json import dumps, loads as json_loads
from typen import ArucoMarkerPos, ArucoMetaBroadcast, CamSettings, CamSettingsWithFilename

CamSet = TypeVar('CamSet', CamSettings, CamSettingsWithFilename)


class CameraControl:
    """
    The CameraControl class represents the main script for controlling the camera.

    It provides methods for starting and controlling the camera, taking photos,
    setting camera settings, and handling broadcast messages.

    Attributes:
        __conf (ConfigParser): The configuration parser object.
        __sock (socket.socket): The socket object for UDP communication.
        cam (CameraInterface): The camera interface object.

    Methods:
        __init__(self, conf: ConfigParser): Initializes the CameraControl object.
        shutdown(self): Shuts down the Raspberry Pi.
        run(self): Runs the camera.
        __check_settings(self, settings: CamSet | str) -> CamSet: Checks and converts camera settings.
        photo(self, settings: CamSettings | str): Takes a photo with the camera.
        set_settings(self, settings: CamSettings | str): Sets camera settings.
        __save(self, settings: CamSettingsWithFilename | str, aruco_callback: None | Callable[[list[ArucoMarkerPos], dict[str, Any]], None] = None): Saves a photo with the camera.
        preview(self, settings: CamSettings | str = {}): Takes a preview photo with the camera.
        focus(self, focus: float) -> str: Sets the focus of the camera.
        aruco(self) -> list[ArucoMarkerPos]: Finds ArUco markers in the camera image.
        __aruco_broadcast(self, addr: tuple[str, int], id: str): Broadcasts ArUco marker information.
        __send_aruco_data(self, addr: tuple[str, int], id: str, marker: list[ArucoMarkerPos], meta: dict[str, Any] = {}): Sends ArUco marker data to a client.
        meta(self) -> None | dict[str, int]: Gets camera metadata.
        pause(self): Pauses the camera.
        resume(self): Resumes the camera.
        say_moin(self): Sends a broadcast message.
        __receive_broadcast(self): Receives and processes broadcast messages.
        __take_focusstack(self, filename: str, addr: tuple[str, int]): Takes a focus stack of photos.
        __take_photo(self, data: str, addr: tuple[str, int]): Takes a photo with the camera.
        __answer(self, addr: str, msg: str): Sends an answer message to a client.
    """

    def __init__(self, conf: ConfigParser):
        """
        Constructor for the CameraControl class.

        Args:
            conf (ConfigParser): The configuration parser object.

        Returns:
            None
        """
        self.__conf = conf

        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.__sock.bind(
            ("0.0.0.0", int(self.__conf['both']['BroadCastPort'])))

        if not path.exists(self.__conf['kameras']['Folder']):
            makedirs(self.__conf['kameras']['Folder'])

        t = Thread(target=self.__receive_broadcast)
        t.start()

    def shutdown(self):
        """ 
        Shutdown Raspberry Pi.

        This method shuts down the Raspberry Pi by executing the shutdown command.
        It waits for 5 seconds before executing the command to allow any pending operations to complete.
        After the shutdown command is executed, the program exits with a status code of 0.

        """
        system("sleep 5s; sudo shutdown -h now")
        print("Shutdown Raspberry...")
        exit(0)

    def run(self):
        self.cam = CameraInterface(self.__conf['kameras']['Folder'])
        print("Moin")

    def __check_settings(self, settings: CamSet | str) -> CamSet:
        settingR: CamSet
        if isinstance(settings, str):
            settingR = json_loads(settings)
        else:
            settingR = settings
        return settingR

    def photo(self, settings: CamSettings | str):
        """
        Takes a photo with the camera using the specified settings.

        Parameters:
        - settings: Either a dictionary containing the camera settings, or a JSON string representing the settings.

        Returns:
        - The captured photo.

        """
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
        """
        Sets the camera settings.

        Parameters:
        - settings: A dictionary or a JSON string representing the camera settings.

        Returns:
        - The result of setting the camera settings.

        If `settings` is a dictionary, it is directly used as the camera settings.
        If `settings` is a JSON string, it is parsed into a dictionary using `json.loads`.
        If `settings` cannot be parsed into a dictionary, an empty dictionary is used as the camera settings.

        Example usage:
        ```
        camera.set_settings({'resolution': '1920x1080', 'fps': 30})
        ```

        or

        ```
        camera.set_settings('{"resolution": "1920x1080", "fps": 30}')
        ```
        """
        settingR: CamSettings
        if isinstance(settings, dict):
            settingR = settings
        else:
            try:
                settingR = json_loads(settings)
            except:
                settingR = {}
        return self.cam.set_settings(settingR)

    def __save(self, settings: CamSettingsWithFilename | str, aruco_callback: None | Callable[[list[ArucoMarkerPos], dict[str, Any]], None] = None):
        """
        Saves a picture using the specified settings.

        Args:
            settings (CamSettingsWithFilename | str): The settings for saving the picture. It can be either an instance of `CamSettingsWithFilename` or a JSON string representing the settings.
            aruco_callback (None | Callable[[list[ArucoMarkerPos], dict[str, Any]], None], optional): A callback function to be called after the picture is saved. Defaults to None.

        Returns:
            The result of the `save_picture` method of the `cam` object.

        """
        settingsR: CamSettingsWithFilename
        if isinstance(settings, str):
            settingsR = json_loads(settings)
        else:
            settingsR = settings
        return self.cam.save_picture(settingsR, aruco_callback=aruco_callback)

    def preview(self, settings: CamSettings | str = {}):
        settings = self.__check_settings(settings)
        return self.cam.make_picture(settings, preview=True)

    def focus(self, focus: float) -> str:
        return self.cam.focus(focus)

    def aruco(self) -> list[ArucoMarkerPos]:
        return self.cam.find_aruco()

    def __aruco_broadcast(self, addr: tuple[str, int], id: str):
        """
        Broadcasts Aruco information to the specified address.

        Args:
            addr (tuple[str, int]): The address to which the Aruco information should be broadcasted.
            id (str): The ID of the capture.

        Returns:
            None
        """
        print("Aruco: " + id, addr)

        def aruco_pic():
            self.__answer(addr[0], 'arucoImg:' + id +
                          ':' + socket.gethostname())
        marker = self.cam.find_aruco(aruco_pic)
        # open(self.conf['kameras']['Folder'] + id +
        #     '.json', 'w').write(dumps(m, indent=2))
        self.__send_aruco_data(addr, id, marker)

    def __send_aruco_data(self, addr: tuple[str, int], id: str, marker: list[ArucoMarkerPos], meta: dict[str, Any] = {}):
        data: ArucoMetaBroadcast = {"aruco": marker, "meta": meta}
        json_str = dumps(data, indent=None, separators=(",", ":"))
        self.__answer(addr[0], 'arucoReady:' + id + ':' +
                      socket.gethostname() + ':' + json_str)

    def meta(self) -> None | dict[str, int]:
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
                self.__conf['both']['BroadCastPort'])))

    def __receive_broadcast(self):
        """
        Receives and processes broadcast messages.

        This method continuously listens for broadcast messages and performs
        actions based on the received data. The actions include responding
        to specific commands, executing camera operations, and controlling
        the camera settings.

        The method runs in an infinite loop until the program is terminated.

        Returns:
            None
        """
        while True:
            data, addr = self.__sock.recvfrom(1024)
            data = data.decode("utf-8")
            print(addr, data)
            if data[:4] == 'Moin':
                pass
            elif data == 'search':
                self.__answer(addr[0], 'Moin:'+socket.gethostname())
            elif data[0:6] == 'aruco:':
                # Thread(target=self.aruco_broadcast,
                #       args=(addr, data[6:])).start()
                self.__aruco_broadcast(addr, data[6:])
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
                self.__take_photo(data, addr)
            elif data[:5] == 'stack':
                print("Fokusstack: ", data[6:])
                filename = data[6:]
                self.__take_focusstack(filename, addr)
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

    def __take_focusstack(self, filename: str, addr: tuple[str, int]):
        """
        Takes a focus stack of photos with different focus levels.

        Args:
            filename (str): The base filename for the photos.
            addr (tuple[str, int]): The address to send the photo completion message.

        Returns:
            None
        """
        for f in [1, 3, 4, 5]:
            cs: CamSettingsWithFilename = {
                'focus': f,
                'filename': filename + '_' + str(f) + '.jpg'}
            self.__save(cs)
            self.__answer(addr[0], 'photoDone:' + cs['filename'])

    def __take_photo(self, data: str, addr: tuple[str, int]):
        """
        Takes a photo with the camera.

        Args:
            data (str): The data received via broadcast (filename, focus).
            addr (tuple[str, int]): The address of the client.

        Returns:
            None
        """
        json: CamSettingsWithFilename
        try:
            json = json_loads(data[6:])
            id = json['filename']
            id = id[:id.rfind('.')]
        except:
            json = {'filename': data[6:] + '.jpg'}
            id = data[6:]

        def aruco_callback(data: list[ArucoMarkerPos], metadata: dict[str, Any]):
            self.__send_aruco_data(addr, id, data, metadata)
        self.__save(json, aruco_callback)
        self.__answer(addr[0], 'photoDone:' + id + ':' + json['filename'])

    def __answer(self, addr: str, msg: str):
        """
        Sends an answer message to the specified address.

        Args:
            addr (str): The address to send the message to.
            msg (str): The message to send.

        Returns:
            None
        """
        print("Answer: ", addr, msg)
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.sendto((msg).encode("utf-8"),
                        (addr, int(self.__conf['both']['BroadCastPort'])))
