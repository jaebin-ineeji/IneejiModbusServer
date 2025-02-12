# app/services/modbus/analog.py
from app.services.exceptions import ModbusReadError, ModbusWriteError
from app.services.modbus.client import ModbusClientManager


class AnalogService:
    def __init__(self, client_manager: ModbusClientManager):
        self.client_manager = client_manager

    async def read_value(self, register: int) -> int:
        with self.client_manager.connect() as client:
            result = client.read_holding_registers(
                register, count=1, slave=self.client_manager.slave
            )
            if result.isError():
                raise ModbusReadError(f"아날로그 레지스터 {register}의 값 읽기 실패")
            return result.registers[0]

    async def write_value(self, register: int, value: int) -> int:
        with self.client_manager.connect() as client:
            result = client.write_register(
                register, value, slave=self.client_manager.slave
            )
            if result.isError():
                raise ModbusWriteError(f"아날로그 레지스터 {register}의 값 쓰기 실패")
            return result.registers[0]
