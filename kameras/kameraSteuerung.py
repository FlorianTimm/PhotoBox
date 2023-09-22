#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@author: Florian Timm
@version: 2023.09.21
"""

from flask import Flask, request, send_file, Response, make_response
from threading import Thread
import configparser
from os import system
from sys import exit
from kamera import Kamera


import io
from threading import Condition


class KameraSteuerung:

    """ main script for automatic start """

    def __init__(self, web_interface):
        """
        Constructor
        :param web_interface: Thread with Flask web interface
        :type web_interface: Thread
        """
        print("Kamerasteuerung\n")

        # load config file
        self.__conf = configparser.ConfigParser()
        self.__conf.read("config.ini")

    def shutdown(self):
        """ Shutdown Raspberry Pi """
        self.stop_children()
        system("sleep 5s; sudo shutdown -h now")
        print("Shutdown Raspberry...")
        exit(0)

    def run(self):
        self.cam = Kamera()  # flip pi camera if upside down.
        print("Moin")

    # def stream(self):
    #    while True:
    #        frame = self.cam.get_frame()
    #        yield (b'--frame\r\n'
    #            b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

    def photo(self, focus):
        return self.cam.make_picture(focus)


# web control
app = Flask(__name__)


@app.route("/")
def web_index():
    """ index page of web control """
    output = """<html>
    <head>
        <title>Kamera</title>
        <meta name="viewport" content="width=device-width; initial-scale=1.0;" />
    </head>
    <body>
    <a href="./photo"><img src="photo" width="853" height="480" /></a>
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


@app.route('/stream')
def stream():
    return Response(ks.stream(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/photo/')
@app.route('/photo/<focus>')
def photo(focus=-1):
    focus = float(focus)
    stream = ks.photo(focus)
    response = make_response(stream)
    response.headers.set('Content-Type', 'image/jpeg')
    return response


def start_web():
    """ start web control """
    print("Web server is starting...")
    app.run('0.0.0.0', 8080)


if __name__ == '__main__':
    w = Thread(target=start_web)
    ks = KameraSteuerung(w)
    w.start()
    ks.run()
