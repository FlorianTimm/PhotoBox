import socket
from flask import Flask, Response, render_template, send_from_directory
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
            static_folder=conf['server']['Folder'], template_folder='../template')
CORS(app)


@app.route("/static/<path:filename>")
def static_file(filename) -> Response:
    return send_from_directory("../template/static/", filename)


@app.route("/")
def index() -> str:
    return render_template('index.htm')


@app.route("/time/<int:time>")
def time(time) -> str:
    clk_id: int = CLOCK_REALTIME
    alt: float = clock_gettime(clk_id)
    neu: float = float(time)/1000.
    if neu-alt > 10:
        clock_settime(clk_id, neu)
        return "updated: " + str(neu)
    return "keeped: " + str(alt)


@app.route("/overviewZip")
def overviewZip() -> str:
    '''Overview of all zip files with images.'''
    filelist = glob(conf['server']['Folder'] + "*.zip")
    filelist.sort(key=lambda x: path.getmtime(x))

    def f2d(file):
        time = path.getmtime(file)
        p = file.replace(conf['server']['Folder'], "")
        t = datetime.utcfromtimestamp(time).strftime('%Y-%m-%d %H:%M:%S')
        return {'path': p, 'time': t}
    files = [f2d(file) for file in filelist]
    return render_template('overviewZip.htm', files=files)


@app.route("/overview")
def overview() -> str:
    global liste
    hnames = dict(sorted(liste.items()))
    hip = [{'hostname': hostname, 'ip': ip} for hostname, ip in hnames.items()]
    return render_template('overview.htm', cameras=hip)


@app.route("/search")
def search_html() -> str:
    search()
    return render_template('wait.htm', time=5, target_url="/overview", title="Search for cameras...")


def search(send_search=True) -> None:
    global liste
    liste = dict()
    if gpio_available:
        pixels.fill(BLUE)  # type: ignore
    if send_search:
        send_to_all('search')


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
        return render_template('wait.htm', time=5,
                               target_url=f"/{action}/{id}", title="Photo...")
    else:
        hnames = dict(sorted(liste.items()))
        return render_template('overviewCapture.htm', cameras=hnames.keys(), id=id, action=action)


@app.route("/photo")
@app.route("/photo/<id>")
def photo(id: str = "") -> str:
    return capture("photo", id)


@app.route("/stack")
def stack() -> str:
    return capture("stack")


@app.route("/preview")
def preview() -> str:
    """Renders a preview page with camera settings and a photo.

    Returns:
        Response: The HTTP response containing the preview page.
    """
    hnames = dict(sorted(liste.items()))
    cameras = [{'hostname': k, 'ip': v} for k, v in hnames.items()]
    return render_template('preview.htm', cameras=cameras)


@app.route("/focus")
@app.route("/focus/<val>")
def focus(val=-1) -> str:
    """ Focus """
    send_to_all('focus:' + str(val))
    return render_template('wait.htm', time=5, target_url="/overview", title="Focusing...")


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
    return render_template('wait.htm', time=15, target_url="/", title="Restarting...")


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
    return render_template('wait.htm', time=5, target_url="/arucoErg", title="Search for Aruco...")


@app.route("/arucoErg")
def aruco_erg() -> str:
    """ Aruco """
    return render_template('aruco.htm', content=json_dumps(marker).replace("\n", "<br />\n").replace(" ", "&nbsp;"))


@app.route("/light")
@app.route("/light/<val>")
def photo_light(val=0) -> str:
    global licht
    licht = True
    if gpio_available:
        pixels.fill(WHITE)
    try:
        return render_template('wait.htm', time=1, target_url="/", title="Light...")
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
        return render_template('wait.htm', time=1, target_url="/", title="Status...")
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


def stack_photos(id) -> None:
    folder: str = conf['server']['Folder'] + id + "/"
    imgs: list[str] = glob(folder + "*.jpg")
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


def receive_aruco(data) -> None:
    global marker
    i1: int = data.find(":")
    i2: int = data[i1+1:].find(":")
    id: int = data[:i1]

    hostname: str = data[i1+1:i1+i2+1]
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

def red_button_held() -> None:
    global button_red_was_held
    button_red_was_held = True
    print("Shutdown pressed...")
    shutdown()


def red_button_released() -> None:
    global button_red_was_held
    if not button_red_was_held:
        print("Red pressed...")
        switch_pause_resume()
        pass
    button_red_was_held = False


def blue_button_released() -> None:
    global button_blue_was_held
    if not button_blue_was_held:
        print("Photo pressed...")
        photo()
    button_blue_was_held = False


def blue_button_held() -> None:
    global button_blue_was_held
    button_blue_was_held = True
    print("Calibration pressed...")
    pass


def green_button_released() -> None:
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
