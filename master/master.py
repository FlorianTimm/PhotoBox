import socket
from unittest.util import strclass
from flask import Flask, Response
from flask_cors import CORS
from threading import Thread
import configparser
import re
from time import sleep, clock_settime, clock_gettime, CLOCK_REALTIME
import uuid
from os import system, makedirs, path
import requests
from json import loads as json_loads, dumps as json_dumps
from shutil import make_archive
from glob import glob
from datetime import datetime
from typing import Literal, NoReturn
from os.path import basename
import FocusStack
from cv2 import imread, imwrite
from requests import get, Response as GetResponse


try:
    import neopixel
    import board
    from gpiozero import Button
    from adafruit_blinka.microcontroller.generic_linux.libgpiod_pin import Pin
    gpio_available = True
except ImportError:
    print("GPIO not available")
    gpio_available = False
except NotImplementedError:
    print("GPIO not available")
    gpio_available = False


RED = (255, 75, 75)
BLUE = (75, 75, 255)
GREEN = (75, 255, 75)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
YELLOW = (255, 255, 100)
LIGHTRED = (50, 0, 0)

liste: dict[str, str] = dict()
marker: dict[str, list] = dict()

photo_count: dict[str, int] = {}
download_count: dict[str, int] = {}
photo_type: dict[str, Literal["photo", "stack"]] = {}
cams_started = True

conf = configparser.ConfigParser()
conf.read("../config.ini")

if not path.exists(conf['server']['Folder']):
    makedirs(conf['server']['Folder'])

if gpio_available:
    leds: list[int] = [int(v) for v in conf['server']['leds'].split(",")]
    pixel_pin: Pin = board.D18
    num_pixels: int = len(leds)

    pixels = neopixel.NeoPixel(
        pixel_pin, num_pixels, brightness=1, auto_write=True, pixel_order=neopixel.RGB)  # type: ignore

    pixels.fill(BLUE)

licht = False

# web control
app = Flask(__name__, static_url_path='/bilder',
            static_folder=conf['server']['Folder'])
CORS(app)


@app.route("/")
def index() -> str:
    return """<html>
    <head>
        <title>Kamera</title>
        <meta name="viewport" content="width=device-width; initial-scale=1.0;" />

        <script>
            const time = new Date();
            fetch('/time/' + time.getTime());
        </script>
    </head>
    <body>
        <a href="/overview">Overview</a><br>
        <a href="/search">Search</a><br>
        <a href="/preview">Preview</a><br>
        <a href="/aruco">Aruco</a><br>
        <a href="/bilderUebersicht">Bilder</a><br>
        <br>
        <a href="/photo">Photo</a><br>
        <a href="/stack">Focus-Stack</a><br>
        <a href="/focus/-1">Autofocus</a><br>
        <a href="/light">Light</a>/<a href="/status">Status</a><br>
        <a href="/update">Update (pull from git)</a><br>
        <a href="/restart">Restart</a><br>
        <br><br>
        <a href="/shutdown">Shutdown</a><br>
        <a href="/reboot">Reboot</a><br>
    </body>
    </html>"""


@app.route("/time/<int:time>")
def time(time) -> str:
    clk_id: int = CLOCK_REALTIME
    alt: float = clock_gettime(clk_id)
    neu: float = float(time)/1000.
    if neu-alt > 10:
        clock_settime(clk_id, neu)
        return "updated: " + str(neu)
    return "keeped: " + str(alt)


@app.route("/bilderUebersicht")
def bilderUebersicht() -> str:
    output = """<html>
    <head>
        <title>Kamera</title>
        <meta name="viewport" content="width=device-width; initial-scale=1.0;" />
    </head>
    <body><table>"""

    files = glob(conf['server']['Folder'] + "*.zip")
    files.sort(key=lambda x: path.getmtime(x))
    for file in files:
        t = path.getmtime(file)
        file = file.replace(conf['server']['Folder'], "")
        output = output + """<tr><td><a href="/bilder/""" + file + """">""" + file + """</a></td><td>""" + \
            datetime.utcfromtimestamp(t).strftime(
                '%Y-%m-%d %H:%M:%S') + """</td></tr>"""
    output = output + """<br></body>
    </html>"""
    return output


@app.route("/overview")
def overview() -> str:
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
        output: str = output + """<div><a href="http://""" + ip + """:8080/photo"><img id="img" src="http://""" + \
            ip + """:8080/preview/-2?" width="640" height="480" /></a><br>""" + \
            hostname + """</div>"""
    output = output + """<a href="/focus/-1">Autofocus</a><br></body>
    </html>"""
    return output


@app.route("/search")
def search(send_search=True) -> str:
    global liste
    liste = dict()
    if gpio_available:
        pixels.fill(BLUE)  # type: ignore
    if send_search:
        send_to_all('search')
    return """<html><head><meta http-equiv="refresh" content="5; URL=/overview"><title>Suche...</title></head><body>Suche läuft...</body></html>"""


def capture(action: Literal['photo', 'stack'] = "photo", id: str = "") -> str:
    global photo_count, download_count, photo_type
    if id == "":
        if gpio_available:
            pixels.fill(WHITE)  # type: ignore
        id = str(uuid.uuid4())
        photo_count[id] = len(liste) * (4 if action == "stack" else 1)
        download_count[id] = len(liste) * (4 if action == "stack" else 1)
        photo_type[id] = action
        send_to_all(f'{action}:{id}')
        sleep(1 if action == "photo" else 5)
        status_led()
        return f"""<html><head><meta http-equiv="refresh" content="5; URL=/{action}/{id}"><title>Photo...</title></head><body>Photo wird gemacht...</body></html>"""
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
            output = output + """<div><a href="/bilder/""" + id + """/""" + hostname + """.jpg">""" + \
                """<img id="img" src="/bilder/""" + id + """/"""+hostname+""".jpg" /></a><br>""" + \
                hostname + """</div>"""
        output = output + """<br /><br />
        <a href="/bilder/""" + id + """.zip">Download as ZIP</a></body>
        </html>"""
        return output


@app.route("/photo")
@app.route("/photo/<id>")
def photo(id: str = "") -> str:
    return capture("photo", id)


@app.route("/stack")
def stack() -> str:
    return capture("stack")


@app.route("/preview")
def preview() -> Response:
    """Renders a preview page with camera settings and a photo.

    Returns:
        Response: The HTTP response containing the preview page.
    """
    response = Response()
    t = """<html><head><title>Preview</title></head><body>
    <script>
    function settings() {
        let url = document.getElementById("camera").value + 'settings/';
        let data = {
            focus: parseFloat(document.getElementById("focus").value),
            iso: parseInt(document.getElementById("iso").value),
            shutter_speed: parseInt(document.getElementById("shutter_speed").value)
        }
        data = JSON.stringify(data);
        fetch (url,  {
            method: 'POST',
            headers: {
                'Accept': 'application/json, text/plain, */*',
                'Content-Type': 'application/json'
            },
            body: data
        })
    }
    function lade_bild() {
        let img = document.getElementsByTagName("img")[0];
        let url = document.getElementById("camera").value + 'photo/';
        fetch (url,  {
            headers: {
                'Accept': 'application/json, text/plain, */*',
                'Content-Type': 'application/json'
            },
        }).then(function(response) {
            return response.blob();
        }).then(function(blob) {
            img.src = URL.createObjectURL(blob);
        });
    }
    </script>
    4608 × 2592
    <img width="1152" height="648" /><br />
    <select onchange="lade_bild()" id="camera">"""

    for hostname, ip in liste.items():
        t = t + """<option value="http://""" + ip + """:8080/">""" + \
            hostname + """</option>"""

    t += """</select><br />
    Focus: <input type="range" id="focus" value="0.3" min="0.10" max="1" step="0.05" onchange="settings()" /><br />
    ISO: <input type="range" id="iso" value="100" min="50" max="2000" step="50" onchange="settings()" /><br />
    ShutterSpeed: <input type="range" id="shutter_speed" value="1" min="1000" max="50000" step="1000" onchange="settings()" /><br />
    <input type="button" value="Photo" onclick="lade_bild()" />    
    </body></html>"""
    response.data = t
    return response


@app.route("/focus")
@app.route("/focus/<val>")
def focus(val=-1) -> str:
    """ Focus """
    send_to_all('focus:' + str(val))
    return """<html><head><meta http-equiv="refresh" content="5; URL=/overview"><title>Focus...</title></head><body>Fokussierung...</body></html>"""


def system_control(action: Literal['shutdown', 'reboot']) -> NoReturn:
    """ Controls the system based on the action """
    send_to_all(action)
    if gpio_available:
        pixels.fill(BLACK)  # type: ignore
    if action == 'shutdown':
        system("sleep 5s; sudo shutdown -h now")
        print("Shutdown Raspberry...")
    elif action == 'reboot':
        system("sleep 5s; sudo reboot")
        print("Reboot Raspberry...")
    exit(0)


@app.route("/shutdown")
def shutdown() -> NoReturn:
    """ Shutdown Raspberry Pi """
    return system_control('shutdown')


@app.route("/reboot")
def reboot() -> NoReturn:
    """ Reboot Raspberry Pi """
    return system_control('reboot')


@app.route("/restart")
def restart() -> str:
    """ Restart Skript """
    send_to_all('restart')
    if gpio_available:
        pixels.fill(YELLOW)  # type: ignore

    def restart_skript():
        system("sleep 5s; sudo systemctl restart PhotoBoxMaster.service")
        exit(1)
    Thread(target=restart_skript).start()
    print("Restart Skript...")
    return "Restarting..."


@app.route('/proxy/<host>/<path>')
def proxy(host: str, path: str) -> bytes:
    r: GetResponse = get("http://"+host+"/"+path)
    return r.content


@app.route("/update")
def update() -> str:
    """ Update Skript """
    send_to_all('update')
    if gpio_available:
        pixels.fill(YELLOW)  # type: ignore
    print("Update Skript...")
    system("sudo git -C /home/photo/PhotoBox pull")
    if gpio_available:
        pixels.fill(WHITE)  # type: ignore
    return "Updated"


@app.route("/aruco")
def aruco() -> str:
    """ Aruco """
    send_to_all('aruco:' + str(uuid.uuid4()))
    return """<html><head><meta http-equiv="refresh" content="10; URL=/arucoErg"><title>Erfasse...</title></head><body>Erfasse...</body></html>"""


@app.route("/arucoErg")
def aruco_erg() -> str:
    """ Aruco """
    return """<html><head><meta http-equiv="refresh" content="10; URL=/arucoErg"><title>Aruco</title></head><body>""" + json_dumps(marker).replace("\n", "<br />\n").replace(" ", "&nbsp;") + """</body></html>"""


@app.route("/light")
@app.route("/light/<val>")
def photo_light(val=0) -> str:
    global licht
    licht = True
    if gpio_available:
        pixels.fill(WHITE)
    try:
        return """<html><head><meta http-equiv="refresh" content="1; URL=/"><title>Light...</title></head><body>Light...</body></html>"""
    finally:
        if (val > 0):
            sleep(float(val))
            status_led()


@app.route("/status")
@app.route("/status/<val>")
def status_led(val=0) -> str:
    global licht
    licht = False
    if gpio_available:
        for led, pi in enumerate(leds):
            pixels[led] = RED
            liste_aktuell = list(liste.items())
            for hostname, ip in liste_aktuell:
                n = re.findall("\d{2}", hostname)
                if len(n) > 0:
                    t = int(n[0])
                    if t == pi:
                        pixels[led] = GREEN
    try:
        return """<html><head><meta http-equiv="refresh" content="1; URL=/"><title>Status...</title></head><body>Status...</body></html>"""
    finally:
        if val > 0:
            sleep(float(val))
            photo_light()


def send_to_all(msg) -> None:
    msg = msg.encode("utf-8")
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(msg, ("255.255.255.255", int(
            conf['both']['BroadCastPort'])))


def start_web() -> None:
    """ start web control """
    print("Web server is starting...")
    app.run('0.0.0.0', 8080)


def found_camera(hostname, ip) -> None:
    global liste
    if hostname in liste:
        return
    liste[hostname] = ip
    status_led(5)


def get_hostname(ip) -> list[str]:
    global liste
    print(liste)
    print(ip)
    return [k for k, v in liste.items() if v == ip]


def receive_photo(ip, name) -> None:
    global photo_count
    print("Photo received: " + name)
    id = name[:36]
    photo_count[id] -= 1
    hostname = get_hostname(ip)
    if len(hostname) > 0:
        hostname = hostname[0]
    else:
        print("Error: Hostname not found!")
        return
    Thread(target=download_photo, args=(ip, id, name, hostname)).start()
    if photo_count[id] == 0:
        status_led()
        del photo_count[id]
        print("All photos taken!")


def download_photo(ip, id, name, hostname) -> None:
    """ collect photos """
    global download_count
    print("Downloading photo...")
    folder = conf['server']['Folder'] + id + "/"
    if not path.exists(folder):
        makedirs(folder)

    print("Collecting photo from " + hostname + "...")
    try:
        url = "http://" + ip + ":8080/bilder/" + name
        print(url)
        r = requests.get(url, allow_redirects=True)
        open(folder + hostname + name[36:], 'wb').write(r.content)
    except Exception as e:
        print("Error collecting photo from " + hostname + ":", e)
    download_count[id] -= 1
    if download_count[id] == 0:
        print("Collecting photos done!")
        del download_count[id]
        if photo_type[id] == "stack":
            pass
            stack_photos(id)
        del photo_type[id]
        make_archive(conf['server']['Folder'] + id, 'zip', folder)
        photo_light()


def stack_photos(id)_>None:
    folder:str = conf['server']['Folder'] + id + "/"
    imgs:list[str] = glob(folder + "*.jpg")
    groups: dict[str, list] = {}
    imgs.sort()
    for i in imgs:
        name = basename(i)
        name = name.split("_")[0]
        if not name in groups:
            groups[name] = []
        groups[name].append(imread(i))
    for camera, bilder in groups.items():
        imwrite(folder + camera + ".jpg", FocusStack.focus_stack(bilder))


def receive_aruco(data)->None:
    global marker
    i1:int = data.find(":")
    i2:int = data[i1+1:].find(":")
    id:int = data[:i1]

    hostname:str = data[i1+1:i1+i2+1]
    marker[hostname][id] = json_loads(data[i1+i2+2:])


def listen_to_port():
    socket_rec = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    socket_rec.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    socket_rec.bind(("0.0.0.0", int(conf['both']['BroadCastPort'])))
    while True:
        # sock.sendto(bytes("hello", "utf-8"), ip_co)
        data, addr = socket_rec.recvfrom(1024)
        print("received message: %s" % data)
        print(addr)
        data = data.decode("utf-8")
        print(addr[0] + ": " + data)
        if data[:4] == 'Moin':
            Thread(target=found_camera, args=(data[5:], addr[0])).start()
        elif data[:6] == 'photo:':
            receive_photo(addr[0], data[6:])
        elif data[:11] == 'arucoReady:':
            print(data)
            receive_aruco(data[11:])
        elif data[:5] == 'light':
            photo_light()


def switch_pause_resume():
    global cams_started
    if cams_started:
        pause()
    else:
        resume()


def pause():
    global cams_started
    cams_started = False
    send_to_all('pause')
    Thread(target=running_light).start()


def running_light():
    global cams_started
    pixels.fill(BLACK)
    while not cams_started:
        for j in range(num_pixels//8):
            for i in range(8):
                pixels[j+num_pixels//8*i] = LIGHTRED
            sleep(0.5)
            for i in range(8):
                pixels[j+num_pixels//8*i] = BLACK
            if cams_started:
                break


def resume():
    global cams_started
    if not cams_started:
        cams_started = True
        search(False)
        send_to_all('resume')


# Buttons

def red_button_held()->None:
    global button_red_was_held
    button_red_was_held = True
    print("Shutdown pressed...")
    shutdown()


def red_button_released()->None:
    global button_red_was_held
    if not button_red_was_held:
        print("Red pressed...")
        switch_pause_resume()
        pass
    button_red_was_held = False


def blue_button_released()->None:
    global button_blue_was_held
    if not button_blue_was_held:
        print("Photo pressed...")
        photo()
    button_blue_was_held = False


def blue_button_held()->None:
    global button_blue_was_held
    button_blue_was_held = True
    print("Calibration pressed...")
    pass


def green_button_released()->None:
    global button_green_was_held
    if not button_green_was_held:
        print("Status LED pressed...")
        status_led(5)
    button_green_was_held = False


def green_button_held():
    global button_green_was_held
    button_green_was_held = True
    print("Search pressed...")
    search()


if gpio_available:
    print("Buttons are starting...")
    button_blue = Button(24, pull_up=True, hold_time=2, bounce_time=0.1)
    button_blue.when_released = blue_button_released
    button_blue.when_held = blue_button_held
    button_blue_was_held = False

    button_red = Button(23, pull_up=True, hold_time=2, bounce_time=0.1)
    button_red.when_held = red_button_held
    button_red.when_released = red_button_released
    button_red_was_held = False

    button_green = Button(25, pull_up=True, hold_time=2, bounce_time=0.1)
    button_green.when_released = green_button_released
    button_green.when_held = green_button_held
    button_green_was_held = False


# Start

if __name__ == '__main__':
    w = Thread(target=start_web)
    w.start()
    global receiver
    receiver = Thread(target=listen_to_port)
    sleep(5)
    receiver.start()
    search()
