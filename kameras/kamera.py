# stream: https://github.com/raspberrypi/picamera2/issues/366#issuecomment-1285888051

from io import BytesIO
from typing import Any, TypeVar
from picamera2 import Picamera2
from libcamera import controls  # type: ignore
from time import sleep
import piexif
from socket import gethostname
from typen import CamSettings, CamSettingsWithFilename
from typing import Dict, Tuple, List, Callable


class Kamera(object):
    def __init__(self, folder: str):
        tuning = Picamera2.load_tuning_file("imx708.json", dir='./tuning/')
        self.cam: Picamera2 = Picamera2(tuning=tuning)
        scm: List[int] = self.cam.camera_properties['ScalerCropMaximum']
        h: int = scm[3]-scm[1]
        w: int = scm[2]-scm[0]
        rect: Tuple[int, int, int, int] = (
            scm[0]+3*w//7, scm[1]+3*h//7, w//7, h//7)
        ctrl: Dict[str, Any] = {
            "AwbMode": controls.AwbModeEnum.Auto.value,
            "AeMeteringMode": controls.AeMeteringModeEnum.CentreWeighted.value,
            "AeExposureMode": controls.AeExposureModeEnum.Long.value,
            "AfMetering": controls.AfMeteringEnum.Windows.value,
            "AfWindows": [rect],
            "AfMode": controls.AfModeEnum.Continuous.value,
            "AfRange": controls.AfRangeEnum.Macro.value
        }
        self.preview_config = self.cam.create_preview_configuration(
            controls=ctrl)
        self.still_config = self.cam.create_still_configuration(
            controls=ctrl)
        self.cam.configure(self.still_config)  # type: ignore
        self.cam.start()
        self.folder = folder
        self.aruco_dict = None

    def make_picture(self, settings: CamSettings = {}, preview=False) -> bytes:
        data = BytesIO()
        print("Kamera aktiviert!")
        self.set_settings(settings)
        req = self.cam.capture_request(wait=True, flush=True)
        req.save("main", data, format="jpeg")
        metadata = req.get_metadata()
        print("Fokus (real): ", metadata["LensPosition"])
        req.release()
        """
        if metadata["LensPosition"] != 0:
            focus = 1./metadata["LensPosition"]
        else:
            focus = 0
        focus = int(focus*100)

        
        exif_dict = piexif.load(data)
        exif_dict["Exif"][piexif.ExifIFD.FocalLength] = (474, 100)
        exif_dict["Exif"][piexif.ExifIFD.SubjectDistance] = (focus, 100)
        exif_dict["Exif"][piexif.ExifIFD.BodySerialNumber] = gethostname()
        exif_bytes = piexif.dump(exif_dict)
        piexif.insert(exif_bytes, data)
        """

        print("Bild gemacht!")
        data.seek(0)
        return data.read()

    def save_picture(self, settings: CamSettingsWithFilename) -> str:
        print("Kamera aktiviert!")
        settings = self.set_settings(settings)
        file = self.folder + settings['filename']

        req = self.cam.capture_request(wait=True, flush=True)
        metadata = req.get_metadata()
        print("Fokus (real): ", metadata["LensPosition"])
        req.save("main", file)
        req.release()
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
        m = self.cam.capture_metadata()
        return m
    CamSet = TypeVar('CamSet', CamSettings, CamSettingsWithFilename)

    def set_settings(self, settings: CamSet) -> CamSet:
        if isinstance(settings, dict):
            if 'focus' in settings and settings['focus'] != 0:
                print("focus: ", settings['focus'])
                self.focus(settings['focus'])
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
            print("Fokus nicht verändern")
            pass
        elif (focus == -1):
            print("Autofokus")
            self.cam.set_controls({"AfMode": controls.AfModeEnum.Continuous})
            # self.cam.autofocus_cycle()
        else:
            print("Fokus (soll): ", focus)
            self.cam.set_controls(
                {"AfMode": controls.AfModeEnum.Manual, "LensPosition": focus})
            for i in range(10):
                m = self.cam.capture_metadata()
                if abs(m["LensPosition"] - focus) < 0.01:
                    print("Fokus erreicht nach ", i*0.1, "s")
                    break
                sleep(0.1)
        return "Fokus"

    def get_status(self) -> dict[str, Any]:
        return self.cam.camera_properties

    def aruco(self, inform_after_picture: None | Callable[[], None] = None) -> list[dict[str, int | float]]:
        from cv2.aruco import Dictionary_create, DetectorParameters, CORNER_REFINE_SUBPIX, detectMarkers
        if self.aruco_dict is None:
            self.aruco_dict = Dictionary_create(32, 3)
            self.parameter = DetectorParameters.create()
            self.parameter.cornerRefinementMethod = CORNER_REFINE_SUBPIX

        req = self.cam.capture_request(flush=True)
        im = req.make_array("main")
        req.release()
        print("Aruco Bild gemacht!")
        if inform_after_picture != None:
            inform_after_picture()
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

    def pause(self):
        self.cam.stop()

    def resume(self):
        self.cam.start()
