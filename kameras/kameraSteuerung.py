#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@author: Florian Timm
@version: 2023.09.21
"""

from flask import Flask, make_response
from threading import Thread
from configparser import ConfigParser
from os import system, makedirs, path
from sys import exit
from kamera import Kamera
import socket
from time import sleep
from json import dumps, loads as json_loads
from typen import CamSettings, CamSettingsWithFilename

conf = ConfigParser()
conf.read("../config.ini")


class KameraSteuerung:

    """ main script for automatic start """

    def __init__(self, conf):
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
        self.cam = Kamera(self.conf['kameras']['Folder'])
        print("Moin")

    def check_settings(self, settings: CamSettings | str = {}) -> CamSettings | CamSettingsWithFilename:
        if type(settings) == str:
            settings = json_loads(settings)
        return settings

    def photo(self, settings: CamSettings | str):
        try:
            settings = json_loads(settings)
        except:
            settings = {}

        return self.cam.make_picture(settings)

    def save(self, settings: CamSettingsWithFilename | str):
        settings = self.check_settings(settings)
        return self.cam.save_picture(settings)

    def preview(self, settings: CamSettings | str = {}):
        settings = self.check_settings(settings)
        return self.cam.make_picture(settings, preview=True)

    def focus(self, focus):
        return self.cam.focus()

    def aruco(self):
        return self.cam.aruco()

    def meta(self):
        return self.cam.meta()

    def receive_broadcast(self):
        while True:
            data, addr = self.sock.recvfrom(1024)
            data = data.decode("utf-8")
            print(addr)
            if data[:4] == 'Moin':
                pass
            elif data == 'search':
                self.answer(addr[0], 'Moin:'+socket.gethostname())
            elif data[0:5] == 'focus':
                z = -1
                try:
                    z = float(data[6:])
                except:
                    pass
                print("Focus: " + str(z))
                self.focus(z)  # Autofokus
            elif data[:5] == 'photo':
                print(photo)
                try:
                    json = json_loads(data[6:])
                    print("Erfolgreich geparst", json)
                except:
                    json = {'filename': data[6:]}
                self.save(json)
                self.answer(addr[0], 'photo: ' + json['filename'])
            elif data == 'preview':
                self.preview({'focus': -2})  # preview
            elif data == 'shutdown':
                self.shutdown()
            elif data == 'reboot':
                system("sleep 5s; sudo reboot")
                print("Reboot Raspberry...")
                exit(0)
            elif data == 'restart':
                system("systemctl restart PhotoBoxKamera.service")
                print("Restart Script...")
                exit(1)
            else:
                print("Unknown command: " + data)

    def answer(self, addr, msg):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.sendto((msg).encode("utf-8"), (addr, int(
                self.conf['both']['BroadCastPort'])))


# web control
app = Flask(__name__, static_url_path='/bilder',
            static_folder=conf['kameras']['Folder'])


@app.route("/")
def web_index():
    """ index page of web control """
    output = """<html>
    <head>
        <title>Kamera</title>
        <meta name="viewport" content="width=device-width; initial-scale=1.0;" />
    </head>
    <body>
    <script>
        window.onload = function() {
            let image = document.getElementById("img");

            function updateImage() {
                image.src = "preview/-2?" + new Date().getTime();
            }
            setInterval(updateImage, 1000);

            let focus = document.getElementById("focus");
            focus.onclick= function() {
                fetch("focus/-1")
            }
        }   
    </script>
    <a href="./photo"><img id="img" src="preview/-2" width="640" height="480" /></a>
    <br /><button id="focus">Autofokus</button>
    </body>
    </html>"""

    return output


@app.route("/shutdown")
def web_shutdown():
    """ web control: shutdown """
    ks.shutdown()
    return """
    <meta http-equiv="refresh" content="3; URL=/">
    Shutdown..."""


"""@app.route('/stream.mjpg')
def stream():
    return Response(ks.cam.streaming(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')
"""


@app.route('/photo/')
@app.route('/photo/<focus>')
def photo(focus=-1):
    focus = float(focus)
    stream = ks.photo({'focus': focus})
    response = make_response(stream)
    response.headers.set('Content-Type', 'image/jpeg')
    return response


@app.route('/preview/')
@app.route('/preview/<focus>')
def preview(focus=-2):
    focus = float(focus)
    stream = ks.preview({'focus': focus})
    response = make_response(stream)
    response.headers.set('Content-Type', 'image/jpeg')
    return response


@app.route('/focus/')
@app.route('/focus/<focus>')
def focus(focus=-1):
    focus = float(focus)
    return ks.focus(focus)


@app.route('/aruco/')
def aruco():
    return dumps(ks.aruco(), indent=2)


@app.route('/meta/')
def meta():
    return dumps(ks.meta(), indent=2)


def start_web(conf):
    """ start web control """
    print("Web server is starting...")
    app.run('0.0.0.0', conf['kameras']['WebPort'])


if __name__ == '__main__':

    ks = KameraSteuerung(conf)
    w = Thread(target=start_web, args=(conf,))
    w.start()
    ks.run()

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(('Moin:'+socket.gethostname()).encode("utf-8"), ('255.255.255.255', int(
            ks.conf['both']['BroadCastPort'])))
