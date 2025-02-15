from pydantic import BaseModel
from enum import Enum
from typing import Any, Optional, Dict


class ApiResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None


class Mode(str, Enum):
    AUTO = "AUTO"
    MANUAL = "MANUAL"
    LOCAL = "LOCAL"
    REMOTE = "REMOTE"


class TagType(str, Enum):
    ANALOG = "Analog"
    DIGITAL = "Digital"
    DIGITAL_AM = "DigitalAM"
    DIGITAL_RM = "DigitalRM"


class Permission(str, Enum):
    READ = "Read"
    READ_WRITE = "ReadWrite"


class TagConfig(BaseModel):
    tag_type: TagType
    logical_register: str
    real_register: str
    permission: Permission


class MachineConfig(BaseModel):
    ip: str
    port: int
    slave: int
    tags: Dict[str, TagConfig]


# 태그설정 벌크 임포트/익스포트 스키마
class TagConfigFormat(BaseModel):
    tag_type: str
    logical_register: str
    real_register: str
    permission: str


class MachineConfigFormat(BaseModel):
    ip: str
    port: int
    slave: int
    tags: Dict[str, TagConfigFormat]
