#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@author: Florian Timm
@version: 2024.03.11
"""

from typing import Any, Required, TypedDict, NotRequired, Union,  TypeAlias


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


class ArucoMetaBroadcast(TypedDict):
    aruco: list[ArucoMarkerPos]
    meta: dict[str, Any]
