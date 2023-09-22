#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@author: Florian Timm
@version: 2023.09.21
"""

from flask import Flask, make_response
from threading import Thread
import configparser
from os import system
from sys import exit
from kamera import Kamera
import socket
from time import sleep


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
        t = Thread(target=self.broadcast)
        t.start()

    def shutdown(self):
        """ Shutdown Raspberry Pi """
        system("sleep 5s; sudo shutdown -h now")
        print("Shutdown Raspberry...")
        exit(0)

    def run(self):
        self.cam = Kamera()  # flip pi camera if upside down.
        print("Moin")

    def photo(self, focus):
        return self.cam.make_picture(focus)

    def preview(self, focus):
        return self.cam.make_picture(focus, preview=True)

    def focus(self, focus):
        return self.cam.focus(focus)

    def broadcast(self):
        msg = b'hello world'
        while True:

            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                sock.sendto(msg, ("255.255.255.255", 5005))

            sleep(2)


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
    stream = ks.photo(focus)
    response = make_response(stream)
    response.headers.set('Content-Type', 'image/jpeg')
    return response


@app.route('/preview/')
@app.route('/preview/<focus>')
def preview(focus=-2):
    focus = float(focus)
    stream = ks.preview(focus)
    response = make_response(stream)
    response.headers.set('Content-Type', 'image/jpeg')
    return response


@app.route('/focus/')
@app.route('/focus/<focus>')
def focus(focus=-1):
    focus = float(focus)
    return ks.focus(focus)


def start_web():
    """ start web control """
    print("Web server is starting...")
    app.run('0.0.0.0', 8080)


if __name__ == '__main__':
    w = Thread(target=start_web)
    ks = KameraSteuerung(w)
    w.start()
    ks.run()
