from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi import HTTPException
from app.models.schemas import ApiResponse, ErrorResponse
from app.services.exceptions import CustomException


async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP 예외 처리 핸들러"""
    error_code = getattr(exc, 'error_code', f"HTTP_{exc.status_code}_ERROR")
    return JSONResponse(
        status_code=exc.status_code,
        content=ApiResponse(
            success=False,
            message=exc.detail,
            error=ErrorResponse(
                code=error_code,
                message=exc.detail
            )
        ).model_dump()
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """요청 데이터 검증 예외 처리 핸들러"""
    return JSONResponse(
        status_code=422,
        content=ApiResponse(
            success=False,
            message="입력값 검증 오류",
            error=ErrorResponse(
                code="VALIDATION_ERROR",
                message=str(exc),
                details={"errors": exc.errors()}
            )
        ).model_dump()
    )


async def general_exception_handler(request: Request, exc: Exception):
    """일반 예외 처리 핸들러"""
    return JSONResponse(
        status_code=500,
        content=ApiResponse(
            success=False,
            message="서버 내부 오류",
            error=ErrorResponse(
                code="INTERNAL_SERVER_ERROR",
                message=str(exc)
            )
        ).model_dump()
    ) 

async def custom_exception_handler(request: Request, exc: CustomException):
    return JSONResponse(
        status_code=exc.status_code,
        content=ApiResponse(
            success=False,
            message=exc.message,
            error=ErrorResponse(
                code=exc.error_code.value,
                message=exc.message,
                details=exc.details
            )
        ).model_dump()
    )