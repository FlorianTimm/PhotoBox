from typing import TypedDict, NotRequired


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
