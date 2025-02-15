import os
import json
from datetime import datetime
from typing import Dict
from app.models.schemas import MachineConfigFormat, TagConfig, TagType, Permission
from app.services.modbus.client import DatabaseClientManager


class ConfigService:
    def __init__(self, db: DatabaseClientManager):
        self.db = db

    async def import_config(self, config: Dict[str, MachineConfigFormat]):
        """설정 일괄 등록"""
        for machine_name, machine_config in config.items():
            # 1. 기계 등록/업데이트
            self.db.execute_query(
                """INSERT INTO machines (name, ip_address, port, slave) 
                    VALUES (?, ?, ?, ?) 
                    ON CONFLICT(name) DO UPDATE SET 
                    ip_address = ?, port = ?, slave = ?""",
                (
                    machine_name,
                    machine_config.ip,
                    machine_config.port,
                    machine_config.slave,
                    machine_config.ip,
                    machine_config.port,
                    machine_config.slave,
                ),
            )

            # 2. 기존 태그 삭제
            machine_id = self._get_machine_id(machine_name)
            self.db.execute_query(
                "DELETE FROM tags WHERE machine_id = ?",
                (machine_id,),
            )

            # 3. 새로운 태그 등록
            for tag_name, tag_config in machine_config.tags.items():
                tag_config_obj = TagConfig(
                    tag_type=TagType(tag_config.tag_type),
                    logical_register=tag_config.logical_register,
                    real_register=tag_config.real_register,
                    permission=Permission(tag_config.permission),
                )
                self._add_tag(machine_name, tag_name, tag_config_obj)

        # 4. 설정 리로드
        self.db.load_modbus_config()

    async def export_config(self) -> Dict:
        """설정 추출 및 저장"""
        machines = self.db.execute_query(
            "SELECT name, ip_address, port, slave FROM machines"
        )

        config = {}
        for machine in machines:
            machine_name = machine["name"]
            tags = self.db.execute_query(
                """
                SELECT tag_name, tag_type, logical_register, real_register, permission 
                FROM tags 
                WHERE machine_id = (SELECT id FROM machines WHERE name = ?)
                """,
                (machine_name,),
            )

            tags_dict = {
                tag["tag_name"]: {
                    "tag_type": tag["tag_type"],
                    "logical_register": tag["logical_register"],
                    "real_register": tag["real_register"],
                    "permission": tag["permission"],
                }
                for tag in tags
            }

            config[machine_name] = {
                "ip": machine["ip_address"],
                "port": machine["port"],
                "slave": machine["slave"],
                "tags": tags_dict,
            }

        # 설정 파일 저장
        config_dir = "logs/config"
        os.makedirs(config_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"machine_config_{timestamp}.json"
        file_path = os.path.join(config_dir, filename)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

        return {"config": config, "saved_path": file_path}

    def _get_machine_id(self, machine_name: str) -> int:
        """기계 ID 조회"""
        machine_result = self.db.execute_query(
            "SELECT id FROM machines WHERE name = ?", (machine_name,)
        )
        if not machine_result:
            raise ValueError(f"기계 '{machine_name}'를 찾을 수 없습니다.")
        return machine_result[0]["id"]

    def _add_tag(self, machine_name: str, tag_name: str, tag_config: TagConfig):
        """태그 추가"""
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
