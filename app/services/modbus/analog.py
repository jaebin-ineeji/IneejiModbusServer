# app/services/modbus/analog.py
from typing import Dict
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

    async def read_all_values(self) -> Dict[int, int]:
        """모든 아날로그 값 읽기"""
        register_map = {}
        register_ranges = [
            (1220, 6),  # 1220-1225
            (2000, 11),  # 2000-2010
            (2100, 21),  # 2100-2120
            (2300, 11),  # 2300-2310
            (2330, 6),  # 2330-2335
            (2500, 11),  # 2500-2510
            (2701, 5),  # 2701-2705
            (2901, 2),  # 2901-2902
            (1200, 11),  # 1200-1210
        ]

        with self.client_manager.connect() as client:
            for start_addr, count in register_ranges:
                response = client.read_holding_registers(
                    start_addr, count=count, slave=self.client_manager.slave
                )
                if response.isError():
                    raise ModbusReadError(
                        f"레지스터 범위 {start_addr}-{start_addr+count-1} 읽기 실패"
                    )

                for i, value in enumerate(response.registers):
                    register_map[start_addr + i] = value

        return register_map
