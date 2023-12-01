from typing import TypedDict, NotRequired


class CamSettings(TypedDict):
    focus: NotRequired[float]
    filename: NotRequired[str]


class CamSettingsWithFilename(CamSettings):
    filename: str
