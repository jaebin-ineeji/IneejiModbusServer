from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from schemas import ApiResponse
from utils import (
    get_analog_value,
    get_digital_status_bit,
    set_digital_status_bit,
    test_connection,
    get_all_analog_values,
)
from middleware import log_middleware, global_exception_handler

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 origin 허용
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메소드 허용
    allow_headers=["*"],  # 모든 HTTP 헤더 허용
)
# 미들웨어 추가
app.middleware("http")(log_middleware)
# 에러 핸들러 추가
app.add_exception_handler(Exception, global_exception_handler)


@app.get(
    "/",
    summary="API 서버 상태 확인",
    description="API 서버가 정상적으로 동작하는지 확인하는 헬스체크 엔드포인트입니다.",
    response_description="서버가 정상 동작 중임을 알리는 메시지를 반환합니다.",
)
async def root():
    return {"message": "Hello World"}


@app.get(
    "/test_connection",
    summary="테스트 연결 확인",
    description="테스트 연결 확인",
)
async def test_connect(
    host: str = Query(
        ...,
        description="원격 호스트 주소 (예: 172.30.1.97)",
        pattern=r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$",
        examples=["172.30.1.97"],
    ),
    port: int = Query(
        ..., description="통신 포트 번호", ge=1, le=65535, examples=[502]
    ),
):
    result = test_connection(host, port)
    return ApiResponse(
        success=True,
        message=result["message"],
    )


@app.get(
    "/get_all_analog",
    summary="모든 아날로그 값 조회",
    description="모든 아날로그 값 조회",
)
async def get_all_analog(
    host: str = Query(
        ...,
        description="원격 호스트 주소 (예: 172.30.1.97)",
        pattern=r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$",
        examples=["172.30.1.97"],
    ),
    port: int = Query(
        ..., description="통신 포트 번호", ge=1, le=65535, examples=[502]
    ),
):
    result = get_all_analog_values(host, port)
    return ApiResponse(
        success=True,
        message="모든 아날로그 값 조회",
        data=result,
    )


@app.post(
    "/set_digital",
    summary="디지털 신호 설정",
    description="""디지털 신호의 상태를 설정합니다.
    
    - AUTO/MANUAL 또는 LOCAL/REMOTE 모드를 변경할 수 있습니다.
    - 지정된 레지스터의 특정 비트 값을 변경합니다.
    
    **사용 예시:**
    - AUTO/MANUAL 모드 변경: type=0
    - LOCAL/REMOTE 모드 변경: type=1
    """,
    response_description="설정된 디지털 신호의 상태를 반환합니다.",
    response_model=ApiResponse,
)
async def set_digital_status(
    host: str = Query(
        ...,
        description="원격 호스트 주소 (예: 172.30.1.97)",
        pattern=r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$",
        examples=["172.30.1.97"],
    ),
    port: int = Query(
        ..., description="통신 포트 번호", ge=1, le=65535, examples=[502]
    ),
    register: int = Query(..., description="레지스터 주소", ge=0, examples=[42008]),
    bit: int = Query(
        ..., description="레지스터 내 비트 위치 (0-15)", ge=0, le=15, examples=[0]
    ),
    slave: int = Query(
        ..., description="장비의 슬레이브 주소 (Unit ID)", ge=0, examples=[1]
    ),
    state: bool = Query(
        ...,
        description="설정할 상태 값 [true(MANUAL or REMOTE)/false(AUTO or LOCAL)]",
        examples=[False],
    ),
    type: int = Query(
        ...,
        description="제어 타입 (0: AUTO/MANUAL, 1: LOCAL/REMOTE)",
        ge=0,
        le=1,
        examples=[0],
    ),
):
    try:
        result = set_digital_status_bit(
            host=host,
            port=port,
            register_address=register,
            bit_position=bit,
            slave=slave,
            new_state=state,
            type=type,
        )
        return ApiResponse(
            success=True,
            message=f"slave:{slave}, 레지스터:{register}.{bit}의 디지털신호가 {result}로 변경되었습니다.",
            data=result,
        )
    except Exception as e:
        raise Exception(f"Error: {e}")


@app.get(
    "/get_digital",
    summary="디지털 신호 상태 조회",
    description="""현재 디지털 신호의 상태를 조회합니다.
    
    - AUTO/MANUAL 상태 확인
    - LOCAL/REMOTE 상태 확인
    - 지정된 레지스터의 특정 비트 값을 읽어옵니다.
    """,
    response_description="조회된 디지털 신호의 현재 상태를 반환합니다.",
    response_model=ApiResponse,
)
async def get_digital_status(
    host: str = Query(
        ...,
        description="원격 호스트 주소 (예: 172.30.1.97)",
        pattern=r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$",
        examples=["172.30.1.97"],
    ),
    port: int = Query(
        ..., description="통신 포트 번호", ge=1, le=65535, examples=[502]
    ),
    register: int = Query(..., description="레지스터 주소", ge=0, examples=[42008]),
    bit: int = Query(
        ..., description="레지스터 내 비트 위치 (0-15)", ge=0, le=15, examples=[0]
    ),
    slave: int = Query(
        ..., description="장비의 슬레이브 주소 (Unit ID)", ge=0, examples=[1]
    ),
    type: int = Query(
        ...,
        description="조회 타입 (0: AUTO/MANUAL, 1: LOCAL/REMOTE)",
        ge=0,
        le=1,
        examples=[0],
    ),
):
    try:
        result = get_digital_status_bit(
            host=host,
            port=port,
            register_address=register,
            bit_position=bit,
            slave=slave,
            type=type,
        )
        return ApiResponse(
            success=True,
            message=f"slave:{slave}, 레지스터:{register}.{bit}의 디지털신호가 {result}입니다.",
            data=result,
        )
    except Exception as e:
        raise Exception(f"Error: {e}")


@app.get(
    "/get_analog",
    summary="아날로그 값 조회",
    description="""지정된 레지스터의 아날로그 값을 조회합니다.
    
    - 센서 값, 측정 값 등의 아날로그 데이터를 읽어옵니다.
    - 16비트 정수 형태로 값을 반환합니다.
    """,
    response_description="조회된 아날로그 값을 반환합니다.",
    response_model=ApiResponse,
)
async def get_analog_status(
    host: str = Query(
        ...,
        description="원격 호스트 주소 (예: 172.30.1.97)",
        pattern=r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$",
        examples=["172.30.1.97"],
    ),
    port: int = Query(
        ..., description="통신 포트 번호", ge=1, le=65535, examples=[502]
    ),
    register: int = Query(..., description="레지스터 주소", ge=0, examples=[42008]),
    slave: int = Query(
        ..., description="장비의 슬레이브 주소 (Unit ID)", ge=0, examples=[1]
    ),
):
    try:
        result = get_analog_value(
            host=host, port=port, register_address=register, slave=slave
        )
        return ApiResponse(
            success=True,
            message=f"slave:{slave}, 레지스터:{register}의 아날로그 값이 {result}입니다.",
            data=result,
        )
    except Exception as e:
        return ApiResponse(success=False, message=f"Error: {e}")


@app.get(
    "/set_analog",
    summary="아날로그 값 설정",
    description="""지정된 레지스터에 아날로그 값을 설정합니다.
    
    - 설정값, 제어값 등의 아날로그 데이터를 쓰기합니다.
    - 16비트 정수 형태로 값을 전송합니다.
    """,
    response_description="설정된 아날로그 값을 반환합니다.",
    response_model=ApiResponse,
)
async def set_analog_status(
    host: str = Query(
        ...,
        description="원격 호스트 주소 (예: 172.30.1.97)",
        pattern=r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$",
        examples=["172.30.1.97"],
    ),
    port: int = Query(
        ..., description="통신 포트 번호", ge=1, le=65535, examples=[502]
    ),
    register: int = Query(..., description="레지스터 주소", ge=0, examples=[42008]),
    slave: int = Query(
        ..., description="장비의 슬레이브 주소 (Unit ID)", ge=0, examples=[1]
    ),
    value: int = Query(..., description="설정할 아날로그 값", ge=0, examples=[100]),
):
    pass


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=4444, reload=True)
