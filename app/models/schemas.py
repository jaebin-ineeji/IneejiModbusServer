from pydantic import BaseModel, Field
from enum import Enum
from typing import Any, Optional, Dict, List


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

# 자동 제어를 위한 태그 설정
class AutoControlTagConfig(BaseModel):
    tag_name: str
    target_value: str = Field(..., description="제어 목표 값")

# 자동 제어 설정
class AutoControlConfig(BaseModel):
    enabled: bool = Field(default=False, description="자동 제어 활성화 여부")
    machine_name: str = Field(..., description="제어할 기계 이름") 
    tags: List[AutoControlTagConfig] = Field(default=[], description="제어할 태그 목록")

# 자동 제어 상태
class AutoControlStatus(BaseModel):
    enabled: bool
    machine_name: str
    tags: List[AutoControlTagConfig]
    last_executed: Optional[str] = None

# 기계별 자동 제어 설정
class MachineAutoControlConfig(BaseModel):
    machine_name: str = Field(..., description="제어할 기계 이름")
    tags: List[AutoControlTagConfig] = Field(default=[], description="제어할 태그 목록")

# 전역 자동 제어 설정
class GlobalAutoControlConfig(BaseModel):
    enabled: bool = Field(default=False, description="자동 제어 모드 활성화 여부")
    machines: List[MachineAutoControlConfig] = Field(default=[], description="제어할 기계 목록")

# 전역 자동 제어 상태
class GlobalAutoControlStatus(BaseModel):
    enabled: bool
    machines: List[MachineAutoControlConfig]
    last_executed: Optional[str] = None