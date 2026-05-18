import enum


class BodyType(str, enum.Enum):
    TENT = "tent"
    REFRIGERATOR = "refrigerator"
    FLATBED = "flatbed"
    TANK = "tank"
    CONTAINER = "container"
    OTHER = "other"
