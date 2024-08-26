#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This module contains the type definitions used in the project.

Author: Florian Timm
Version: 2024.06.20
"""

from typing import Required, TypedDict, NotRequired, Union,  TypeAlias, NamedTuple


class CommonCamSettings(TypedDict):
    """
    Represents the common camera settings.

    Attributes:
        exposure_value (float): The exposure value of the camera.
        exposure_sync (bool): Indicates whether the exposure is synchronized.
    """
    exposure_value: Required[float]
    exposure_sync: Required[bool]
    # shutter_speed: NotRequired[float]


class CamSettingsWithoutFilename(TypedDict):
    """
    Represents the camera settings without the filename.
    
    Attributes:
        focus (float): The focus value of the camera.
        iso (float): The ISO value of the camera.
        shutter_speed (float): The shutter speed of the camera.
    """
    focus: NotRequired[float]
    iso: NotRequired[float]
    shutter_speed: NotRequired[float]


class CamSettingsOptionalFilename(CamSettingsWithoutFilename):
    """
    Represents the camera settings with an optional filename.
    
    Attributes:
        filename (str): The filename of the camera.
        focus (float): The focus value of the camera.
        iso (float): The ISO value of the camera.
        shutter_speed (float): The shutter speed of the camera.
    """

    filename: NotRequired[str]


class CamSettingsWithFilename(CamSettingsWithoutFilename):
    """
    Represents the camera settings with filename.
    
    Attributes:
        filename (str): The filename of the camera.
        focus (float): The focus value of the camera.
        iso (float): The ISO value of the camera.
        shutter_speed (float): The shutter speed of the camera.
    """
    filename: Required[str]


CamSettings: TypeAlias = Union[CamSettingsOptionalFilename,
                               CamSettingsWithFilename]


class ConfigServer(TypedDict):
    """
    Represents the server configuration.
    
    Attributes:
        folder (str): The folder of the server.
        leds (str): The LEDs of the server.
    """
    folder: str
    leds: str


class ConfigKamera(TypedDict):
    """
    Represents the camera configuration.
    
    Attributes:
        WebPort (int): The web port of the camera.
        Folder (str): The folder of the camera.
    """
    WebPort: int
    Folder: str


class ConfigBoth(TypedDict):
    """
    Represents the configuration for both the server and the camera.

    Attributes:
        BroadCastPort (int): The broadcast port.
    """
    BroadCastPort: int


class Config(TypedDict):
    """
    Represents the configuration of the server and the camera.
    
    Attributes:
        kameras (ConfigKamera): The camera configuration.
        both (ConfigBoth): The configuration for both the server and the camera.
        server (ConfigServer): The server configuration.
    """
    kameras: ConfigKamera
    both: ConfigBoth
    server: ConfigServer


class ArucoMarkerPos(TypedDict):
    """
    Represents the position of an Aruco marker.

    Attributes:
        id (int): The ID of the Aruco marker.
        corner (int): The corner of the Aruco marker.
        x (float): The x-coordinate of the Aruco marker.
        y (float): The y-coordinate of the Aruco marker.
    """
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
    """
    Represents the corners of an Aruco marker.
    
    Attributes:
        top_left (Point3D | None): The top left corner of the Aruco marker.
        top_right (Point3D | None): The top right corner of the Aruco marker.
        bottom_right (Point3D | None): The bottom right corner of the Aruco marker.
        bottom_left (Point3D | None): The bottom left corner of the Aruco marker.
        
        Methods:
            __init__: Initializes the ArucoMarkerCorners object.
            __iter__: Returns an iterator over the corners.
            __len__: Returns the number of corners.
            __getitem__: Returns the corner at the specified index.
            __setitem__: Sets the corner at the specified index.
            __str__: Returns a string representation of the ArucoMarkerCorners object.
            __repr__: Returns a string representation of the ArucoMarkerCorners object.
        """
    top_left: Point3D | None
    top_right: Point3D | None
    bottom_right: Point3D | None
    bottom_left: Point3D | None

    def __init__(self, liste: dict[int, Point3D] | None = None):
        """
        Initializes the ArucoMarkerCorners object.
        
        Args:
            liste (dict[int, Point3D] | None): A dictionary containing the corners of the Aruco marker.
        """
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
            """Iterates over the four corners of the object.

            Yields:
                Point: The top left corner of the object.
                Point: The top right corner of the object.
                Point: The bottom right corner of the object.
                Point: The bottom left corner of the object.
            """
            yield self.top_left
            yield self.top_right
            yield self.bottom_right
            yield self.bottom_left

    def __len__(self):
        """Returns the number of corners of the object."""
        return 4

    def __getitem__(self, key: int) -> Point3D | None:
        """Returns the corner at the specified index.

        Args:
            key (int): The index of the corner.

        Returns:
            Point: The corner at the specified index.

        Raises:
            IndexError: If the index is out of range.
        """
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
        """
        Sets the corner at the specified index.
        
        Args:
            key (int): The index of the corner.
            value (Point3D | None): The corner to set.  
            
        Raises:         
            IndexError: If the index is out of range.
        """
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
        """
        Returns a string representation of the ArucoMarkerCorners object.
        """
        return f"top_left: {self.top_left}, top_right: {self.top_right}, bottom_right: {self.bottom_right}, bottom_left: {self.bottom_left}"

    def __repr__(self) -> str:
        """
        Returns a string representation of the ArucoMarkerCorners object.
        """
        return f"ArucoMarkerCorners({self.top_left}, {self.top_right}, {self.bottom_right}, {self.bottom_left})"


class Metadata(TypedDict):
    """
    Represents the metadata of an image.

    Attributes:
        SensorTimestamp (int): The sensor timestamp.
        ScalerCrop (list[int]): The scaler crop.
        AfPauseState (int): The autofocus pause state.
        ExposureTime (int): The exposure time.
        SensorBlackLevels (list[int]): The sensor black levels.
        AnalogueGain (float): The analogue gain.
        FrameDuration (int): The frame duration.
        SensorTemperature (float): The sensor temperature.
        LensPosition (float): The lens position.
        DigitalGain (float): The digital gain.
        AfState (int): The autofocus state.
        AeLocked (bool): Indicates whether the auto exposure is locked.
        Lux (float): The lux value.
        FocusFoM (int):
        ColourGains (list[float]): The colour gains.
        ColourTemperature (int): The colour temperature.
        ColourCorrectionMatrix (list[float]): The colour correction matrix.
    """

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
    """
    Represents the Aruco meta broadcast.
    
    Attributes:
        aruco (list[ArucoMarkerPos]): The Aruco markers.
        meta (Metadata): The metadata.
    """
    aruco: list[ArucoMarkerPos]
    meta: Metadata


class CameraExterior (TypedDict):
    """
    Represents the exterior orientation of the camera.
    
    Attributes:
        x (float): The x-coordinate of the camera.
        y (float): The y-coordinate of the camera.
        z (float): The z-coordinate of the camera.
        roll (float): The roll of the camera.
        pitch (float): The pitch of the camera.
        yaw (float): The yaw of the camera.
    """
    x: float
    y: float
    z: float
    roll: float
    pitch: float
    yaw: float
