#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@author: Florian Timm
@version: 2024.03.11
"""

from typing import Required, TypedDict, NotRequired, Union,  TypeAlias, NamedTuple


class CamSettingsWithoutFilename(TypedDict):
    focus: NotRequired[float]
    iso: NotRequired[float]
    shutter_speed: NotRequired[float]


class CamSettingsOptionalFilename(CamSettingsWithoutFilename):
    filename: NotRequired[str]


class CamSettingsWithFilename(CamSettingsWithoutFilename):
    filename: Required[str]


CamSettings: TypeAlias = Union[CamSettingsOptionalFilename,
                               CamSettingsWithFilename]


class ConfigServer(TypedDict):
    folder: str
    leds: str


class ConfigKamera(TypedDict):
    WebPort: int
    Folder: str


class ConfigBoth(TypedDict):
    BroadCastPort: int


class Config(TypedDict):
    kameras: ConfigKamera
    both: ConfigBoth
    server: ConfigServer


class ArucoMarkerPos(TypedDict):
    id: int
    corner: int
    x: float
    y: float


class Point2D(NamedTuple):
    x: float
    y: float


class Point3D(NamedTuple):
    x: float
    y: float
    z: float

    def __str__(self) -> str:
        return f"x: {self.x}, y: {self.y}, z: {self.z}"


Point: TypeAlias = Union[Point2D, Point3D]


class ArucoMarkerCorners():
    top_left: Point3D | None
    top_right: Point3D | None
    bottom_right: Point3D | None
    bottom_left: Point3D | None

    def __init__(self, liste: dict[int, Point3D] | None = None):
        if liste is not None:
            self.top_left = liste.get(0)
            self.top_right = liste.get(1)
            self.bottom_right = liste.get(2)
            self.bottom_left = liste.get(3)
        else:
            self.top_left = None
            self.top_right = None
            self.bottom_right = None
            self.bottom_left = None

    def __iter__(self):
        yield self.top_left
        yield self.top_right
        yield self.bottom_right
        yield self.bottom_left

    def __len__(self):
        return 4

    def __getitem__(self, key: int) -> Point3D | None:
        if key == 0:
            return self.top_left
        if key == 1:
            return self.top_right
        if key == 2:
            return self.bottom_right
        if key == 3:
            return self.bottom_left
        raise IndexError

    def __setitem__(self, key: int, value: Point3D | None) -> None:
        if key == 0:
            self.top_left = value
            return
        if key == 1:
            self.top_right = value
            return
        if key == 2:
            self.bottom_right = value
            return
        if key == 3:
            self.bottom_left = value
            return
        raise IndexError

    def __str__(self) -> str:
        return f"top_left: {self.top_left}, top_right: {self.top_right}, bottom_right: {self.bottom_right}, bottom_left: {self.bottom_left}"

    def __repr__(self) -> str:
        return f"ArucoMarkerCorners({self.top_left}, {self.top_right}, {self.bottom_right}, {self.bottom_left})"


class Metadata(TypedDict):
    SensorTimestamp: NotRequired[int]
    ScalerCrop: NotRequired[list[int]]
    AfPauseState: NotRequired[int]
    ExposureTime: NotRequired[int]
    SensorBlackLevels: NotRequired[list[int]]
    AnalogueGain: NotRequired[float]
    FrameDuration: NotRequired[int]
    SensorTemperature: NotRequired[float]
    LensPosition: NotRequired[float]
    DigitalGain: NotRequired[float]
    AfState: NotRequired[int]
    AeLocked: NotRequired[bool]
    Lux: NotRequired[float]
    FocusFoM: NotRequired[int]
    ColourGains: NotRequired[list[float]]
    ColourTemperature: NotRequired[int]
    ColourCorrectionMatrix: NotRequired[list[float]]


class ArucoMetaBroadcast(TypedDict):
    aruco: list[ArucoMarkerPos]
    meta: Metadata


class CameraExterior (TypedDict):
    x: float
    y: float
    z: float
    roll: float
    pitch: float
    yaw: float
