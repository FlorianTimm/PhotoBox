# stream: https://github.com/raspberrypi/picamera2/issues/366#issuecomment-1285888051

from io import BytesIO
from typing import Any, TypeVar
from picamera2 import Picamera2
from libcamera import controls  # type: ignore
from time import sleep
import piexif
from socket import gethostname
from typen import CamSettings, CamSettingsWithFilename
from typing import Dict, Tuple, List


class Kamera(object):
    def __init__(self, folder: str):
        self.cam: Picamera2 = Picamera2()
        scm: List[int] = self.cam.camera_properties['ScalerCropMaximum']
        h: int = scm[3]-scm[1]
        w: int = scm[2]-scm[0]
        rect: Tuple[int, int, int, int] = (
            scm[0]+w//3, scm[1]+w//3, w//3, h//3)
        ctrl: Dict[str, Any] = {
            "AwbMode": controls.AwbModeEnum.Auto.value,
            "AeMeteringMode": controls.AeMeteringModeEnum.CentreWeighted.value,
            "AeExposureMode": controls.AeExposureModeEnum.Long.value,
            "AfMetering": controls.AfMeteringEnum.Windows.value,
            "AfWindows": [rect],
            "AfMode": controls.AfModeEnum.Continuous.value
        }
        self.preview_config = self.cam.create_preview_configuration(
            controls=ctrl)
        self.still_config = self.cam.create_still_configuration(
            controls=ctrl)
        self.cam.configure(self.still_config)  # type: ignore
        self.cam.start()
        self.folder = folder

    def make_picture(self, settings: CamSettings = {}, preview=False) -> bytes:
        data = BytesIO()
        print("Kamera aktiviert!")
        self.set_settings(settings)
        # if (preview):
        self.cam.capture_file(data, format='jpeg')
        # else:
        #    req = self.cam.switch_mode_and_capture_image(
        #        self.still_config)
        #    req.save(data, format='jpeg')  # type: ignore
        print("Bild gemacht!")
        data.seek(0)
        return data.read()

    def save_picture(self, settings: CamSettingsWithFilename) -> str:
        print("Kamera aktiviert!")
        settings = self.set_settings(settings)
        file = self.folder + settings['filename']

        metadata = self.cam.capture_file(file, wait=True)
        if metadata["LensPosition"] != 0:
            focus = 1./metadata["LensPosition"]
        else:
            focus = 0
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

    def meta(self) -> dict[str, Any]:
        # request = self.cam.capture_request(wait=None)
        # if request is not None:
        #    return request.metadata
        # else:
        return {}

    CamSet = TypeVar('CamSet', CamSettings, CamSettingsWithFilename)

    def set_settings(self, settings: CamSet) -> CamSet:
        if isinstance(settings, dict):
            if 'focus' in settings and settings['focus'] != 0:
                print("focus: ", settings['focus'])
                focus_value = 1/settings['focus']
                self.focus(focus_value)
            with self.cam.controls as controls:
                if 'iso' in settings:
                    print("iso: ", settings['iso'])
                    controls.AnalogueGain = settings['iso']/100.
                if 'shutter_speed' in settings:
                    print("shutter_speed: ", settings['shutter_speed'])
                    controls.ExposureTime = settings['shutter_speed']
                if 'white_balance' in settings:
                    print("white_balance: ", settings['white_balance'])
                    controls.AwbMode = settings['white_balance']
        return settings

    def focus(self, focus: float) -> str:
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

    def get_status(self) -> dict[str, Any]:
        return self.cam.camera_properties

    def aruco(self) -> list[dict[str, int | float]]:
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
