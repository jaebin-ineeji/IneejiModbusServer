from pydantic import BaseModel
from enum import Enum
from typing import Any, Optional, Dict


class ApiResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None


class DataType(str, Enum):
    ANALOG = "Analog"
    DIGITAL = "Digital"
    DIGITAL_AM = "DigitalAM"
    DIGITAL_RM = "DigitalRM"


class Permission(str, Enum):
    READ = "Read"
    READ_WRITE = "ReadWrite"


class TagConfig(BaseModel):
    data_type: DataType
    logical_register: str
    real_register: str
    permission: Permission
    slave: int


class MachineConfig(BaseModel):
    ip: str
    tags: Dict[str, TagConfig]
