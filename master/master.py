import socket
from flask import Flask
from threading import Thread
import configparser
import neopixel
import board
import re


liste = set()

pixel_pin = board.D18
num_pixels = 48

pixels = neopixel.NeoPixel(
    pixel_pin, num_pixels, brightness=0.1, auto_write=True, pixel_order=neopixel.RGB)

pixels.fill((0, 0, 255))

conf = configparser.ConfigParser()
conf.read("../config.ini")

socket_rec = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
socket_rec.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
socket_rec.bind(("0.0.0.0", conf['both']['BroadCastPort']))


# web control
app = Flask(__name__)


@app.route("/")
def index():
    output = """<html>
    <head>
        <title>Kamera</title>
        <meta name="viewport" content="width=device-width; initial-scale=1.0;" />
        <script>
        window.onload = function() {
            function updateImage() {
                let images = document.getElementsByTagName("img");
                for (let i = 0; i< images.length; i++) {
                    images[i].src = images[i].src.split("?")[0] + "?"+ new Date().getTime();
                } 
            }
            setInterval(updateImage, 10000);
        }   
    </script>
    <style>
    div {
        display: inline-block;
        height: 20%;
        width: 20%;
    }
    #img {
        max-height: 90%;
        max-width: 100%;
    }
    </style>
    </head>
    <body>"""

    hnames = dict()

    for e in liste:
        hnames[socket.gethostbyaddr(e)[0]] = e

    hnames = dict(sorted(hnames.items()))

    for e in hnames.values():
        output = output + """<div><a href="http://""" + e + """:8080/photo"><img id="img" src="http://""" + \
            e + """:8080/preview/-2?" width="640" height="480" /></a><br>""" + \
                socket.gethostbyaddr(e)[0] + """</div>"""
    output = output + """</body>
    </html>"""
    return output


def start_web():
    """ start web control """
    print("Web server is starting...")
    app.run('0.0.0.0', 8080)


def search():
    msg = b'search'
    while True:

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.sendto(msg, ("255.255.255.255", 5005))

        sleep(10)


if __name__ == '__main__':
    w = Thread(target=start_web)
    w = Thread(target=search)
    w.start()
    while True:
        # sock.sendto(bytes("hello", "utf-8"), ip_co)
        data, addr = socket_rec.recvfrom(1024)
        liste.add(addr[0])
        t = re.findall("\d{2}", socket.gethostbyaddr(addr[0])[0])
        if len(t) > 0:
            pixels[int(t[0])*2-2] = (0, 255, 0)
            pixels[int(t[0])*2-1] = (0, 255, 0)
