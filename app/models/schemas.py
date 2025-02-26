from pydantic import BaseModel, Field
from enum import Enum
from typing import Any, Optional, Dict


class ServiceResult(BaseModel):
    """서비스 계층의 결과를 표현하는 모델"""

    success: bool
    message: str
    data: Optional[Any] = None


class ErrorResponse(BaseModel):
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


# class MetaResponse(BaseModel):
#     timestamp: datetime = Field(default_factory=datetime.now)
#     pagination: Optional[Dict[str, int]] = None
#     class Config:
#         json_encoders = {
#             datetime: lambda v: v.isoformat()
#         }


class ApiResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None
    error: Optional[ErrorResponse] = None
    # meta: MetaResponse = Field(default_factory=MetaResponse)


class Mode(str, Enum):
    AUTO = "AUTO"
    MANUAL = "MANUAL"
    LOCAL = "LOCAL"
    REMOTE = "REMOTE"
    ON = "ON"
    OFF = "OFF"


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
    ip: str = Field(..., description="기계의 IP 주소", examples=["172.30.1.97"])
    port: int = 502
    slave: int = 1
    tags: Dict[str, TagConfig] = {}


# 태그설정 벌크 임포트/익스포트 스키마
class TagConfigFormat(BaseModel):
    tag_type: TagType
    logical_register: str
    real_register: str
    permission: Permission


class MachineConfigFormat(BaseModel):
    ip: str
    port: int = 502
    slave: int = 1
    tags: Dict[str, TagConfigFormat] = {}
