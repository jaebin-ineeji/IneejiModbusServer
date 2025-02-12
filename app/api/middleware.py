# app/api/middleware.py
import json
import time

from fastapi import Request, Response
from fastapi.responses import JSONResponse

from app.core.logging_config import setup_logger

logger = setup_logger()


async def log_middleware(request: Request, call_next):
    # 요청 시작 시간
    start_time = time.time()

    # 요청 바디 읽기
    body = await request.body()
    body_str = body.decode() if body else ""

    # 쿼리 파라미터 수집
    query_params = dict(request.query_params)

    # 요청 정보 로깅
    request_log = {
        "method": request.method,
        "path": request.url.path,
        "query_params": query_params,
        "client_ip": request.client.host if request.client else "unknown",
        "body": body_str,
    }
    logger.info(f"Request: {json.dumps(request_log, ensure_ascii=False)}")

    # 응답 처리
    response = await call_next(request)

    # 응답 바디 읽기
    response_body = b""
    async for chunk in response.body_iterator:
        response_body += chunk

    # 응답 시간 계산
    process_time = time.time() - start_time

    # 응답 정보 로깅
    response_log = {
        "status_code": response.status_code,
        "process_time": f"{process_time:.3f}s",
        "response_body": response_body.decode(),
    }
    logger.info(f"Response: {json.dumps(response_log, ensure_ascii=False)}")

    return Response(
        content=response_body,
        status_code=response.status_code,
        headers=dict(response.headers),
        media_type=response.media_type,
    )


# 에러 핸들러 추가
async def global_exception_handler(request: Request, exc: Exception):
    error_log = {
        "path": request.url.path,
        "method": request.method,
        "error_type": type(exc).__name__,
        "error_message": str(exc),
    }
    logger.error(f"Error: {json.dumps(error_log, ensure_ascii=False)}")

    return JSONResponse(status_code=500, content={"message": "Internal server error"})


async def validation_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "message": "입력값 검증 오류",
            "error_type": type(exc).__name__,
            "error_message": str(exc),
        },
    )
