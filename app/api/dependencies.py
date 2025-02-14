# app/api/dependencies.py
from fastapi import Query
from app.services.modbus.client import ModbusClientManager, DatabaseClientManager
from app.core.config import settings
from app.services.modbus.machine import MachineService

# 데이터베이스 인스턴스 생성
db = DatabaseClientManager(settings.DATABASE_NAME)


def get_database_client():
    return db


async def get_modbus_client_by_ip(
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


async def get_modbus_client_by_machine_name(
    machine_name: str,
) -> ModbusClientManager:
    machine_service = MachineService(db)
    machine_config = machine_service.get_machine_config(machine_name)
    return ModbusClientManager(
        host=machine_config.ip, port=machine_config.port, slave=machine_config.slave
    )
