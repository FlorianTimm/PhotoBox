from flask import Flask, Response, render_template, send_from_directory
from flask_cors import CORS
import configparser
from time import clock_settime, clock_gettime, CLOCK_REALTIME
import uuid
from os import path
from json import dumps as json_dumps
from glob import glob
from datetime import datetime
from typing import Literal, NoReturn
from requests import get, Response as GetResponse

from control import Control

conf = configparser.ConfigParser()
conf.read('../config.ini')

app = Flask(__name__, static_url_path='/bilder',
            static_folder=conf['server']['Folder'], template_folder='../template')
CORS(app)

control = Control(conf, app)


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
    filelist = glob(control.conf['server']['Folder'] + "*.zip")
    filelist.sort(key=lambda x: path.getmtime(x))

    def f2d(file):
        time = path.getmtime(file)
        p = file.replace(control.conf['server']['Folder'], "")
        t = datetime.utcfromtimestamp(time).strftime('%Y-%m-%d %H:%M:%S')
        return {'path': p, 'time': t}
    files = [f2d(file) for file in filelist]
    return render_template('overviewZip.htm', files=files)


@app.route("/overview")
def overview() -> str:
    hnames = control.get_hostnames()
    hip = [{'hostname': hostname, 'ip': ip} for hostname, ip in hnames.items()]
    return render_template('overview.htm', cameras=hip)


@app.route("/search")
def search_html() -> str:
    control.search_cameras()
    return render_template('wait.htm', time=5, target_url="/overview", title="Search for cameras...")


@app.route("/photo")
@app.route("/photo/<id>")
def photo_html(id: str = "") -> str:
    return capture_html("photo", id)


@app.route("/stack")
def stack_html() -> str:
    return capture_html("stack")


def capture_html(action: Literal['photo', 'stack'] = "photo", id: str = "") -> str:
    if id == "":
        id = control.capture_photo(action)
        return render_template('wait.htm', time=5,
                               target_url=f"/{action}/{id}", title="Photo...")
    else:
        hnames = dict(sorted(control.list_of_cameras.items()))
        return render_template('overviewCapture.htm', cameras=hnames.keys(), id=id, action=action)


@app.route("/preview")
def preview() -> str:
    """Renders a preview page with camera settings and a photo.

    Returns:
        Response: The HTTP response containing the preview page.
    """
    hnames = dict(sorted(control.list_of_cameras.items()))
    cameras = [{'hostname': k, 'ip': v} for k, v in hnames.items()]
    return render_template('preview.htm', cameras=cameras)


@app.route("/focus")
@app.route("/focus/<val>")
def focus(val=-1) -> str:
    """ Focus """
    control.send_to_all('focus:' + str(val))
    return render_template('wait.htm', time=5, target_url="/overview", title="Focusing...")


@app.route("/shutdown")
def shutdown_html() -> NoReturn:
    """ Shutdown Raspberry Pi """
    return control.system_control('shutdown')


@app.route("/reboot")
def reboot_html() -> NoReturn:
    """ Reboot Raspberry Pi """
    return control.system_control('reboot')


@app.route("/restart")
def restart() -> str:
    return control.restart()


@app.route('/proxy/<host>/<path>')
def proxy(host: str, path: str) -> bytes:
    r: GetResponse = get("http://"+host+"/"+path)
    return r.content


@app.route("/update")
def update() -> str:
    return control.update()


@app.route("/aruco")
def aruco() -> str:
    """ Aruco """
    control.send_to_all('aruco:' + str(uuid.uuid4()))
    return render_template('wait.htm', time=5, target_url="/arucoErg", title="Search for Aruco...")


@app.route("/arucoErg")
def aruco_erg() -> str:
    """ Aruco """
    return render_template('aruco.htm', json_data=json_dumps(control.detected_markers, indent=2).replace(" ", "&nbsp;").replace("\n", "<br />\n"))


@app.route("/test")
def test() -> str:
    """ Test """
    control.send_to_all('test')
    control.send_to_desktop("test")
    return render_template('wait.htm', time=5, target_url="/overview", title="Test...")


@app.route("/light")
@app.route("/light/<val>")
def photo_light_html(val=0) -> str:
    try:
        return render_template('wait.htm', time=1, target_url="/", title="Light...")
    finally:
        control.get_leds().photo_light(val)


@app.route("/status")
@app.route("/status/<val>")
def status_led_html(val=0) -> str:
    try:
        return render_template('wait.htm', time=1, target_url="/", title="Status...")
    finally:
        control.get_leds().status_led(val)


control.start()
