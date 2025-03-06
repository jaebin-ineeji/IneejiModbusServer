# main.py
from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.api.middleware import log_middleware
from app.api.routes.direct.analog import router as analog_router
from app.api.routes.direct.digital import router as digital_router
from app.api.routes.health import router as health_router
from app.api.routes.machine import router as machine_router
from app.api.routes.config import router as config_router
from app.api.routes.autocontrol import router as autocontrol_router
from app.api.exceptions import (
    http_exception_handler,
    validation_exception_handler,
    custom_exception_handler,
    general_exception_handler,
)

from contextlib import asynccontextmanager
from app.services.exceptions import CustomException
from app.services.modbus.client import ModbusClientManager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 시작할 때 실행할 코드
    print("서버가 시작됩니다...")
    yield
    ModbusClientManager.close_all()
    # 종료할 때 실행할 코드
    print("서버가 종료됩니다...")


app = FastAPI(lifespan=lifespan)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 전역 예외 핸들러 등록
@app.exception_handler(Exception)
async def app_general_exception_handler(request: Request, exc: Exception):
    return await general_exception_handler(request, exc)


@app.exception_handler(HTTPException)
async def app_http_exception_handler(request: Request, exc: HTTPException):
    return await http_exception_handler(request, exc)


@app.exception_handler(RequestValidationError)
async def app_validation_exception_handler(
    request: Request, exc: RequestValidationError
):
    return await validation_exception_handler(request, exc)


@app.exception_handler(CustomException)
async def app_custom_exception_handler(request: Request, exc: CustomException):
    return await custom_exception_handler(request, exc)


# 미들웨어 추가
app.middleware("http")(log_middleware)

# 라우터 포함
app.include_router(health_router)
app.include_router(machine_router)
app.include_router(config_router)
app.include_router(analog_router)
app.include_router(digital_router)
app.include_router(autocontrol_router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=4444)
