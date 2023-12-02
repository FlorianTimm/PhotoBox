import socket
from flask import Flask
from threading import Thread
import configparser
import neopixel
import board
import re
from time import sleep
import uuid
from os import system, makedirs, path
import requests
from gpiozero import Button

liste = dict()

photo_count = 0

conf = configparser.ConfigParser()
conf.read("../config.ini")

if not path.exists(conf['server']['Folder']):
    makedirs(conf['server']['Folder'])

leds = [int(v) for v in conf['server']['leds'].split(",")]
pixel_pin = board.D18
num_pixels = len(leds)

pixels = neopixel.NeoPixel(
    pixel_pin, num_pixels, brightness=1, auto_write=True, pixel_order=neopixel.RGB)  # type: ignore

pixels.fill((0, 0, 25))

licht = False

# web control
app = Flask(__name__)


def collect_photos(liste, id):
    """ collect photos """
    print("Collecting photos...")
    sleep(5)
    folder = conf['server']['Folder'] + id + "/"
    makedirs(folder)
    for hostname, ip in liste.items():
        print("Collecting photo from " + hostname + "...")
        try:
            url = "http://" + ip + ":8080/bilder/" + id
            print(url)
            r = requests.get(url, allow_redirects=True)
            open(folder + hostname + '.jpg', 'wb').write(r.content)
        except Exception as e:
            print("Error collecting photo from " + hostname + ":", e)
    print("Collecting photos done!")
    photo_light()


@app.route("/")
def index():
    return """<html>
    <head>
        <title>Kamera</title>
        <meta name="viewport" content="width=device-width; initial-scale=1.0;" />
    </head>
    <body>
        <a href="/overview">Overview</a><br>
        <a href="/search">Search</a><br>
        <a href="/preview">Preview</a><br>

        <a href="/photo">Photo</a><br>
        <a href="/focus/-1">Autofocus</a><br>
        <a href="/light">Light</a>/<a href="/status">Status</a><br>
        <a href="/restart">Restart</a><br>

        <br><br>
        <a href="/shutdown">Shutdown</a><br>
        <a href="/reboot">Reboot</a><br>
    </body>
    </html>"""


@app.route("/overview")
def overview():
    global liste
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

    for hostname, ip in hnames.items():
        output = output + """<div><a href="http://""" + ip + """:8080/photo"><img id="img" src="http://""" + \
            ip + """:8080/preview/-2?" width="640" height="480" /></a><br>""" + \
            hostname + """</div>"""
    output = output + """<a href="/focus/-1">Autofocus</a><br></body>
    </html>"""
    return output


@app.route("/search")
def search():
    global liste
    msg = b'search'
    liste = dict()
    pixels.fill((0, 0, 25))
    send_to_all('search')
    return """<html><head><meta http-equiv="refresh" content="5; URL=/overview"><title>Suche...</title></head><body>Suche läuft...</body></html>"""


@app.route("/photo")
@app.route("/photo/<id>")
def photo(id=""):
    global photo_count
    if id == "":
        pixels.fill((255, 255, 255))
        id = str(uuid.uuid4()) + '.jpg'
        sleep(2)
        photo_count = photo_count + len(liste)
        send_to_all('photo:' + id)
        sleep(0.5)
        status_led()
        Thread(target=collect_photos, args=(liste, id)).start()
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
                ip + """:8080/bilder/""" + id + """"><img id="img" src="http://""" + \
                ip + """:8080/bilder/""" + id + """" /></a><br>""" + \
                hostname + """</div>"""
        output = output + """</body>
        </html>"""
        return output


@app.route("/preview")
def preview():
    """ preview """
    t = """<html><head><title>Preview</title></head><body>
    <script>
    function lade_bild() {
        var img = document.getElementsByTagName("img")[0];
        url = document.getElementById("camera").value;
        data = {
            focus: document.getElementById("focus").value,
            iso: document.getElementById("iso").value,
            shutter_speed: document.getElementById("shutter_speed").value
        }
        fetch (url).then(function(response) {
            return response.blob();
        }).then(function(blob) {
            img.src = URL.createObjectURL(blob);
        });
    }
    </script>
    <img width="640" height="480" />
    <textarea id="log" rows="10" cols="50"></textarea>
    <select onchange="lade_bild()" id="camera">"""

    for hostname, ip in liste.items():
        t = t + """<option value="http://""" + ip + """:8080/preview/-2">""" + \
            hostname + """</option>"""

    t += """</select>
    <input type="slider" id="focus" value="0" min="10" max="100" step="5" onchange="lade_bild()" />
    <input type="slider" id="iso" value="0" min="50" max="800" step="50" onchange="lade_bild()" />
    <input type="slider" id="shutter_speed" value="0" min="100" max="1000000" step="100" onchange="lade_bild()" />
    <input type="button" value="Photo" onclick="lade_bild()" />
    
    
    </body></html>"""
    return t


@app.route("/shutdown")
def shutdown():
    """ Shutdown Raspberry Pi """
    send_to_all('shutdown')
    pixels.fill((0, 0, 0))
    system("sleep 5s; sudo shutdown -h now")
    print("Shutdown Raspberry...")
    exit(0)


@app.route("/focus")
@app.route("/focus/<val>")
def focus(val=-1):
    """ Focus """
    send_to_all('focus:' + str(val))
    return """<html><head><meta http-equiv="refresh" content="5; URL=/overview"><title>Focus...</title></head><body>Fokussierung...</body></html>"""


@app.route("/reboot")
def reboot():
    """ Reboot Raspberry Pi """
    send_to_all('reboot')
    pixels.fill((0, 0, 0))
    system("sleep 5s; sudo reboot")
    print("Reboot Raspberry...")
    exit(0)


@app.route("/restart")
def restart():
    """ Restart Skript """
    send_to_all('restart')
    pixels.fill((255, 255, 0))
    system("systemctl restart PhotoBoxMaster.service")
    print("Restart Skript...")
    exit(1)


@app.route("/light")
@app.route("/light/<val>")
def photo_light(val=0):
    licht = True
    pixels.fill((255, 255, 255))
    try:
        return """<html><head><meta http-equiv="refresh" content="1; URL=/"><title>Light...</title></head><body>Light...</body></html>"""
    finally:
        if (val > 0):
            sleep(float(val))
            status_led()


@app.route("/status")
@app.route("/status/<val>")
def status_led(val=0):
    licht = False
    for led, pi in enumerate(leds):
        pixels[led] = (25, 0, 0)
        liste_aktuell = list(liste.items())
        for hostname, ip in liste_aktuell:
            n = re.findall("\d{2}", hostname)
            if len(n) > 0:
                t = int(n[0])
                if t == pi:
                    pixels[led] = (0, 25, 0)
    try:
        return """<html><head><meta http-equiv="refresh" content="1; URL=/"><title>Status...</title></head><body>Status...</body></html>"""
    finally:
        if val > 0:
            sleep(float(val))
            photo_light()


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


def found_camera(hostname, ip):
    if hostname in liste:
        return
    liste[hostname] = ip
    status_led(10)


def receive_photo():
    global photo_count
    photo_count = photo_count - 1
    if photo_count == 0:
        status_led(10)


def listen_to_port():
    socket_rec = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    socket_rec.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    socket_rec.bind(("0.0.0.0", int(conf['both']['BroadCastPort'])))
    while True:
        # sock.sendto(bytes("hello", "utf-8"), ip_co)
        data, addr = socket_rec.recvfrom(1024)
        data = data.decode("utf-8")
        print(addr[0] + ": " + data)
        if data[:4] == 'Moin':
            Thread(target=found_camera, args=(data[5:], addr[0])).start()
        elif data[:5] == 'photo':
            receive_photo()
        elif data[:5] == 'light':
            photo_light()


def shutdown_button():
    print("Shutdown pressed...")
    shutdown()


def photo_button():
    print("Photo pressed...")
    photo()


def status_led_button():
    print("Status LED pressed...")
    status_led(10)


print("Buttons are starting...")
button_blue = Button(24, pull_up=True, bounce_time=0.1)
button_blue.when_pressed = photo_button

button_red = Button(23, pull_up=True, hold_time=2, bounce_time=0.1)
button_red.when_held = shutdown_button

button_green = Button(25, pull_up=True, bounce_time=0.1)
button_green.when_pressed = status_led_button


if __name__ == '__main__':
    w = Thread(target=start_web)
    w.start()
    global receiver
    receiver = Thread(target=listen_to_port)
    sleep(5)
    receiver.start()
    search()
