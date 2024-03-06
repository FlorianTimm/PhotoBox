#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@author: Florian Timm
@version: 2024.02.28
"""

# stream: https://github.com/raspberrypi/picamera2/issues/366#issuecomment-1285888051

from io import BytesIO
from json import dump
from threading import Thread
from typing import Any, TypeVar
from camera_aruco import Aruco

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
        tuning: Dict[str, Any] = Picamera2.load_tuning_file(
            "imx708.json", dir='./tuning/')
        self.cam: Picamera2 = Picamera2(tuning=tuning)
        self.rgb_config: dict[str, Any] = self.cam.create_still_configuration()
        self.cam.configure(self.rgb_config)  # type: ignore
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
        self.aruco = Aruco()

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
        req: CompletedRequest = self.cam.capture_request(  # type: ignore
            wait=True, flush=True)
        metadata: dict[str, Any] = req.get_metadata()
        return req, metadata, settings

    def save_picture(self, settings: CamSettingsWithFilename, aruco_callback: None | Callable[[List[dict[str, int | float]]], None]) -> List[dict[str, int | float]]:
        print("Kamera aktiviert!")
        req, metadata, settings = self.capture_photo(settings)
        file = self.folder + settings['filename']
        print("Fokus (real): ", metadata["LensPosition"])
        req.save("main", file)
        aruco_marker = []

        def aruco_search(img, aruco_callback: Callable[[List[dict[str, int | float]]], None]):

            aruco_marker = self.aruco.detect_from_rgb(img)
            dump(aruco_marker, open(file + ".aruco", "w"), indent=2)
            aruco_callback(aruco_marker)
        if aruco_callback:
            img = req.make_array("main")
            Thread(target=aruco_search, args=(
                img, aruco_callback), name="Aruco").start()
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
        return aruco_marker

    def meta(self) -> None | dict[str, Any]:
        self.resume()
        _, m = self.cam.capture_metadata(wait=True)  # type: ignore
        return m  # type: ignore

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
            self.cam.set_controls(self.DEFAULT_CTRL)
            # self.cam.autofocus_cycle()
        else:
            print("Fokus (soll): ", focus)
            self.cam.set_controls(
                {"AfMode": controls.AfModeEnum.Manual, "LensPosition": focus})
            for i in range(10):
                m = self.cam.capture_metadata()
                if abs(m["LensPosition"] - focus) < 0.01:  # type: ignore
                    print("Fokus erreicht nach ", i*0.1, "s")
                    break
                sleep(0.1)
        return "Fokus"

    def get_status(self) -> dict[str, Any]:
        return self.cam.camera_properties

    def find_aruco(self, inform_after_picture: None | Callable[[], None] = None) -> list[dict[str, int | float]]:
        # directly shoted in YUV and filtered to grayscale
        # https://github.com/raspberrypi/picamera2/issues/698

        _, _, w, h = self.cam.camera_properties['ScalerCropMaximum']

        if not self.cam.started:
            self.cam.start(self.yuv_config)
            image = self.cam.capture_array('main', wait=True)[  # type: ignore
                :h, :w]
        else:
            image = self.cam.switch_mode_and_capture_array(  # type: ignore
                self.yuv_config, 'main', wait=True)[:h, :w]

        print("Aruco Bild gemacht!")
        if inform_after_picture != None:
            inform_after_picture()
        return self.aruco.detect(image)

    def pause(self):
        if self.cam.started:
            self.cam.stop()

    def resume(self):
        if not self.cam.started:
            self.cam.start()
