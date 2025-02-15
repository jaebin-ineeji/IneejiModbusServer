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
        """모든 기계 이름을 반환하는 메소드"""
        return list(settings.MODBUS_MACHINES.keys())

    def get_all_machines(self) -> list[MachineConfig]:
        """모든 기계 설정을 반환하는 메소드"""
        return list(settings.MODBUS_MACHINES.values())

    def get_machine_config(self, machine_name: str) -> MachineConfig:
        """기계 설정을 반환하는 메소드"""
        try:
            machine_name = machine_name.upper()
            return settings.MODBUS_MACHINES[machine_name]
        except KeyError:
            raise HTTPException(
                status_code=404, detail=f"기계 '{machine_name}'를 찾을 수 없습니다."
            )

    def get_machine_tags(self, machine_name: str) -> Dict[str, TagConfig]:
        """특정 기계의 모든 태그 반환"""
        try:
            machine_name = machine_name.upper()
            return settings.MODBUS_MACHINES[machine_name].tags
        except KeyError:
            raise HTTPException(
                status_code=404, detail=f"기계 '{machine_name}'를 찾을 수 없습니다."
            )

    def get_machine_tag_by_name(self, machine_name: str, tag_name: str) -> TagConfig:
        """기계의 특정 태그 설정을 반환하는 메소드"""
        try:
            machine_name = machine_name.upper()
            tag_name = tag_name.upper()
            return settings.MODBUS_MACHINES[machine_name].tags[tag_name]
        except KeyError:
            raise HTTPException(
                status_code=404, detail=f"태그 '{tag_name}'를 찾을 수 없습니다."
            )

    async def read_machine_tag_value(
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

    async def write_machine_tag_value(
        self, machine_name: str, tag_name: str, tag_value: str
    ):
        tag_config = self.get_machine_tag_by_name(machine_name, tag_name)
        if self.client_manager is not None:
            if tag_config.tag_type == TagType.ANALOG:
                if tag_config.permission == Permission.READ_WRITE and tag_value != "*":
                    result = await AnalogService(self.client_manager).write_value(
                        int(tag_config.real_register), int(tag_value)
                    )
                    return {
                        "message": f"태그 {tag_name}의 값이 {result}로 변경되었습니다."
                    }
                elif (
                    tag_config.permission == Permission.READ_WRITE and tag_value == "*"
                ):
                    raise HTTPException(
                        status_code=403, detail="태그 값을 입력해주세요."
                    )
                else:
                    raise HTTPException(status_code=403, detail="읽기 전용 태그입니다.")
            elif tag_config.tag_type == TagType.DIGITAL_AM:
                register, bit = tag_config.real_register.split(".")
                tag_value = tag_value.upper()
                if tag_config.permission == Permission.READ_WRITE and tag_value != "*":
                    if tag_value == Mode.AUTO:
                        mode = False
                    elif tag_value == Mode.MANUAL:
                        mode = True
                    else:
                        raise HTTPException(
                            status_code=403,
                            detail="모드 값을 확인해주세요. (AUTO, MANUAL)",
                        )
                    result = await DigitalService(self.client_manager).write_bit(
                        register=int(register), bit=int(bit), state=mode, type=0
                    )
                    return {
                        "message": f"태그 {tag_name}의 모드가 {result}로 변경되었습니다."
                    }
                elif (
                    tag_config.permission == Permission.READ_WRITE and tag_value == "*"
                ):
                    service = DigitalService(self.client_manager)
                    response = await service.read_bit(
                        register=int(register), bit=int(bit), type=0
                    )
                    # 모드를 토글 (반대로 변경)
                    mode = True if response == Mode.AUTO else False
                    result = await service.write_bit(
                        register=int(register), bit=int(bit), state=mode, type=0
                    )
                    return {
                        "message": f"태그 {tag_name}의 모드가 {result}로 변경되었습니다."
                    }
                else:
                    raise HTTPException(status_code=403, detail="읽기 전용 태그입니다.")
            elif tag_config.tag_type == TagType.DIGITAL_RM:
                register, bit = tag_config.real_register.split(".")
                tag_value = tag_value.upper()
                if tag_config.permission == Permission.READ_WRITE and tag_value != "*":
                    if tag_value == Mode.LOCAL:
                        mode = False
                    elif tag_value == Mode.REMOTE:
                        mode = True
                    else:
                        raise HTTPException(
                            status_code=403,
                            detail="모드 값을 확인해주세요. (LOCAL, REMOTE)",
                        )
                    result = await DigitalService(self.client_manager).write_bit(
                        register=int(register), bit=int(bit), state=mode, type=1
                    )
                    return {
                        "message": f"태그 {tag_name}의 모드가 {result}로 변경되었습니다."
                    }
                elif (
                    tag_config.permission == Permission.READ_WRITE and tag_value == "*"
                ):
                    service = DigitalService(self.client_manager)
                    response = await service.read_bit(
                        register=int(register), bit=int(bit), type=1
                    )
                    # 모드를 토글 (반대로 변경)
                    mode = True if response == Mode.LOCAL else False
                    result = await service.write_bit(
                        register=int(register), bit=int(bit), state=mode, type=1
                    )
                    return {
                        "message": f"태그 {tag_name}의 모드가 {result}로 변경되었습니다."
                    }
                else:
                    raise HTTPException(status_code=403, detail="읽기 전용 태그입니다.")
        else:
            raise HTTPException(
                status_code=500, detail="Client manager is not initialized"
            )

    def add_machine_tag(self, machine_name: str, tag_name: str, tag_config: TagConfig):
        try:
            # 태그 설정 검증
            validated_config = validate_tag_config(tag_config)

            # 태그 중복 검사
            if self._check_tag_exists(machine_name, tag_name):
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
            # 태그 설정 검증
            validated_config = validate_tag_config(tag_config)

            # 태그 존재 여부 확인
            if not self._check_tag_exists(machine_name, tag_name):
                raise HTTPException(
                    status_code=404, detail=f"태그 '{tag_name}'를 찾을 수 없습니다."
                )

            # 태그 업데이트
            self.db.execute_query(
                """
                UPDATE tags 
                SET tag_type = ?, logical_register = ?, real_register = ?, 
                    permission = ?
                WHERE machine_name = ? AND tag_name = ?
                """,
                (
                    validated_config.tag_type,
                    validated_config.logical_register,
                    validated_config.real_register,
                    validated_config.permission,
                    machine_name,
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

        # 태그 존재 여부 확인
        if not self._check_tag_exists(machine_name, tag_name):
            raise HTTPException(
                status_code=404, detail=f"태그 '{tag_name}'를 찾을 수 없습니다."
            )

        # 태그 삭제
        self.db.execute_query(
            "DELETE FROM tags WHERE machine_id = ? AND tag_name = ?",
            (machine_name, tag_name),
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
        tag_name = tag_name.upper()
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

    def _check_tag_exists(self, machine_name: str, tag_name: str) -> bool:
        """태그 존재 여부를 확인하는 내부 메소드

        Returns:
            bool: 태그가 존재하면 True, 존재하지 않으면 False
        """
        tag_name = tag_name.upper()
        machine_id = self._get_machine_id(machine_name)
        tag_exists = self.db.execute_query(
            "SELECT COUNT(*) as count FROM tags WHERE machine_id = ? AND tag_name = ?",
            (machine_id, tag_name),
        )
        return tag_exists[0]["count"] > 0
