from configparser import ConfigParser
import socket
from threading import Thread
from stoppable_thread import StoppableThread

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from control import Control


class CameraControlThread(StoppableThread):
    def __init__(self, conf: ConfigParser,  control: Control) -> None:
        StoppableThread.__init__(  # type: ignore
            self, name="CameraControlThread")
        self.control = control
        self.conf = conf

    def run(self):
        socket_rec = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        socket_rec.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        socket_rec.bind(("0.0.0.0", int(self.conf['both']['BroadCastPort'])))
        while self.control.system_is_stopping == False:
            # sock.sendto(bytes("hello", "utf-8"), ip_co)
            data, addr = socket_rec.recvfrom(1024)
            print("received message: %s" % data)
            print(addr)
            data = data.decode("utf-8")
            print(addr[0] + ": " + data)
            if data[:4] == 'Moin':
                Thread(target=self.control.found_camera,
                       args=(data[5:], addr[0])).start()
            elif data[:10] == 'photoDone:':
                self.control.receive_photo(addr[0], data[10:])
            elif data[:11] == 'arucoReady:':
                print(data)
                self.control.receive_aruco(data[11:])
            elif data[:5] == 'light':
                self.control.get_leds().photo_light()
        socket_rec.close()
