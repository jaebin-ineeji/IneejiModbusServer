# app/services/exceptions.py
from enum import Enum

from fastapi import HTTPException
class ModbusError(Exception):
    def __init__(self, message: str, error_code: int = 500):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class ModbusConnectionError(ModbusError):
    pass


class ModbusReadError(ModbusError):
    pass


class ModbusWriteError(ModbusError):
    pass


class ErrorCode(Enum):
    UNKNOWN_ERROR = "UNKNOWN_ERROR"
    # 태그 관련 에러
    TAG_NOT_FOUND = "TAG_NOT_FOUND"
    TAG_ALREADY_EXISTS = "TAG_ALREADY_EXISTS"
    TAG_VALIDATION_ERROR = "TAG_VALIDATION_ERROR"
    TAG_WRITE_ERROR = "TAG_WRITE_ERROR"
    TAG_READ_ERROR = "TAG_READ_ERROR"
    
    # 기계 관련 에러
    MACHINE_NOT_FOUND = "MACHINE_NOT_FOUND"
    MACHINE_ALREADY_EXISTS = "MACHINE_ALREADY_EXISTS"
    MACHINE_ADD_ERROR = "MACHINE_ADD_ERROR"
    
    # 시스템 에러
    INVALID_INPUT = "INVALID_INPUT"
    DATABASE_ERROR = "DATABASE_ERROR"
    MODBUS_CONNECTION_ERROR = "MODBUS_CONNECTION_ERROR"

class CustomException(Exception):
    def __init__(
        self, 
        error_code: ErrorCode = ErrorCode.UNKNOWN_ERROR,
        message: str = "알 수 없는 오류가 발생했습니다.",
        status_code: int = 500,
        details: dict = {}
    ):
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(self.message)

class HTTPCustomException(HTTPException):
    def __init__(self, status_code: int, detail: str, error_code: str):
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = error_code