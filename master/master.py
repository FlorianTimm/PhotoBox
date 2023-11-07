import socket
from flask import Flask
from threading import Thread
import configparser
import neopixel
import board
import re
from time import sleep
import uuid

liste = dict()

conf = configparser.ConfigParser()
conf.read("../config.ini")

leds = [int(v) for v in conf['server']['leds'].split(",")]
pixel_pin = board.D18
num_pixels = len(leds)

pixels = neopixel.NeoPixel(
    pixel_pin, num_pixels, brightness=0.1, auto_write=True, pixel_order=neopixel.RGB)

pixels.fill((0, 0, 255))


socket_rec = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
socket_rec.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
socket_rec.bind(("0.0.0.0", int(conf['both']['BroadCastPort'])))


# web control
app = Flask(__name__)


@app.route("/")
def web_index():
    return """<html>
    <head>
        <title>Kamera</title>
        <meta name="viewport" content="width=device-width; initial-scale=1.0;" />
    </head>
    <body>
        <a href="/overview">Overview</a><br>
        <a href="/search">Search</a><br>
        <a href="/shutdown">Shutdown</a><br>
        <a href="/reboot">Reboot</a><br>
        <a href="/photo">Photo</a><br>
        <a href="/focus/-1">Autofocus</a><br>
    </body>
    </html>"""


@app.route("/overview")
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

    hnames = dict(sorted(liste.items()))

    for e in hnames.values():
        output = output + """<div><a href="http://""" + e + """:8080/photo"><img id="img" src="http://""" + \
            e + """:8080/preview/-2?" width="640" height="480" /></a><br>""" + \
                socket.gethostbyaddr(e)[0] + """</div>"""
    output = output + """<a href="/focus/-1">Autofocus</a><br></body>
    </html>"""
    return output


@app.route("/search")
def search():
    msg = b'search'
    liste = dict()
    pixels.fill((0, 0, 255))
    send_to_all('search')
    return """<html><head><meta http-equiv="refresh" content="5; URL=/overview"><title>Suche...</title></head><body>Suche läuft...</body></html>"""


@app.route("/photo")
@app.route("/photo/<id>")
def photo(id=""):
    if id == "":
        id = str(uuid.uuid4()) + '.jpg'
        send_to_all('photo:' + id)
        return """<html><head><meta http-equiv="refresh" content="5; URL=/photo/""" + id + """"><title>Photo...</title></head><body>Photo wird gemacht...</body></html>"""
    else:
        output = """<html>
        <head>
            <title>Kamera</title>
            <meta name="viewport" content="width=device-width; initial-scale=1.0;" />
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

        hnames = dict(sorted(liste.items()))

        for hostname, ip in hnames.items():
            output = output + """<div><a href="http://""" + \
                ip + """:8080/bilder/""" + id + """" <img id="img" src="http://""" + \
                ip + """:8080/bilder/""" + id + """" /></a><br>""" + \
                hostname + """</div>"""
        output = output + """</body>
        </html>"""
        return output


@app.route("/shutdown")
def shutdown():
    """ Shutdown Raspberry Pi """
    send_to_all('shutdown')
    system("sleep 5s; sudo shutdown -h now")
    print("Shutdown Raspberry...")
    exit(0)


@app.route("/focus/<val>")
def focus(val=-1):
    """ Focus """
    send_to_all('focus:' + str(val))
    return """<html><head><meta http-equiv="refresh" content="5; URL=/overview"><title>Focus...</title></head><body>Fokussierung...</body></html>"""


@app.route("/reboot")
def reboot():
    """ Reboot Raspberry Pi """
    send_to_all('reboot')
    system("sleep 5s; sudo reboot")
    print("Reboot Raspberry...")
    exit(0)


def send_to_all(msg):
    msg = msg.encode("utf-8")
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(msg, ("255.255.255.255", int(
            conf['both']['BroadCastPort'])))


def start_web():
    """ start web control """
    print("Web server is starting...")
    app.run('0.0.0.0', 8080)


if __name__ == '__main__':
    w = Thread(target=start_web)
    w.start()
    # s = Thread(target=search)
    # s.start()
    search()
    while True:
        # sock.sendto(bytes("hello", "utf-8"), ip_co)
        data, addr = socket_rec.recvfrom(1024)
        data = data.decode("utf-8")
        if data[:4] == 'Moin':
            hostname = data[5:]
            liste[hostname] = addr[0]
            n = re.findall("\d{2}", hostname)
            if len(n) > 0:
                t = int(n[0])
                for led, pi in enumerate(leds):
                    if t != pi:
                        continue
                    pixels[led] = (0, 255, 0)
