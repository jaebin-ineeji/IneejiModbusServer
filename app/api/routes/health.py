from fastapi import APIRouter, Depends
from app.api.dependencies import get_modbus_client
from app.models.schemas import ApiResponse
from app.services.modbus.client import ModbusClientManager

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health_check():
    return ApiResponse(success=True, message="서비스가 정상 동작중입니다.")


@router.get("/test-connection")
async def test_connection(
    client: ModbusClientManager = Depends(get_modbus_client),
):
    return await client.test_connection()
