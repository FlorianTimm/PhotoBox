#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@author: Florian Timm
@version: 2024.03.11
"""

from flask import Flask, make_response, request
from threading import Thread
from camera.camera_control import CameraControl
from json import dumps
from typing import TypeVar
from flask_cors import CORS

from common.typen import CamSettings, CamSettingsWithFilename, Config
from common.conf import Conf

CamSet = TypeVar("CamSet", CamSettings, CamSettingsWithFilename)

conf = Conf().load_conf()
LOGGER = Conf().get_logger()

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
    cc.pause()
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
    cc.resume()
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
    cc.shutdown()
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
        stream = cc.photo(settings)
        response = make_response(stream)
        response.headers.set('Content-Type', 'image/jpeg')
        return response
    focus = float(focus)
    stream = cc.photo({'focus': focus})
    response = make_response(stream)
    response.headers.set('Content-Type', 'image/jpeg')
    return response


@app.route('/settings/', methods=['GET', 'POST'])
@app.route('/settings/<focus>')
def settings(focus: float = -1):
    if request.method == 'POST':
        settings = request.get_json()
        cc.set_settings(settings)
        return 'ok'
    focus = float(focus)
    cc.focus(focus)
    return 'ok'


@app.route('/preview/')
@app.route('/preview/<focus>')
def preview(focus: float = -2):
    focus = float(focus)
    stream = cc.preview({'focus': focus})
    response = make_response(stream)
    response.headers.set('Content-Type', 'image/jpeg')
    return response


@app.route('/focus/')
@app.route('/focus/<focus>')
def focus(focus: float = -1):
    focus = float(focus)
    return cc.focus(focus)


@app.route('/aruco/')
@app.route('/aruco/<id>')
def aruco(id: str = ""):
    if id != "":
        return ""
    return dumps(cc.aruco(), indent=2)


@app.route('/meta/')
def meta():
    return dumps(cc.meta(), indent=2)


def start_web(conf: Config):
    """ start web control """
    LOGGER.info("Web server is starting...")
    app.run('0.0.0.0', conf['kameras']['WebPort'])


if __name__ == '__main__':

    cc = CameraControl(conf)
    w = Thread(target=start_web, args=(conf,))
    w.start()
    cc.run()

    cc.say_moin()
