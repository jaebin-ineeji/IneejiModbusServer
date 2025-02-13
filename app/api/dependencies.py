# app/api/dependencies.py
from fastapi import Query
from app.services.modbus.client import ModbusClientManager
from app.core.config import settings

async def get_modbus_client(
    host: str = Query(
        ...,
        description="원격 호스트 주소 (예: 172.30.1.97)",
        pattern=r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$",
        examples=["172.30.1.97"],
    ),
    port: int = Query(
        default=settings.MODBUS_DEFAULT_PORT,
        description="통신 포트 번호",
        ge=1,
        le=65535,
        examples=[settings.MODBUS_DEFAULT_PORT],
    ),
    slave: int = Query(
        default=settings.MODBUS_SLAVE,
        description="장비의 슬레이브 주소 (Unit ID)",
        ge=0,
    ),
) -> ModbusClientManager:
    return ModbusClientManager(host=host, port=port, slave=slave)
