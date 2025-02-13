from fastapi import APIRouter, Depends, HTTPException
from app.core.config import settings
from app.api.dependencies import get_database_client
from app.services.modbus.client import DatabaseClientManager

router = APIRouter(prefix="/machine", tags=["machine"])


@router.get("")
def get_machines_config():
    """현재 등록된 기계 목록 및 태그 반환"""
    return settings.MODBUS_MACHINES


@router.post("/{machine_name}")
def add_machine(
    machine_name: str,
    ip_address: str,
    db: DatabaseClientManager = Depends(get_database_client),
):
    """새로운 기계를 추가하고 설정을 갱신"""
    machine_name = machine_name.lower()
    print(machine_name)
    db.execute_query(
        "INSERT INTO machines (name, ip_address) VALUES (?, ?) ON CONFLICT(name) DO UPDATE SET ip_address = ?",
        (machine_name, ip_address, ip_address),
    )

    db.load_modbus_config()
    return {"message": f"Machine {machine_name} added/updated"}


@router.delete("/{machine_name}")
def delete_machine(
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
def add_tag(
    machine_name: str,
    tag_name: str,
    tag_data: dict,
    db: DatabaseClientManager = Depends(get_database_client),
):
    """특정 기계에 태그 추가"""
    with db.get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM machines WHERE name = ?", (machine_name,))
        machine = cursor.fetchone()
        if not machine:
            raise HTTPException(status_code=404, detail="Machine not found")

        cursor.execute(
            "INSERT INTO tags (machine_id, logical_name, data_type, logical_register, real_register, permission, slave) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                machine[0],
                tag_name,
                tag_data["data_type"],
                tag_data["logical_register"],
                tag_data["real_register"],
                tag_data["permission"],
                tag_data["slave"],
            ),
        )

    db.load_modbus_config()
    return {"message": f"Tag {tag_name} added to {machine_name}"}


@router.delete("/{machine_name}/tags/{tag_name}")
def delete_tag(
    machine_name: str,
    tag_name: str,
    db: DatabaseClientManager = Depends(get_database_client),
):
    """특정 기계에서 태그 삭제"""
    with db.get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM tags WHERE machine_id = (SELECT id FROM machines WHERE name = ?) AND logical_name = ?",
            (machine_name, tag_name),
        )

    db.load_modbus_config()
    return {"message": f"Tag {tag_name} deleted from {machine_name}"}
