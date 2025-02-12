import re
from typing import Tuple

from pydantic import BaseModel, field_validator


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
