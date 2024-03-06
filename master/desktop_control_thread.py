
from configparser import ConfigParser
from queue import Queue
import socket
from threading import Timer

from master.stoppable_thread import StoppableThread


class DesktopControlThread(StoppableThread):
    def __init__(self, conf: ConfigParser, control, queue: Queue[str]):
        StoppableThread.__init__(self)
        self.conf = conf
        self.queue = queue
        self.control = control

    def heartbeat(self):
        self.queue.put("heartbeat")
        hb = Timer(5, self.heartbeat)
        if not self.control.system_is_stopping:
            hb.start()

    def run(self):
        di_socket = None
        conn = None
        hb = None

        try:
            di_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            di_socket.bind(("", int(self.conf['server']['DesktopPort'])))
            di_socket.listen()
            di_socket.settimeout(1)

            try:
                while self.control.system_is_stopping == False:
                    try:
                        conn, addr = di_socket.accept()
                    except socket.timeout:
                        continue
                    conn.settimeout(0.1)
                    self.queue.queue.clear()
                    if hb:
                        hb.cancel()
                    # Heartbeat-Signal to keep the connection alive
                    hb = Timer(10, self.heartbeat)
                    hb.start()

                    while self.control.system_is_stopping == False:
                        try:
                            if self.queue.qsize() > 0:
                                conn.sendall(
                                    (self.queue.get()+"\n").encode("utf-8"))

                            data = conn.recv(1024).decode("utf-8")
                            if data != "":
                                print(addr, data)

                            parts = data.split(":", 2)
                            match parts[0]:
                                case "Moin":
                                    print("Client connected")
                                    conn.sendall(bytes("Moin\n", "utf-8"))
                                case "time":
                                    self.control.set_time(parts[1])
                                case 'photo':
                                    id = ""
                                    if len(parts) > 1:
                                        id = parts[1]
                                    self.control.capture_photo('photo', id)

                        except socket.timeout:
                            continue
                        except:
                            print("Client disconnected")
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
