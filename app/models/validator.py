import re
from typing import Tuple

from pydantic import BaseModel, field_validator

from app.models.schemas import DataType, Permission, TagConfig


class DigitalRegisterInput(BaseModel):
    register_bit: str

    @field_validator("register_bit")
    def validate_register_bit(cls, v):
        # 정규식으로 형식 검사 (숫자.숫자 형식)
        if not re.match(r"^\d+\.\d+$", v):
            raise ValueError(
                "입력 형식이 잘못되었습니다. '레지스터.비트' 형식으로 입력해주세요."
            )

        register, bit = map(int, v.split("."))

        # 레지스터 범위 검사 (예: 1000-3000 사이)
        if not (0 <= register <= 9999):
            raise ValueError("레지스터 주소는 0-9999 사이여야 합니다.")

        # 비트 위치 검사 (0-15)
        if not (0 <= bit <= 15):
            raise ValueError("비트 위치는 0-15 사이여야 합니다.")

        return v

    def parse_values(self) -> Tuple[int, int]:
        """검증된 register_bit 문자열을 레지스터와 비트 값으로 분리"""
        register, bit = map(int, self.register_bit.split("."))
        return register, bit


def validate_tag_config(tag_config: TagConfig) -> TagConfig:
    """태그 설정 유효성 검증"""
    # 대소문자 구분 없이 DataType 검증
    data_type = tag_config.data_type.upper()
    if data_type not in [dt.value.upper() for dt in DataType]:
        valid_types = ", ".join([dt.value for dt in DataType])
        raise ValueError(f"잘못된 데이터 타입입니다. 가능한 값: {valid_types}")

    # 대소문자 구분 없이 Permission 검증
    permission = tag_config.permission.upper()
    if permission not in [p.value.upper() for p in Permission]:
        valid_permissions = ", ".join([p.value for p in Permission])
        raise ValueError(f"잘못된 권한입니다. 가능한 값: {valid_permissions}")

    # 디지털 타입일 경우 레지스터 형식 검증
    if data_type != DataType.ANALOG.value.upper():
        if not re.match(r"^\d+\.\d+$", tag_config.real_register):
            raise ValueError(
                "디지털 타입의 레지스터는 '레지스터.비트' 형식이어야 합니다. (예: 2000.0)"
            )

        register, bit = map(int, tag_config.real_register.split("."))

        # 레지스터 범위 검사
        if not (0 <= register <= 9999):
            raise ValueError("레지스터 주소는 0-9999 사이여야 합니다.")

        # 비트 위치 검사 (0-15)
        if not (0 <= bit <= 15):
            raise ValueError("비트 위치는 0-15 사이여야 합니다.")

    # 정확한 enum 값으로 변환
    tag_config.data_type = next(dt for dt in DataType if dt.value.upper() == data_type)
    tag_config.permission = next(p for p in Permission if p.value.upper() == permission)

    return tag_config
