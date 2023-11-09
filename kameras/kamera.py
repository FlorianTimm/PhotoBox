# stream: https://github.com/raspberrypi/picamera2/issues/366#issuecomment-1285888051

import io
from picamera2 import Picamera2
from libcamera import controls
from time import sleep
from cv2 import aruco


class Kamera(object):
    def __init__(self, folder):
        self.cam = Picamera2()
        scm = self.cam.camera_properties['ScalerCropMaximum']
        h = scm[3]-scm[1]
        w = scm[2]-scm[0]
        rect = (scm[0]+w//3, scm[1]+w//3, w//3, h//3)
        ctrl = {
            "AwbMode": controls.AwbModeEnum.Fluorescent,
            "AeMeteringMode": controls.AeMeteringModeEnum.CentreWeighted,
            "AfMetering": controls.AfMeteringEnum.Windows,
            "AfWindows": [rect],
            "AfMode": controls.AfModeEnum.Continuous
        }
        self.preview_config = self.cam.create_preview_configuration(
            controls=ctrl)
        self.still_config = self.cam.create_still_configuration(
            controls=ctrl)
        self.cam.configure(self.still_config)
        self.cam.start()
        self.folder = folder
        self.aruco_dict = aruco.Dictionary_create(32, 3)
        self.parameter = aruco.DetectorParameters.create()
        self.parameter.cornerRefinementMethod = aruco.CORNER_REFINE_SUBPIX
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
        self.cam.capture_file(self.folder + filename)
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

    def aruco(self):
        im = self.cam.capture_array()
        return aruco.detectMarkers(im, self.aruco_dict, parameters=self.parameter)
