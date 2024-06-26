#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@author: Florian Timm
@version: 2024.03.11
"""

import socket
from threading import Thread
from common.logger import Logger
from master.stoppable_thread import StoppableThread

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from master.control import Control

from common.conf import Conf


class CameraControlThread(StoppableThread):
    def __init__(self,  control: 'Control') -> None:
        StoppableThread.__init__(  # type: ignore
            self, name="CameraControlThread")
        self.__control = control
        self.__conf = Conf().get()

    def run(self):
        """
        Executes the main logic of the camera control thread.

        This method listens for incoming messages on a UDP socket and performs
        actions based on the received data. It runs in a loop until the system
        is stopping.

        Returns:
            None
        """

        socket_rec = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        socket_rec.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        port = int(self.__conf['both']['BroadCastPort'])
        free_port_found = False
        while free_port_found is False:
            try:
                socket_rec.bind(("0.0.0.0", port))
                free_port_found = True
                if port == int(self.__conf['both']['BroadCastPort']):
                    Logger().info(
                        "CameraControlThread is listening on port %s", port)
                else:
                    Logger().info("CameraControlThread is listening on ",
                                  "port %s", port, "because port",
                                  self.__conf['both']['BroadCastPort'],
                                  "was already in use")
            except OSError:
                Logger().error("Port %s already in use", port)
                port += 1
        while self.__control.is_system_stopping() is False:
            # sock.sendto(bytes("hello", "utf-8"), ip_co)
            data, addr = socket_rec.recvfrom(10000)
            Logger().info("received message: %s", data)
            Logger().info(addr)
            data = data.decode("utf-8")
            Logger().info("%s: %s", addr[0], data)
            if data[:4] == 'Moin':
                Thread(target=self.__control.found_camera,
                       args=(data[5:], addr[0])).start()
            elif data[:10] == 'photoDone:':
                data = data[10:].split(":", 2)
                self.__control.receive_photo(addr[0], data[0], data[1])
            elif data[:11] == 'arucoReady:':
                Logger().info(data)
                self.__control.receive_aruco(data[11:])
            elif data[:5] == 'light':
                self.__control.get_leds().photo_light()
        socket_rec.close()
