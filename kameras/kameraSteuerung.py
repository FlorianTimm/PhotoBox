#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@author: Florian Timm
@version: 2023.09.21
"""

from flask import Flask, make_response, request
from threading import Thread
from configparser import ConfigParser
from os import system, makedirs, path
from sys import exit
from kamera import Kamera
import socket
from json import dumps, loads as json_loads
from typen import CamSettings, CamSettingsWithFilename, Config
from typing import TypeVar
from flask_cors import CORS

conf = ConfigParser()
conf.read("../config.ini")

CamSet = TypeVar("CamSet", CamSettings, CamSettingsWithFilename)


class KameraSteuerung:

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
        self.cam = Kamera(self.conf['kameras']['Folder'])
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
        open(conf['kameras']['Folder'] + id +
             '.json', 'w').write(dumps(m, indent=2))
        self.answer(addr[0], 'arucoReady:' + id + ':' + socket.gethostname())

    def meta(self) -> dict[str, int]:
        return self.cam.meta()

    def pause(self):
        self.cam.pause()

    def resume(self):
        self.cam.resume()
        say_moin()

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
                Thread(target=self.aruco_broadcast,
                       args=(addr, data[6:])).start()
                # self.aruco_broadcast(addr, data[6:])
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
                json: CamSettingsWithFilename
                try:
                    json = json_loads(data[6:])
                except:
                    json = {'filename': data[6:]}
                self.save(json)
                self.answer(addr[0], 'photo: ' + json['filename'])
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

    def answer(self, addr: str, msg: str):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.sendto((msg).encode("utf-8"), (addr, int(
                self.conf['both']['BroadCastPort'])))


# web control
app = Flask(__name__, static_url_path='/bilder',
            static_folder=conf['kameras']['Folder'])
CORS(app)


@app.route("/")
def web_index():
    """ index page of web control """
    output = """<html>
    <head>
        <title>Kamera</title>
        <meta name="viewport" content="width=device-width; initial-scale=1.0;" />
    </head>
    <body>
    <a href="./photo_view">Foto</a>
    <a href="./pause">Standby</a>

    </body>
    </html>"""

    return output


@app.route("/pause")
def web_pause():
    """ index page of web control """
    ks.pause()
    output = """<html>
    <head>
        <title>Kamera</title>
        <meta name="viewport" content="width=device-width; initial-scale=1.0;" />
    </head>
    <body>
    <a href="./resume">Resume</a>
    </body>
    </html>"""

    return output


@app.route("/resume")
def web_resume():
    """ index page of web control """
    ks.resume()
    output = """<html>
    <head>
        <title>Kamera</title>
        <meta http-equiv="refresh" content="0; URL=/">
    </head>
    <body>
    <a href="./">Index</a>
    </body>
    </html>"""

    return output


@app.route("/photo_view")
def photo_view():
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
            setInterval(updateImage, 10000);

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


@app.route('/photo/', methods=['GET', 'POST'])
@app.route('/photo/<focus>')
def photo(focus: float = -2):
    if request.method == 'POST':
        settings = request.get_json()
        stream = ks.photo(settings)
        response = make_response(stream)
        response.headers.set('Content-Type', 'image/jpeg')
        return response
    focus = float(focus)
    stream = ks.photo({'focus': focus})
    response = make_response(stream)
    response.headers.set('Content-Type', 'image/jpeg')
    return response


@app.route('/settings/', methods=['GET', 'POST'])
@app.route('/settings/<focus>')
def settings(focus: float = -1):
    if request.method == 'POST':
        settings = request.get_json()
        ks.set_settings(settings)
        return 'ok'
    focus = float(focus)
    ks.focus(focus)
    return 'ok'


@app.route('/preview/')
@app.route('/preview/<focus>')
def preview(focus: float = -2):
    focus = float(focus)
    stream = ks.preview({'focus': focus})
    response = make_response(stream)
    response.headers.set('Content-Type', 'image/jpeg')
    return response


@app.route('/focus/')
@app.route('/focus/<focus>')
def focus(focus: float = -1):
    focus = float(focus)
    return ks.focus(focus)


@app.route('/aruco/')
@app.route('/aruco/<id>')
def aruco(id=""):
    if id != "":
        return ""
    return dumps(ks.aruco(), indent=2)


@app.route('/meta/')
def meta():
    return dumps(ks.meta(), indent=2)


def start_web(conf: Config):
    """ start web control """
    print("Web server is starting...")
    app.run('0.0.0.0', conf['kameras']['WebPort'])


def say_moin():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(('Moin:'+socket.gethostname()).encode("utf-8"), ('255.255.255.255', int(
            ks.conf['both']['BroadCastPort'])))


if __name__ == '__main__':

    ks = KameraSteuerung(conf)
    w = Thread(target=start_web, args=(conf,))
    w.start()
    ks.run()

    say_moin()
