#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@author: Florian Timm
@version: 2024.03.11
"""

from os import PathLike
from common.logger import Logger
from socket import gethostname
from flask import Flask, Response, render_template, request, make_response, send_from_directory
from threading import Thread
from camera.camera_control import CameraControl
from json import dumps
from flask_cors import CORS
from common.conf import Conf

conf = Conf().get()

hostname = gethostname()
cc = CameraControl()

# web control
app = Flask(__name__, static_url_path='/bilder',
            static_folder=conf['kameras']['Folder'], template_folder='../template')
CORS(app)


@app.route("/static/<path:filename>")
def static_file(filename: PathLike[str] | str) -> Response:
    return send_from_directory("../template/static/", filename)


@app.route("/")
def web_index():
    """ index page of web control """
    return render_template('camera_index.htm', hostname=hostname, paused=cc.is_paused())


@app.route("/pause")
def web_pause():
    """ index page of web control """
    cc.pause()
    return render_template('wait.htm', target_url="/", time=1, title="Pause...")


@app.route("/resume")
def web_resume():
    cc.resume()
    return render_template('wait.htm', target_url="/", time=1, title="Resume...")


@app.route("/photo_view")
def photo_view():
    return render_template('camera_preview.htm', hostname=hostname)


@app.route("/shutdown")
def web_shutdown():
    """ web control: shutdown """
    cc.shutdown()
    return render_template('wait.htm', target_url="/", time=3, title="Shutting down...")


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


def start_web():
    """ start web control """
    Logger().info("Web server is starting...")
    conf = Conf().get()
    app.run('0.0.0.0', int(conf['kameras']['WebPort']))


if __name__ == '__main__':

    w = Thread(target=start_web)
    w.start()
    cc.run()

    cc.say_moin()
