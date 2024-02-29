#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@author: Florian Timm
@version: 2024.02.28
"""

# stream: https://github.com/raspberrypi/picamera2/issues/366#issuecomment-1285888051

from io import BytesIO
from typing import Any, TypeVar
from picamera2 import Picamera2
from picamera2.request import CompletedRequest
from libcamera import controls  # type: ignore
from time import sleep
import piexif
from socket import gethostname
from typen import CamSettings, CamSettingsWithFilename
from typing import Dict, Tuple, List, Callable


class CameraInterface(object):
    CamSet = TypeVar('CamSet', CamSettings, CamSettingsWithFilename)

    def __init__(self, folder: str):
        tuning = Picamera2.load_tuning_file("imx708.json", dir='./tuning/')
        self.cam: Picamera2 = Picamera2(tuning=tuning)
        self.rgb_config = self.cam.create_still_configuration()
        self.cam.configure(self.rgb_config)
        self.cam.start()
        scm: List[int] = self.cam.camera_properties['ScalerCropMaximum']
        self.cam.stop()
        h: int = scm[3]-scm[1]
        w: int = scm[2]-scm[0]
        rect: Tuple[int, int, int, int] = (
            scm[0]+2*w//5, scm[1]+2*h//5, w//5, h//5)
        print("Fokus-Fenster: ", rect)
        self.DEFAULT_CTRL: Dict[str, Any] = {
            "AwbMode": controls.AwbModeEnum.Auto.value,
            "AeMeteringMode": controls.AeMeteringModeEnum.CentreWeighted.value,
            "AeExposureMode": controls.AeExposureModeEnum.Long.value,
            "AfMetering": controls.AfMeteringEnum.Windows.value,
            "AfWindows": [rect],
            "AfMode": controls.AfModeEnum.Continuous.value,
            "AfRange": controls.AfRangeEnum.Macro.value
        }
        ctrl = self.DEFAULT_CTRL.copy()
        ctrl["AnalogueGain"] = 1.0
        self.rgb_config = self.cam.create_still_configuration(
            controls=ctrl)
        self.yuv_config = self.cam.create_still_configuration(
            main={"format": "YUV420"}, controls=ctrl)
        self.cam.configure(self.rgb_config)  # type: ignore
        self.cam.start()
        self.folder = folder
        self.aruco_dict = None

    def make_picture(self, settings: CamSettings = {}, preview=False) -> bytes:
        data = BytesIO()
        print("Kamera aktiviert!")
        req, metadata, settings = self.capture_photo(settings)
        req.save("main", data, format="jpeg")
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

    def capture_photo(self, settings: CamSet) -> Tuple[CompletedRequest, Dict[str, Any], CamSet]:
        self.resume()
        if settings:
            settings = self.set_settings(settings)
        req: CompletedRequest = self.cam.capture_request(wait=True, flush=True)
        metadata = req.get_metadata()
        return req, metadata, settings

    def save_picture(self, settings: CamSettingsWithFilename) -> str:
        print("Kamera aktiviert!")
        req, metadata, settings = self.capture_photo(settings)
        file = self.folder + settings['filename']
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

    def meta(self) -> None | dict[str, Any]:
        self.resume()
        _, m = self.cam.capture_metadata(wait=True)  # type: ignore
        return m

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
                if 'yuv' in settings:
                    print("yuv: ", settings['yuv'])
                    controls.f
        return settings

    def focus(self, focus: float) -> str:
        if (focus == -2):
            print("Fokus nicht verändern")
            pass
        elif (focus == -1):
            print("Autofokus")
            self.cam.set_controls(self.DEFAULT_CTRL)
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
        from cv2.aruco import Dictionary_create, DetectorParameters, CORNER_REFINE_SUBPIX, detectMarkers  # type: ignore

        if self.aruco_dict is None:
            self.aruco_dict = Dictionary_create(32, 3)
            self.parameter = DetectorParameters.create()
            self.parameter.cornerRefinementMethod = CORNER_REFINE_SUBPIX
        cs: CamSettings = {}
        _, _, w, h = cam.camera_properties['ScalerCropMaximum']

        self.cam.stop()
        self.cam.start(self.yuv_config)
        req, _, _ = self.capture_photo(cs)
        im = req.make_array("main")[:h, :w]
        req.release()
        self.cam.stop()
        self.cam.start(self.rgb_config)

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
        if self.cam.started:
            self.cam.stop()

    def resume(self):
        if not self.cam.started:
            self.cam.start()
