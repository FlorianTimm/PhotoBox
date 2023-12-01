class CamSettings(TypedDict):
    focus: NotRequired[float]
    filename: NotRequired[str]


class CamSettingsWithFilename(CamSettings):
    filename: str
