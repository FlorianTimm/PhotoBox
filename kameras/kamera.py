import io
from picamera2 import Picamera2
from libcamera import controls
from time import sleep


class Kamera(object):
    def __init__(self):
        self.cam = Picamera2()
        self.still_config = self.cam.create_still_configuration()
        self.video_config = self.cam.create_video_configuration(
            main={"size": (640, 480)})

    def make_picture(self, focus) -> memoryview:
        data = io.BytesIO()
        print("Kamera aktiviert!")
        self.cam.configure(self.still_config)
        # Camera warm-up time
        if (focus == -1):
            self.cam.set_controls({"AfMode": controls.AfModeEnum.Auto})
            self.cam.autofocus_cycle()
        else:
            self.cam.set_controls(
                {"AfMode": controls.AfModeEnum.Manual, "LensPosition": focus})
            sleep()
        self.cam.capture_file(data, format='jpeg')
        print("Bild gemacht!")
        data.seek(0)
        return data.read()

    def get_status(self):
        return self.cam.camera_properties
