# stream: https://github.com/raspberrypi/picamera2/issues/366#issuecomment-1285888051

from io import BytesIO
from picamera2 import Picamera2
from libcamera import controls
from time import sleep
import piexif
from socket import gethostname
from typen import CamSettings, CamSettingsWithFilename


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
            "AeExposureMode": controls.AeExposureModeEnum.Long,
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

    def make_picture(self, settings: CamSettings = {}, preview=False) -> memoryview:
        data = BytesIO()
        print("Kamera aktiviert!")
        self.set_settings(settings)
        if (preview):
            self.cam.capture_file(data, format='jpeg')
        else:
            req = self.cam.switch_mode_and_capture_image(
                self.still_config)
            req.save(data, format='jpeg')
        print("Bild gemacht!")
        data.seek(0)
        return data.read()

    def save_picture(self, settings: CamSettingsWithFilename) -> str:
        print("Kamera aktiviert!")
        settings = self.set_settings(settings)
        file = self.folder + settings['filename']

        metadata = self.cam.capture_file(file, wait=True)
        focus = 1./metadata["LensPosition"]
        focus = int(focus*100)

        # Add focal length to EXIF data
        exif_dict = piexif.load(file)
        exif_dict["Exif"][piexif.ExifIFD.FocalLength] = (474, 100)
        exif_dict["Exif"][piexif.ExifIFD.SubjectDistance] = (focus, 100)
        exif_dict["Exif"][piexif.ExifIFD.BodySerialNumber] = gethostname()
        exif_bytes = piexif.dump(exif_dict)
        piexif.insert(exif_bytes, file)

        print("Bild " + file + " gemacht!")
        return "fertig"

    def meta(self):
        request = self.cam.capture_request()
        return request.get_metadata()

    def set_settings(self, settings: CamSettings | CamSettingsWithFilename) -> CamSettings | CamSettingsWithFilename:
        if 'focus' in settings:
            self.focus(settings['focus'])
        if 'iso' in settings:
            self.cam.set_controls({"AnalogueGain": settings['focus']/100})
        if 'shutter_speed' in settings:
            self.cam.set_controls({"ExposureTime": settings['shutter_speed']})
        return settings

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
        from cv2.aruco import Dictionary_create, DetectorParameters, CORNER_REFINE_SUBPIX, detectMarkers
        self.aruco_dict = Dictionary_create(32, 3)
        self.parameter = DetectorParameters.create()
        self.parameter.cornerRefinementMethod = CORNER_REFINE_SUBPIX

        im = self.cam.capture_array()
        corners, ids, _ = detectMarkers(
            im, self.aruco_dict, parameters=self.parameter)
        marker = []
        if ids is not None:
            for ecke, id_ in zip(corners, ids):
                for eid, e in enumerate(ecke[0]):
                    x, y = e[0], e[1]
                    marker.append({'marker': int(id_[0]),
                                   'ecke': eid,
                                   'x': float(x),
                                   'y': float(y)})
        return marker
