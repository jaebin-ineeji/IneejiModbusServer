# app/api/routes/analog.py
from fastapi import APIRouter, Depends, Path, Query
from app.api.dependencies import get_modbus_client
from app.models.schemas import ApiResponse
from app.services.modbus.client import ModbusClientManager
from app.services.modbus.analog import AnalogService

router = APIRouter(prefix="/analog", tags=["analog"])


@router.get("/{register}")
async def read_analog(
    register: int = Path(..., ge=0, le=65535),
    client: ModbusClientManager = Depends(get_modbus_client),
):
    service = AnalogService(client)
    value = await service.read_value(register)
    return ApiResponse(success=True, message="아날로그 값 읽기 성공", data=value)


@router.post("/{register}")
async def write_analog(
    register: int = Path(..., ge=0, le=65535),
    value: int = Query(..., ge=0, le=65535),
    client: ModbusClientManager = Depends(get_modbus_client),
):
    service = AnalogService(client)
    result = await service.write_value(register, value)
    return ApiResponse(success=True, message="아날로그 값 쓰기 성공", data=result)


@router.get("/all")
async def read_all_analog(
    client: ModbusClientManager = Depends(get_modbus_client),
):
    service = AnalogService(client)
    result = await service.read_all_values()
    return ApiResponse(success=True, message="모든 아날로그 값 읽기 성공", data=result)
