# stream: https://github.com/raspberrypi/picamera2/issues/366#issuecomment-1285888051

import io
from picamera2 import Picamera2
from libcamera import controls
from time import sleep


class Kamera(object):
    def __init__(self):
        self.cam = Picamera2()
        still_config = self.cam.create_still_configuration()
        self.cam.configure(still_config)
        self.cam.start()

    def make_picture(self, focus) -> memoryview:
        data = io.BytesIO()
        print("Kamera aktiviert!")
        if (focus == -1):
            self.cam.set_controls({"AfMode": controls.AfModeEnum.Auto})
            self.cam.autofocus_cycle()
        else:
            self.cam.set_controls(
                {"AfMode": controls.AfModeEnum.Manual, "LensPosition": focus})
            sleep(0.5)
        self.cam.capture_file(data, format='jpeg')
        print("Bild gemacht!")
        data.seek(0)
        return data.read()

    def get_status(self):
        return self.cam.camera_properties
