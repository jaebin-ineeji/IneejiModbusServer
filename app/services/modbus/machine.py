from typing import Dict, Optional
from fastapi import HTTPException
from app.models.schemas import TagType, MachineConfig, Mode, Permission, TagConfig
from app.models.validator import validate_tag_config
from app.services.modbus.client import DatabaseClientManager, ModbusClientManager
from app.core.config import settings
from app.services.modbus.analog import AnalogService
from app.services.modbus.digital import DigitalService


class MachineService:
    def __init__(self, db: DatabaseClientManager):
        self.client_manager: Optional[ModbusClientManager] = None
        self.db = db

    def get_all_machine_names(self) -> list[str]:
        return list(settings.MODBUS_MACHINES.keys())

    def get_all_machines(self) -> list[MachineConfig]:
        return list(settings.MODBUS_MACHINES.values())

    def get_machine_config(self, machine_name: str) -> MachineConfig:
        machine_name = machine_name.upper()
        return settings.MODBUS_MACHINES[machine_name]

    def get_machine_tags(self, machine_name: str) -> Dict[str, TagConfig]:
        """특정 기계의 모든 태그 반환"""
        machine_name = machine_name.upper()
        return settings.MODBUS_MACHINES[machine_name].tags

    def get_machine_tag_by_name(self, machine_name: str, tag_name: str) -> TagConfig:
        machine_name = machine_name.upper()
        tag_name = tag_name.upper()
        return settings.MODBUS_MACHINES[machine_name].tags[tag_name]

    async def get_machine_tag_value(
        self, machine_name: str, tag_name: str
    ) -> str | int | Mode:
        if self.client_manager is not None:
            tag_config = self.get_machine_tag_by_name(machine_name, tag_name)
            if tag_config.tag_type == TagType.ANALOG:
                register = int(tag_config.real_register)
                result = await AnalogService(self.client_manager).read_value(register)
                return result
            elif (
                tag_config.tag_type == TagType.DIGITAL
                or tag_config.tag_type == TagType.DIGITAL_AM
                or tag_config.tag_type == TagType.DIGITAL_RM
            ):
                register, bit = tag_config.real_register.split(".")
                if tag_config.tag_type == TagType.DIGITAL_AM:
                    result = await DigitalService(self.client_manager).read_bit(
                        int(register), int(bit), 0
                    )
                elif tag_config.tag_type == TagType.DIGITAL_RM:
                    result = await DigitalService(self.client_manager).read_bit(
                        int(register), int(bit), 1
                    )
                return result
            else:
                raise HTTPException(status_code=500, detail="Invalid tag data type")
        else:
            raise HTTPException(
                status_code=500, detail="Client manager is not initialized"
            )

    def add_machine_tag(self, machine_name: str, tag_name: str, tag_config: TagConfig):
        try:
            tag_name = tag_name.upper()
            # 태그 설정 검증
            validated_config = validate_tag_config(tag_config)

            # 기계 ID 조회
            machine_id = self._get_machine_id(machine_name)

            # 태그 중복 검사
            existing_tag = self.db.execute_query(
                "SELECT COUNT(*) as count FROM tags WHERE machine_id = ? AND tag_name = ?",
                (machine_id, tag_name),
            )

            if existing_tag[0]["count"] > 0:
                raise HTTPException(
                    status_code=409, detail=f"태그 '{tag_name}'가 이미 존재합니다."
                )

            # 태그 추가 실행
            self._add_tag_to_machine(machine_name, tag_name, validated_config)

            self.db.load_modbus_config()
            return {"message": f"태그 {tag_name}가 {machine_name}에 추가되었습니다."}

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"태그 추가 중 오류가 발생했습니다: {str(e)}"
            )

    def update_machine_tag(
        self, machine_name: str, tag_name: str, tag_config: TagConfig
    ):
        """태그 설정을 업데이트하는 메소드"""
        try:
            tag_name = tag_name.upper()
            # 태그 설정 검증
            validated_config = validate_tag_config(tag_config)

            # 기계 ID 조회
            machine_id = self._get_machine_id(machine_name)

            # 태그 존재 여부 확인
            tag_exists = self.db.execute_query(
                "SELECT COUNT(*) as count FROM tags WHERE machine_id = ? AND tag_name = ?",
                (machine_id, tag_name),
            )

            if tag_exists[0]["count"] == 0:
                raise HTTPException(
                    status_code=404, detail=f"태그 '{tag_name}'를 찾을 수 없습니다."
                )

            # 태그 업데이트
            self.db.execute_query(
                """
                UPDATE tags 
                SET tag_type = ?, logical_register = ?, real_register = ?, 
                    permission = ?
                WHERE machine_id = ? AND tag_name = ?
                """,
                (
                    validated_config.tag_type,
                    validated_config.logical_register,
                    validated_config.real_register,
                    validated_config.permission,
                    machine_id,
                    tag_name,
                ),
            )

            self.db.load_modbus_config()
            return {"message": f"태그 {tag_name}가 업데이트되었습니다."}

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"태그 업데이트 중 오류가 발생했습니다: {str(e)}",
            )

    def delete_machine_tag(self, machine_name: str, tag_name: str):
        """태그를 삭제하는 메소드"""
        tag_name = tag_name.upper()
        machine_id = self._get_machine_id(machine_name)
        # 태그 존재 여부 확인
        tag_exists = self.db.execute_query(
            "SELECT COUNT(*) as count FROM tags WHERE machine_id = ? AND tag_name = ?",
            (machine_id, tag_name),
        )

        if tag_exists[0]["count"] == 0:
            raise HTTPException(
                status_code=404, detail=f"태그 '{tag_name}'를 찾을 수 없습니다."
            )

        # 태그 삭제
        self.db.execute_query(
            "DELETE FROM tags WHERE machine_id = ? AND tag_name = ?",
            (machine_id, tag_name),
        )

        self.db.load_modbus_config()

    def _get_machine_id(self, machine_name: str) -> int:
        """기계 ID를 조회하는 내부 메소드"""
        machine_name = machine_name.upper()
        machine_result = self.db.execute_query(
            "SELECT id FROM machines WHERE name = ?", (machine_name,)
        )

        if not machine_result:
            raise HTTPException(status_code=404, detail="기계를 찾을 수 없습니다.")

        return machine_result[0]["id"]

    def _add_tag_to_machine(
        self, machine_name: str, tag_name: str, tag_config: TagConfig
    ):
        """태그를 기계에 추가하는 내부 메소드"""
        machine_id = self._get_machine_id(machine_name)

        self.db.execute_query(
            """
            INSERT INTO tags 
            (machine_id, tag_name, tag_type, logical_register, real_register, permission)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                machine_id,
                tag_name,
                tag_config.tag_type,
                tag_config.logical_register,
                tag_config.real_register,
                tag_config.permission,
            ),
        )
