from fastapi import APIRouter, Depends, HTTPException
from app.core.config import settings
from app.api.dependencies import get_database_client, get_modbus_client_by_machine_name
from app.models.schemas import TagConfig
from app.services.modbus.client import DatabaseClientManager, ModbusClientManager
from functools import lru_cache

from app.services.modbus.machine import MachineService

router = APIRouter(prefix="/machine", tags=["machine"])


@lru_cache
def get_machine_service(db: DatabaseClientManager = Depends(get_database_client)):
    return MachineService(db)


@router.get("")
async def get_machines_config():
    """현재 등록된 기계 목록 및 태그 반환"""
    return settings.MODBUS_MACHINES


@router.post("/{machine_name}")
async def add_machine(
    machine_name: str,
    ip_address: str,
    port: int,
    slave: int,
    db: DatabaseClientManager = Depends(get_database_client),
):
    """새로운 기계를 추가하고 설정을 갱신"""
    machine_name = machine_name.upper()
    db.execute_query(
        "INSERT INTO machines (name, ip_address, port, slave) VALUES (?, ?, ?, ?) ON CONFLICT(name) DO UPDATE SET ip_address = ?, port = ?, slave = ?",
        (machine_name, ip_address, port, slave, ip_address, port, slave),
    )

    db.load_modbus_config()
    return {"message": f"Machine {machine_name} added/updated"}


@router.delete("/{machine_name}")
async def delete_machine(
    machine_name: str, db: DatabaseClientManager = Depends(get_database_client)
):
    """기계를 삭제하고 설정을 갱신"""
    db.execute_query(
        "DELETE FROM machines WHERE name = ?",
        (machine_name,),
    )

    db.load_modbus_config()
    return {"message": f"Machine {machine_name} deleted"}


@router.post("/{machine_name}/tags")
async def add_tag(
    machine_name: str,
    tag_name: str,
    tag_data: TagConfig,
    # db: DatabaseClientManager = Depends(get_database_client),
    machine_service: MachineService = Depends(get_machine_service),
):
    """특정 기계에 태그 추가 후 설정 갱신"""
    machine_service.add_machine_tag(machine_name, tag_name, tag_data)
    return {"message": f"Tag {tag_name} added to {machine_name}"}


@router.delete("/{machine_name}/tags/{tag_name}")
async def delete_tag(
    machine_name: str,
    tag_name: str,
    machine_service: MachineService = Depends(get_machine_service),
):
    """특정 기계에서 태그 삭제 후 설정 갱신"""
    machine_service.delete_machine_tag(machine_name, tag_name)

    return {"message": f"Tag {tag_name} deleted from {machine_name}"}


@router.get("/{machine_name}/tags")
async def get_tags(
    machine_name: str,
    machine_service: MachineService = Depends(get_machine_service),
):
    """특정 기계의 모든 태그 반환"""
    return machine_service.get_machine_tags(machine_name)


@router.get("/{machine_name}/tags/{tag_name}")
async def get_tag(
    machine_name: str,
    tag_name: str,
    machine_service: MachineService = Depends(get_machine_service),
):
    return machine_service.get_machine_tag_by_name(machine_name, tag_name)


@router.put("/{machine_name}/tags/{tag_name}")
async def update_tag(
    machine_name: str,
    tag_name: str,
    tag_data: TagConfig,
    machine_service: MachineService = Depends(get_machine_service),
):
    machine_service.update_machine_tag(machine_name, tag_name, tag_data)
    return {"message": f"Tag {tag_name} updated for {machine_name}"}


@router.get("/{machine_name}/tags/{tag_name}/value")
async def get_tag_value(
    machine_name: str,
    tag_name: str,
    machine_service: MachineService = Depends(get_machine_service),
    client: ModbusClientManager = Depends(get_modbus_client_by_machine_name),
):
    machine_service.client_manager = client

    tag_value = await machine_service.get_machine_tag_value(machine_name, tag_name)

    return {
        "machine_name": machine_name.upper(),
        "tag_name": tag_name.upper(),
        "value": tag_value,
    }
