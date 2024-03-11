#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@author: Florian Timm
@version: 2024.03.11
"""

from configparser import ConfigParser
from queue import Queue
import socket
from threading import Timer
from typing import TYPE_CHECKING

from master.stoppable_thread import StoppableThread

if TYPE_CHECKING:
    from master.control import Control

from common.conf import Conf
LOGGER = Conf().get_logger()


class DesktopControlThread(StoppableThread):
    """
    A thread class for controlling the connection to connector.

    Args:
        conf (ConfigParser): The configuration parser object.
        control: The control object.
        queue (Queue[str]): The queue object for storing messages.

    Attributes:
        conf (ConfigParser): The configuration parser object.
        queue (Queue[str]): The queue object for storing messages.
        control: The control object.

    Methods:
        __heartbeat: Sends a heartbeat signal to keep the connection alive.
        run: The main method that runs the thread.

    """

    def __init__(self, conf: ConfigParser, control: 'Control', queue: Queue[str]):
        StoppableThread.__init__(self)
        self.__conf = conf
        self.__queue = queue
        self.__control = control

    def __heartbeat(self):
        """
        Sends a heartbeat signal to keep the connection alive.
        """
        self.__queue.put("heartbeat")
        hb = Timer(5, self.__heartbeat)
        if not self.__control.is_system_stopping():
            hb.start()

    def run(self):
        """
        The main method that runs the thread.
        """
        di_socket = None
        conn = None
        hb = None

        try:
            di_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Bind to the port and listen for incoming connections
            free_port_found = False
            port = int(self.__conf['server']['DesktopPort'])

            while free_port_found == False:
                try:
                    di_socket.bind(("", port))
                    free_port_found = True
                    if port == int(self.__conf['server']['DesktopPort']):
                        LOGGER.info(
                            "DesktopControlThread is listening on port %s", port)
                    else:
                        LOGGER.warning(
                            "DesktopControlThread is listening on port %s because %s is already in use", port, self.__conf['server']['DesktopPort'])
                except OSError:
                    LOGGER.error("Port %s already in use",
                                 self.__conf['server']['DesktopPort'])
                    port += 1

            di_socket.listen()
            di_socket.settimeout(1)

            try:
                while self.__control.is_system_stopping() == False:
                    try:
                        conn, addr = di_socket.accept()
                    except socket.timeout:
                        continue
                    conn.settimeout(0.1)
                    self.__queue.queue.clear()
                    if hb:
                        hb.cancel()
                    # Heartbeat-Signal to keep the connection alive
                    hb = Timer(10, self.__heartbeat)
                    hb.start()

                    while self.__control.is_system_stopping() == False:
                        try:
                            if self.__queue.qsize() > 0:
                                conn.sendall(
                                    (self.__queue.get()+"\n").encode("utf-8"))

                            data = conn.recv(1024).decode("utf-8")
                            if data != "":
                                LOGGER.info(addr, data)

                            parts = data.split(":", 2)
                            match parts[0]:
                                case "Moin":
                                    LOGGER.info("Client connected")
                                    conn.sendall(bytes("Moin\n", "utf-8"))
                                case "time":
                                    self.__control.set_time(int(parts[1]))
                                case 'photo':
                                    id = ""
                                    if len(parts) > 1:
                                        id = parts[1]
                                    self.__control.capture_photo('photo', id)

                        except socket.timeout:
                            continue
                        except:
                            LOGGER.info("Client disconnected")
                            if hb:
                                hb.cancel()
                            break
            finally:
                if conn:
                    conn.close()
                if hb:
                    hb.cancel()
        finally:
            if di_socket:
                di_socket.close()
