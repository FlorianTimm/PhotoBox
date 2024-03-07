from typing import Any, TypedDict, NotRequired


class CamSettings(TypedDict):
    focus: NotRequired[float]
    filename: NotRequired[str]
    iso: NotRequired[float]
    shutter_speed: NotRequired[float]


class CamSettingsWithFilename(CamSettings):
    filename: str


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
