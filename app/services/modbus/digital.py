from app.services.exceptions import ModbusReadError, ModbusWriteError
from app.services.modbus.client import ModbusClientManager


class DigitalService:
    def __init__(self, client_manager: ModbusClientManager):
        self.client_manager = client_manager

    async def read_bit(self, register: int, bit: int, type: int = 1) -> str:
        with self.client_manager.connect() as client:
            result = client.read_holding_registers(
                register, count=1, slave=self.client_manager.slave
            )
            if result.isError():
                raise ModbusReadError(f"디지털 레지스터 {register}의 값 읽기 실패")

            register_value = result.registers[0]
            digital_value = (register_value >> bit) & 1  # 특정 비트 값 추출
            return _get_digital_status_message(digital_value, type)

    async def write_bit(
        self, register: int, bit: int, state: bool, type: int = 1
    ) -> str:
        with self.client_manager.connect() as client:
            response = client.read_holding_registers(
                register, count=1, slave=self.client_manager.slave
            )
            register_value = response.registers[0]  # 16비트 전체 값

            if state:
                modified_value = register_value | (1 << bit)  # 특정 비트 설정
            else:
                modified_value = register_value & ~(1 << bit)  # 특정 비트 클리어

            # 레지스터 값 쓰기
            result = client.write_register(
                register, modified_value, slave=self.client_manager.slave
            )
            if result.isError():
                raise ModbusWriteError(f"디지털 레지스터 {register}.{bit} 값 쓰기 실패")
            return _get_digital_status_message(modified_value, type, bit_position=bit)


def _get_digital_status_message(
    result: int, type: int, *, bit_position: int = 0
) -> str:
    if type == 0:
        return "AUTO" if (result >> bit_position & 1) == 0 else "MANUAL"
    else:
        return "LOCAL" if (result >> bit_position & 1) == 0 else "REMOTE"
