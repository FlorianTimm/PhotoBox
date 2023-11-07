# stream: https://github.com/raspberrypi/picamera2/issues/366#issuecomment-1285888051

import io
from picamera2 import Picamera2
from libcamera import controls, Rectangle
from time import sleep


class Kamera(object):
    def __init__(self, folder):
        self.cam = Picamera2()
        self.preview_config = self.cam.create_preview_configuration()
        self.still_config = self.cam.create_still_configuration(controls={
            "AwbMode": controls.AwbModeEnum.Fluorescent,
            "AeMeteringMode": controls.AeMeteringModeEnum.CentreWeighted  # ,
            # "AfMetering": controls.AfMeteringEnum.Windows,
            # "AfWindows": [Rectangle(2000, 1000, 600, 500)]
        })
        self.cam.configure(self.preview_config)
        self.cam.start()
        self.folder = folder
        #

    def make_picture(self, focus, preview=False) -> memoryview:
        data = io.BytesIO()
        print("Kamera aktiviert!")
        self.focus(focus)
        if (preview):
            self.cam.capture_file(data, format='jpeg')
        else:
            req = self.cam.switch_mode_and_capture_image(
                self.still_config)
            req.save(data, format='jpeg')
        print("Bild gemacht!")
        data.seek(0)
        return data.read()

    def save_picture(self, filename, focus) -> memoryview:
        data = io.BytesIO()
        print("Kamera aktiviert!")
        self.focus(focus)
        self.cam.switch_mode_and_capture_file(
            self.still_config, self.folder + filename)
        print("Bild " + filename + " gemacht!")
        return "fertig"

    def focus(self, focus):
        if (focus == -2):
            pass
        elif (focus == -1):
            self.cam.set_controls({"AfMode": controls.AfModeEnum.Auto})
            self.cam.autofocus_cycle()
        else:
            self.cam.set_controls(
                {"AfMode": controls.AfModeEnum.Manual, "LensPosition": focus})
            sleep(0.5)
        return "Fokus"

    def get_status(self):
        return self.cam.camera_properties
