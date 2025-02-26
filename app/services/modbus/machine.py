from typing import Dict, Optional, Any
from fastapi import HTTPException
from app.models.schemas import (
    TagType,
    MachineConfig,
    Mode,
    Permission,
    TagConfig,
    ServiceResult,
)
from app.models.validator import validate_tag_config
from app.services.exceptions import CustomException, ErrorCode
from app.services.modbus.client import DatabaseClientManager, ModbusClientManager
from app.core.config import settings
from app.services.modbus.analog import AnalogService
from app.services.modbus.digital import DigitalService


class MachineService:
    def __init__(self, db: DatabaseClientManager):
        self.client_manager: Optional[ModbusClientManager] = None
        self.db = db

    def get_all_machines(self) -> ServiceResult:
        """모든 기계 설정을 반환하는 메소드"""
        return ServiceResult(
            success=True,
            message="기계 목록 조회 성공",
            data=list(settings.MODBUS_MACHINES.keys()),
        )

    def get_machine_config_response(self, machine_name: str) -> ServiceResult:
        """기계 설정을 반환하는 메소드"""
        try:
            machine_name = machine_name.upper()
            return ServiceResult(
                success=True,
                message="기계 설정 조회 성공",
                data=settings.MODBUS_MACHINES[machine_name],
            )
        except KeyError:
            raise CustomException(
                error_code=ErrorCode.MACHINE_NOT_FOUND,
                message=f"기계 '{machine_name}'를 찾을 수 없습니다.",
            )

    def get_machine_config(self, machine_name: str) -> MachineConfig:
        """기계 설정을 반환하는 메소드"""
        try:
            machine_name = machine_name.upper()
            return settings.MODBUS_MACHINES[machine_name]
        except KeyError:
            raise CustomException(
                error_code=ErrorCode.MACHINE_NOT_FOUND,
                message=f"기계 '{machine_name}'를 찾을 수 없습니다.",
            )

    def get_machine_tags(self, machine_name: str) -> Dict[str, TagConfig]:
        """특정 기계의 모든 태그 반환"""

        machine_name = machine_name.upper()
        machine_config = self.get_machine_config(machine_name)
        return machine_config.tags

    def get_machine_tag_by_name(self, machine_name: str, tag_name: str) -> TagConfig:
        """기계의 특정 태그 설정을 반환하는 메소드"""
        try:
            machine_name = machine_name.upper()
            tag_name = tag_name.upper()
            machine_config = self.get_machine_config(machine_name)
            return machine_config.tags[tag_name]
        except KeyError:
            raise CustomException(
                error_code=ErrorCode.TAG_NOT_FOUND,
                status_code=404,
                message=f"{machine_name} 기계의 태그 '{tag_name}'를 찾을 수 없습니다.",
            )

    async def read_machine_tag_value(
        self, machine_name: str, tag_name: str
    ) -> str | int | Mode:
        # Early return으로 클라이언트 매니저 검증
        if self.client_manager is None:
            raise CustomException(
                error_code=ErrorCode.MODBUS_CONNECTION_ERROR,
                message="모드버스 클라이언트가 초기화되지 않았습니다.",
            )

        tag_config = self.get_machine_tag_by_name(machine_name, tag_name)

        # 태그 타입별 처리 함수 매핑
        tag_handlers = {
            TagType.ANALOG: self._read_analog_value,
            TagType.DIGITAL: lambda config: self._read_digital_value(config, 2),
            TagType.DIGITAL_AM: lambda config: self._read_digital_value(config, 0),
            TagType.DIGITAL_RM: lambda config: self._read_digital_value(config, 1),
        }

        handler = tag_handlers.get(tag_config.tag_type)
        if not handler:
            raise CustomException(
                error_code=ErrorCode.INVALID_TAG_TYPE,
                message="태그 타입이 올바르지 않습니다.",
            )

        return await handler(tag_config)

    async def _read_analog_value(self, tag_config: TagConfig) -> int:
        """아날로그 값을 읽는 내부 메소드"""
        assert self.client_manager is not None
        register = int(tag_config.real_register)
        return await AnalogService(self.client_manager).read_value(register)

    async def _read_digital_value(self, tag_config: TagConfig, type_code: int) -> Mode:
        """디지털 값을 읽는 내부 메소드"""
        assert self.client_manager is not None
        register, bit = tag_config.real_register.split(".")
        return await DigitalService(self.client_manager).read_bit(
            int(register), int(bit), type_code
        )

    async def write_machine_tag_value(
        self, machine_name: str, tag_name: str, tag_value: str
    ) -> Optional[ServiceResult]:
        # Early return으로 클라이언트 매니저 검증
        if self.client_manager is None:
            raise CustomException(
                error_code=ErrorCode.MODBUS_CONNECTION_ERROR,
                message="모드버스 클라이언트가 초기화되지 않았습니다.",
            )

        tag_config = self.get_machine_tag_by_name(machine_name, tag_name)

        # 읽기 전용 태그 검증
        if tag_config.permission != Permission.READ_WRITE:
            raise CustomException(
                error_code=ErrorCode.TAG_READ_ONLY,
                status_code=403,
                message="읽기 전용 태그입니다.",
            )

        # 태그 타입별 처리 함수 매핑
        handlers = {
            TagType.ANALOG: self._handle_analog_write,
            TagType.DIGITAL_AM: lambda c, v: self._handle_digital_write(
                c, v, 0, Mode.AUTO, Mode.MANUAL
            ),
            TagType.DIGITAL_RM: lambda c, v: self._handle_digital_write(
                c, v, 1, Mode.LOCAL, Mode.REMOTE
            ),
            TagType.DIGITAL: lambda c, v: self._handle_digital_write(
                c, v, 2, Mode.OFF, Mode.ON
            ),
        }

        handler = handlers.get(tag_config.tag_type)
        if not handler:
            raise CustomException(
                error_code=ErrorCode.INVALID_TAG_TYPE,
                message="지원하지 않는 태그 타입입니다.",
            )

        result = await handler(tag_config, tag_value.upper())
        return ServiceResult(
            success=True,
            message=self._get_success_message(machine_name, tag_name, result),
            data=result,
        )

    async def _handle_analog_write(self, tag_config: TagConfig, tag_value: str) -> int:
        """아날로그 값 쓰기 처리"""
        assert self.client_manager is not None
        if tag_value == "*":
            raise CustomException(
                error_code=ErrorCode.INVALID_TAG_VALUE,
                status_code=403,
                message="태그 값을 입력해주세요.",
            )
        return await AnalogService(self.client_manager).write_value(
            int(tag_config.real_register), int(tag_value)
        )

    async def _handle_digital_write(
        self,
        tag_config: TagConfig,
        tag_value: str,
        type_code: int,
        false_mode: Mode,
        true_mode: Mode,
    ) -> Mode:
        """디지털 값 쓰기 처리"""
        assert self.client_manager is not None
        register, bit = tag_config.real_register.split(".")
        service = DigitalService(self.client_manager)

        if tag_value == "*":
            # 토글 로직
            current_mode = await service.read_bit(
                register=int(register), bit=int(bit), type=type_code
            )
            mode = True if current_mode == false_mode else False
        else:
            # 직접 값 설정
            if tag_value == false_mode:
                mode = False
            elif tag_value == true_mode:
                mode = True
            else:
                raise CustomException(
                    error_code=ErrorCode.CHECK_MODE_VALUE,
                    status_code=403,
                    message=f"모드 값을 확인해주세요. ({false_mode}, {true_mode})",
                )

        return await service.write_bit(
            register=int(register), bit=int(bit), state=mode, type=type_code
        )

    def _get_success_message(
        self, machine_name: str, tag_name: str, result: Any
    ) -> str:
        """성공 메시지 생성"""
        value_type = "값" if isinstance(result, int) else "모드"
        return f"{machine_name.upper()} 기계의 태그 {tag_name.upper()}의 {value_type}이 {result}로 변경되었습니다."

    def add_machine(
        self, machine_name: str, machine_config: MachineConfig
    ) -> ServiceResult:
        try:
            machine_name = machine_name.upper()
            self._validate_machine_exists(machine_name)
            self.db.execute_query(
                "INSERT INTO machines (name, ip_address, port, slave) VALUES (?, ?, ?, ?) ON CONFLICT(name) DO UPDATE SET ip_address = ?, port = ?, slave = ?",
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
            self.db.load_modbus_config()
            return ServiceResult(
                success=True,
                message=f"기계 {machine_name} 추가 완료",
                data={"machine_name": machine_name, "config": machine_config},
            )
        except Exception as e:
            raise CustomException(
                error_code=ErrorCode.MACHINE_ADD_ERROR,
                message=f"기계 추가중 오류가 발생했습니다: {str(e)}",
            )

    def delete_machine(self, machine_name: str) -> ServiceResult:
        machine_name = machine_name.upper()
        machine_id = self._get_machine_id(machine_name)
        self.db.execute_query("DELETE FROM machines WHERE id = ?", (machine_id,))
        self.db.load_modbus_config()
        return ServiceResult(success=True, message=f"기계 {machine_name} 삭제 완료")

    def add_machine_tag(
        self, machine_name: str, tag_name: str, tag_config: TagConfig
    ) -> ServiceResult:
        # 태그 설정 검증
        validated_config = validate_tag_config(tag_config)

        # 태그 중복 검사
        self._validate_tag_not_exists(machine_name, tag_name)

        # 태그 추가 실행
        self._add_tag_to_machine(machine_name, tag_name, validated_config)

        self.db.load_modbus_config()
        return ServiceResult(
            success=True,
            message=f"태그 {tag_name.upper()}가 {machine_name.upper()}에 추가되었습니다.",
            data={
                "machine_name": machine_name.upper(),
                "tag_name": tag_name.upper(),
                "config": validated_config,
            },
        )

    def update_machine_tag(
        self, machine_name: str, tag_name: str, tag_config: TagConfig
    ):
        """태그 설정을 업데이트하는 메소드"""
        # 태그 설정 검증
        validated_config = validate_tag_config(tag_config)

        # 태그 존재 여부 확인
        self._validate_tag_exists(machine_name, tag_name)

        machine_id = self._get_machine_id(machine_name)
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
                tag_name.upper(),
            ),
        )

        self.db.load_modbus_config()
        return ServiceResult(
            success=True,
            message=f"태그 {tag_name.upper()}가 업데이트되었습니다.",
            data=validated_config,
        )

    def delete_machine_tag(self, machine_name: str, tag_name: str):
        """태그를 삭제하는 메소드"""
        tag_name = tag_name.upper()

        # 태그 존재 여부 확인
        self._validate_tag_exists(machine_name, tag_name)

        machine_id = self._get_machine_id(machine_name)

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
            raise CustomException(
                error_code=ErrorCode.MACHINE_NOT_FOUND,
                status_code=404,
                message=f"기계 '{machine_name}'를 찾을 수 없습니다.",
            )

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

    def _validate_tag_not_exists(self, machine_name: str, tag_name: str):
        """태그 중복 검사를 수행하는 내부 메소드

        태그가 이미 존재하면 CustomException을 발생시킵니다.
        """
        machine_name = machine_name.upper()
        tag_name = tag_name.upper()
        machine_id = self._get_machine_id(machine_name)
        tag_exists = self.db.execute_query(
            "SELECT COUNT(*) as count FROM tags WHERE machine_id = ? AND tag_name = ?",
            (machine_id, tag_name),
        )
        if tag_exists[0]["count"] > 0:
            raise CustomException(
                error_code=ErrorCode.TAG_ALREADY_EXISTS,
                status_code=409,
                message=f"기계 '{machine_name}'의 태그 '{tag_name}'가 이미 존재합니다.",
            )

    def _validate_tag_exists(self, machine_name: str, tag_name: str):
        """태그 존재 여부를 확인하는 내부 메소드

        태그가 존재하지 않으면 CustomException을 발생시킵니다.
        """
        machine_name = machine_name.upper()
        tag_name = tag_name.upper()
        machine_id = self._get_machine_id(machine_name)
        tag_exists = self.db.execute_query(
            "SELECT COUNT(*) as count FROM tags WHERE machine_id = ? AND tag_name = ?",
            (machine_id, tag_name),
        )
        if tag_exists[0]["count"] == 0:
            raise CustomException(
                error_code=ErrorCode.TAG_NOT_FOUND,
                status_code=404,
                message=f"기계 '{machine_name}'의 태그 '{tag_name}'를 찾을 수 없습니다.",
            )

    def _validate_machine_exists(self, machine_name: str):
        """기계 존재 여부를 확인하는 내부 메소드

        기계가 존재하면 CustomException을 발생시킵니다.
        """
        machine_name = machine_name.upper()
        machine_exists = self.db.execute_query(
            "SELECT COUNT(*) as count FROM machines WHERE name = ?", (machine_name,)
        )
        if machine_exists[0]["count"] > 0:
            raise CustomException(
                error_code=ErrorCode.MACHINE_ALREADY_EXISTS,
                status_code=409,
                message=f"기계 '{machine_name}'가 이미 존재합니다.",
            )
