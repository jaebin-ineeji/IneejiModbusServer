# main.py
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from app.api.middleware import (
    global_exception_handler,
    log_middleware,
    validation_exception_handler,
)
from app.api.routes.direct.analog import router as analog_router
from app.api.routes.direct.digital import router as digital_router
from app.api.routes.health import router as health_router
from app.api.routes.machine import router as machine_router

from contextlib import asynccontextmanager
from app.services.modbus.client import ModbusClientManager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 시작할 때 실행할 코드
    print("서버가 시작됩니다...")
    yield
    # 종료할 때 실행할 코드
    ModbusClientManager.close_all()
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


# 미들웨어 추가
app.middleware("http")(log_middleware)
# 에러 핸들러 추가
app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(ValidationError, validation_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)


# 라우터 포함
app.include_router(health_router)
app.include_router(machine_router)
app.include_router(analog_router)
app.include_router(digital_router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main1:app", host="0.0.0.0", port=4444)
