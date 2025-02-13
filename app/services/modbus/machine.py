from fastapi import HTTPException
from app.models.schemas import DataType, MachineConfig, Permission, TagConfig
from app.models.validator import validate_tag_config
from app.services.modbus.client import DatabaseClientManager, ModbusClientManager
from app.core.config import settings


class MachineService:
    def __init__(self, db: DatabaseClientManager):
        # self.client_manager = client_manager
        self.db = db

    def get_all_machine_names(self) -> list[str]:
        return list(settings.MODBUS_MACHINES.keys())

    def get_all_machines(self) -> list[MachineConfig]:
        return list(settings.MODBUS_MACHINES.values())

    def get_machine_ip(self, machine_name: str) -> str:
        return settings.MODBUS_MACHINES[machine_name].ip

    def get_machine_tags(self, machine_name: str) -> list[TagConfig]:
        return list(settings.MODBUS_MACHINES[machine_name].tags.values())

    def get_machine_tag_by_name(self, machine_name: str, tag_name: str) -> TagConfig:
        return settings.MODBUS_MACHINES[machine_name].tags[tag_name]

    def add_machine_tag(self, machine_name: str, tag_name: str, tag_config: TagConfig):
        try:
            tag_name = tag_name.upper()
            # 태그 설정 검증
            validated_config = validate_tag_config(tag_config)

            # 기계 ID 조회
            machine_id = self._get_machine_id(machine_name)

            # 태그 중복 검사
            existing_tag = self.db.execute_query(
                "SELECT COUNT(*) as count FROM tags WHERE machine_id = ? AND logical_name = ?",
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
                "SELECT COUNT(*) as count FROM tags WHERE machine_id = ? AND logical_name = ?",
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
                SET data_type = ?, logical_register = ?, real_register = ?, 
                    permission = ?, slave = ?
                WHERE machine_id = ? AND logical_name = ?
                """,
                (
                    validated_config.data_type,
                    validated_config.logical_register,
                    validated_config.real_register,
                    validated_config.permission,
                    validated_config.slave,
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
            "SELECT COUNT(*) as count FROM tags WHERE machine_id = ? AND logical_name = ?",
            (machine_id, tag_name),
        )

        if tag_exists[0]["count"] == 0:
            raise HTTPException(
                status_code=404, detail=f"태그 '{tag_name}'를 찾을 수 없습니다."
            )

        # 태그 삭제
        self.db.execute_query(
            "DELETE FROM tags WHERE machine_id = ? AND logical_name = ?",
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
            (machine_id, logical_name, data_type, logical_register, real_register, permission, slave)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                machine_id,
                tag_name,
                tag_config.data_type,
                tag_config.logical_register,
                tag_config.real_register,
                tag_config.permission,
                tag_config.slave,
            ),
        )
