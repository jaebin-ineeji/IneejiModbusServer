from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.dependencies import get_modbus_client_by_ip
from app.models.schemas import ApiResponse
from app.models.validator import DigitalRegisterInput
from app.services.modbus.client import ModbusClientManager
from app.services.modbus.digital import DigitalService

router = APIRouter(prefix="/direct/digital", tags=["Direct digital"])


@router.get("/{register_bit}")
async def read_digital(
    param: DigitalRegisterInput = Depends(),
    type: int = Query(
        default=1,
        description="0: AUTO/MANUAL, 1: LOCAL/REMOTE",
        ge=0,
        le=1,
    ),
    client: ModbusClientManager = Depends(get_modbus_client_by_ip),
):
    """
    디지털 값을 읽는 엔드포인트
    :param param: "1200.1" 형식의 레지스터.비트 위치
    :param type: 0: AUTO/MANUAL, 1: LOCAL/REMOTE
    """
    try:
        register, bit = param.parse_values()
        service = DigitalService(client)
        result = await service.read_bit(register, bit, type)
        return ApiResponse(success=True, message="디지털 값 읽기 성공", data=result)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"디지털 값을 읽는 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/{register_bit}")
async def write_digital(
    param: DigitalRegisterInput = Depends(),
    state: bool = Query(..., description="True: MANUAL/REMOTE, False: AUTO/LOCAL"),
    type: int = Query(
        default=1,
        description="0: AUTO/MANUAL, 1: LOCAL/REMOTE",
        ge=0,
        le=1,
    ),
    client: ModbusClientManager = Depends(get_modbus_client_by_ip),
):
    try:
        register, bit = param.parse_values()
        service = DigitalService(client)
        result = await service.write_bit(register, bit, state, type)
        return ApiResponse(success=True, message="디지털 값 쓰기 성공", data=result)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"디지털 값을 쓰는 중 오류가 발생했습니다: {str(e)}"
        )
