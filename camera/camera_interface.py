#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@author: Florian Timm
@version: 2024.03.11
"""

# stream: https://github.com/raspberrypi/picamera2/issues/366#issuecomment-1285888051

from io import BytesIO
from json import dump
from threading import Thread
from typing import Any, overload
from camera.camera_aruco import Aruco

from picamera2 import Picamera2
from picamera2.request import CompletedRequest
from libcamera import controls  # type: ignore
from time import sleep
import piexif
from socket import gethostname
from common.typen import ArucoMarkerPos, CamSettings, CamSettingsOptionalFilename, CamSettingsWithFilename
from typing import Callable
from common.logger import Logger


class CameraInterface(object):
    def __init__(self, folder: str):
        tuning: dict[str, Any] = Picamera2.load_tuning_file(
            "imx708.json", dir='./camera/tuning/')
        self.__cam: Picamera2 = Picamera2(tuning=tuning)
        self.__rgb_config: dict[str,
                                Any] = self.__cam.create_still_configuration()
        self.__cam.configure(self.__rgb_config)  # type: ignore
        self.__cam.start()
        scm: list[int] = self.__cam.camera_properties['ScalerCropMaximum']
        self.__cam.stop()
        h: int = scm[3]-scm[1]
        w: int = scm[2]-scm[0]
        rect: tuple[int, int, int, int] = (
            scm[0]+2*w//5, scm[1]+2*h//5, w//5, h//5)
        Logger().info("Fokus-Fenster:  %s", rect)
        self.__DEFAULT_CTRL: dict[str, Any] = {
            "AwbMode": controls.AwbModeEnum.Auto.value,
            "AeMeteringMode": controls.AeMeteringModeEnum.CentreWeighted.value,
            "AeExposureMode": controls.AeExposureModeEnum.Long.value,
            "AfMetering": controls.AfMeteringEnum.Windows.value,
            "AfWindows": [rect],
            "AfMode": controls.AfModeEnum.Continuous.value,
            "AfRange": controls.AfRangeEnum.Macro.value
        }
        ctrl = self.__DEFAULT_CTRL.copy()
        ctrl["AnalogueGain"] = 1.0
        self.__rgb_config = self.__cam.create_still_configuration(
            controls=ctrl)
        self.yuv_config = self.__cam.create_still_configuration(
            main={"format": "YUV420"}, controls=ctrl)
        self.__cam.configure(self.__rgb_config)  # type: ignore
        self.__cam.start()
        self.__folder = folder
        self.__aruco = Aruco()

    def make_picture(self, settings: CamSettings = {}, preview=False) -> bytes:
        data = BytesIO()
        Logger().info("Kamera aktiviert!")
        req, metadata, settings = self.__capture_photo(settings)
        req.save("main", data, format="jpeg")
        Logger().info("Fokus (real):  %s", metadata["LensPosition"])
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

        Logger().info("Bild gemacht!")
        data.seek(0)
        return data.read()

    @overload
    def __capture_photo(
        self, settings: CamSettingsWithFilename) -> tuple[CompletedRequest, dict[str, Any], CamSettingsWithFilename]: ...

    @overload
    def __capture_photo(
        self, settings: CamSettingsOptionalFilename) -> tuple[CompletedRequest, dict[str, Any], CamSettingsOptionalFilename]: ...

    def __capture_photo(self, settings: CamSettings) -> tuple[CompletedRequest, dict[str, Any], CamSettings]:
        self.resume()
        if settings:
            settings = self.set_settings(settings)
        req, metadata = self.__request_capture_with_meta()
        return req, metadata, settings

    def __request_capture_with_meta(self):
        req: CompletedRequest = self.__cam.capture_request(  # type: ignore
            wait=True, flush=True)
        metadata: dict[str, Any] = req.get_metadata()
        return req, metadata

    def save_picture(self, settings: CamSettingsWithFilename, aruco_callback: None | Callable[[list[ArucoMarkerPos], dict[str, Any]], None]) -> list[dict[str, int | float]]:
        Logger().info("Kamera aktiviert!")
        req, metadata, set = self.__capture_photo(settings)

        file = self.__folder + settings['filename']
        Logger().info("Fokus (real):  %s", metadata["LensPosition"])
        req.save("main", file)
        aruco_marker = []

        def aruco_search(img, aruco_callback: Callable[[list[ArucoMarkerPos], dict[str, Any]], None]):

            aruco_marker = self.__aruco.detect_from_rgb(img)
            dump(aruco_marker, open(file + ".aruco", "w"), indent=2)
            aruco_callback(aruco_marker, metadata)
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

        Logger().info("Bild %s gemacht!", file)
        return aruco_marker

    def meta(self) -> None | dict[str, Any]:
        self.resume()
        _, m = self.__cam.capture_metadata(wait=True)  # type: ignore
        return m  # type: ignore

    @overload
    def set_settings(
        self, settings: CamSettingsWithFilename) -> CamSettingsWithFilename: ...

    @overload
    def set_settings(
        self, settings: CamSettingsOptionalFilename) -> CamSettingsOptionalFilename: ...

    def set_settings(self, settings: CamSettings) -> CamSettings:
        if isinstance(settings, dict):
            if 'focus' in settings and settings['focus'] != 0:
                Logger().info("focus: %s", settings['focus'])
                self.focus(settings['focus'])
            with self.__cam.controls as controls:
                if 'iso' in settings:
                    Logger().info("iso: %s", settings['iso'])
                    controls.AnalogueGain = settings['iso']/100.
                if 'shutter_speed' in settings:
                    Logger().info("shutter_speed: %s",
                                  settings['shutter_speed'])
                    controls.ExposureTime = settings['shutter_speed']
                if 'white_balance' in settings:
                    Logger().info("white_balance: %s",
                                  settings['white_balance'])
                    controls.AwbMode = settings['white_balance']
        return settings

    def focus(self, focus: float) -> str:
        if (focus == -2):
            Logger().info("Fokus nicht verändern")
            pass
        elif (focus == -1):
            Logger().info("Autofokus")
            self.__cam.set_controls(self.__DEFAULT_CTRL)
            # self.cam.autofocus_cycle()
        else:
            Logger().info("Fokus (soll): %s", focus)
            self.__cam.set_controls(
                {"AfMode": controls.AfModeEnum.Manual, "LensPosition": focus})
            for i in range(10):
                m = self.__cam.capture_metadata()
                if abs(m["LensPosition"] - focus) < 0.01:  # type: ignore
                    Logger().info("Fokus erreicht nach  %s s", i*0.1)
                    break
                sleep(0.1)
        return "Fokus"

    def __get_status(self) -> dict[str, Any]:
        return self.__cam.camera_properties

    def find_aruco(self, inform_after_picture: None | Callable[[], None] = None) -> list[ArucoMarkerPos]:
        # directly shoted in YUV and filtered to grayscale
        # https://github.com/raspberrypi/picamera2/issues/698

        _, _, w, h = self.__cam.camera_properties['ScalerCropMaximum']

        if not self.__cam.started:
            self.__cam.start(self.yuv_config)
            req, meta = self.__request_capture_with_meta()
            image = req.make_array('main')[:h, :w]
            req.release()
        else:
            image = self.__cam.switch_mode_and_capture_array(  # type: ignore
                self.yuv_config, 'main', wait=True)[:h, :w]

        Logger().info("Aruco Bild gemacht!")
        if inform_after_picture != None:
            inform_after_picture()
        return self.__aruco.detect(image)

    def pause(self):
        if self.__cam.started:
            self.__cam.stop()

    def resume(self):
        if not self.__cam.started:
            self.__cam.start()
