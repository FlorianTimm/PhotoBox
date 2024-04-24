#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@author: Florian Timm
@version: 2024.03.11
"""

from threading import Thread
from os import system, makedirs, path
from sys import exit
from typing import Any, Callable
from common.logger import Logger
from camera.camera_interface import CameraInterface
import socket
from json import JSONDecodeError, dumps, loads as json_loads
from common.typen import ArucoMarkerPos, ArucoMetaBroadcast, CamSettings, CamSettingsWithFilename, Metadata
from common.conf import Conf


class CameraControl:
    '''
    This class is used to control the camera and perform various operations such as taking photos, setting camera settings, and broadcasting Aruco information.

    Attributes:
    - __sock: socket.socket
    - __cam: CameraInterface

    Methods:
    + __init__()
    - run()
    - __check_settings(settings: CamSettings | str): CamSettings
    + photo(settings: CamSettings | str): bytes
    + set_settings(settings: CamSettings | str): CamSettings
    - __save(settings: CamSettingsWithFilename | str,
            aruco_callback: None | Callable[[list[ArucoMarkerPos],
            dict[str, Any]], None] = None):
            tuple[str, dict[str, Any]]
    + preview(settings: CamSettings | str = {}): bytes
    + focus(focus: float): str
    + aruco():list[ArucoMarkerPos]
    - __aruco_broadcast(addr: tuple[str, int], id: str)
    - __send_aruco_data(addr: tuple[str, int], id: str,
            marker: list[ArucoMarkerPos], meta: dict[str, Any] = {})
    + meta():None | dict[str, int]
    + pause()
    + resume()
    + shutdown()
    + say_moin()
    - __receive_broadcast()
    - __take_focusstack(id: str, addr: tuple[str, int])
    - __take_photo(data: str, addr: tuple[str, int])
    - __answer(addr: str, msg: str)
    '''

    __sock: socket.socket
    __cam: CameraInterface

    def __init__(self):
        """
        Constructor for the CameraControl class.
        """
        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.__sock.bind(
            ("255.255.255.255", int(Conf().get()['both']['BroadCastPort'])))

        if not path.exists(Conf().get()['kameras']['Folder']):
            makedirs(Conf().get()['kameras']['Folder'])

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
        Logger().info("Shutdown Raspberry...")
        exit(0)

    def run(self):
        self.__cam = CameraInterface(Conf().get()['kameras']['Folder'])
        Logger().info("Moin")

    def __check_settings(self, settings: CamSettings | str) -> CamSettings:
        """
        Checks the camera settings.

        Parameters:
        - settings: A dictionary or a JSON string representing the camera settings.

        Returns:
        - The camera settings.

        If `settings` is a dictionary, it is directly used as the camera settings.
        If `settings` is a JSON string, it is parsed into a dictionary using `json.loads`.
        """
        settingR: CamSettings
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
            except JSONDecodeError:
                settingR = {}
        return self.__cam.make_picture(settingR)

    def set_settings(self, settings: CamSettings | str) -> CamSettings:
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
            except JSONDecodeError:
                settingR = {}
        return self.__cam.set_settings(settingR)

    def __save(self, settings: CamSettingsWithFilename | str, aruco_callback: None | Callable[[list[ArucoMarkerPos], Metadata], None] = None) -> tuple[str, dict[str, Any]]:
        """
        Saves a picture using the specified settings.

        Args:
            settings (CamSettingsWithFilename | str): The settings for saving the picture. It can be either an instance of `CamSettingsWithFilename` or a JSON string representing the settings.
            aruco_callback (None | Callable[[list[ArucoMarkerPos], dict[str, Any]], None], optional): A callback function to be called after the picture is saved. Defaults to None.

        Returns:
            tuple[str, Metadata]: The filename and metadata of the saved picture.

        """
        settingsR: CamSettingsWithFilename
        if isinstance(settings, str):
            settingsR = json_loads(settings)
        else:
            settingsR = settings
        return self.__cam.save_picture(settingsR, aruco_callback=aruco_callback)

    def preview(self, settings: CamSettings | str = {}):
        settings = self.__check_settings(settings)
        return self.__cam.make_picture(settings, preview=True)

    def focus(self, focus: float) -> str:
        return self.__cam.focus(focus)

    def aruco(self) -> list[ArucoMarkerPos]:
        return self.__cam.find_aruco()

    def __aruco_broadcast(self, addr: tuple[str, int], id: str):
        """
        Broadcasts Aruco information to the specified address.

        Args:
            addr (tuple[str, int]): The address to which the Aruco information should be broadcasted.
            id (str): The ID of the capture.

        Returns:
            None
        """
        Logger().info("Aruco: %s %s", id, addr)

        def aruco_pic():
            self.__answer(addr[0], 'arucoImg:' + id +
                          ':' + socket.gethostname())
        marker = self.__cam.find_aruco(aruco_pic)
        # open(self.conf['kameras']['Folder'] + id +
        #     '.json', 'w').write(dumps(m, indent=2))
        self.__send_aruco_data(addr, id, marker)

    def __send_aruco_data(self, addr: tuple[str, int], id: str, marker: list[ArucoMarkerPos], meta: Metadata = {}):
        data: ArucoMetaBroadcast = {"aruco": marker, "meta": meta}
        json_str = dumps(data, indent=None, separators=(",", ":"))
        self.__answer(addr[0], 'arucoReady:' + id + ':' +
                      socket.gethostname() + ':' + json_str)

    def meta(self) -> None | dict[str, int]:
        return self.__cam.meta()

    def pause(self):
        self.__cam.pause()

    def resume(self):
        self.__cam.resume()
        self.say_moin()

    def is_paused(self):
        return self.__cam.is_paused()

    def say_moin(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.sendto(('Moin:'+socket.gethostname()).encode("utf-8"), ('255.255.255.255', int(
                Conf().get()['both']['BroadCastPort'])))

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
            Logger().info("%s %s", addr, data)
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
                except ValueError:
                    pass
                Logger().info("Focus: %s", z)
                self.focus(z)  # Autofokus
            elif data[:5] == 'photo':
                Logger().info("Einstellung %s", data[6:])
                self.__take_photo(data, addr)
            elif data[:5] == 'stack':
                Logger().info("Fokusstack: %s", data[6:])
                filename = data[6:]
                self.__take_focusstack(filename, addr)
            elif data[:8] == 'settings':
                Logger().info("Einstellung %s", data[9:])
                jsonSettings: CamSettings
                try:
                    jsonSettings = json_loads(data[9:])
                except JSONDecodeError:
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
                Logger().info("Reboot Raspberry...")
                exit(0)
            elif data == 'restart':
                system("systemctl restart PhotoBoxCamera.service")
                Logger().info("Restart Script...")
                exit(1)
            elif data == 'update':
                Logger().info("Update Script...")
                system("sudo git -C /home/photo/PhotoBox pull")
            else:
                Logger().warning("Unknown command: %s", data)

    def __take_focusstack(self, id: str, addr: tuple[str, int]):
        """
        Takes a focus stack of photos with different focus levels.

        Args:
            filename (str): The base filename for the photos.
            addr (tuple[str, int]): The address to send the photo completion message.

        Returns:
            None
        """

        metadata: dict[str, dict[str, Any]] = {}

        for f in [1, 3, 4, 5]:
            filename = id + '_' + str(f) + '.jpg'
            cs: CamSettingsWithFilename = {
                'focus': f,
                'filename': filename}
            _, md = self.__save(cs)
            metadata[filename] = md
            self.__answer(addr[0], 'photoDone:' +
                          filename + ':' + cs['filename'])

        Logger().info("Focusstack: %s", metadata)
        for f, m in metadata.items():
            def aruco_callback(data: list[ArucoMarkerPos], metadata: Metadata):
                self.__send_aruco_data(addr, id, data, metadata)
            self.__cam.aruco_search_in_background_from_file(
                f, m, aruco_callback)

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
        except JSONDecodeError:
            json = {'filename': data[6:] + '.jpg'}
            id = data[6:]

        def aruco_callback(data: list[ArucoMarkerPos], metadata: Metadata):
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
        Logger().info("Answer:  %s %s", addr, msg)
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.sendto((msg).encode("utf-8"),
                        (addr, int(Conf().get()['both']['BroadCastPort'])))
