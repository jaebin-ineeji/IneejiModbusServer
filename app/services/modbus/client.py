# app/services/modbus/client.py
from pymodbus.client import ModbusTcpClient
from contextlib import contextmanager

from app.services.exceptions import ModbusConnectionError


class ModbusClientManager:
    def __init__(self, host: str, port: int, slave: int):
        self.host = host
        self.port = port
        self.slave = slave
        self._client = None

    @contextmanager
    def connect(self):
        try:
            self._client = ModbusTcpClient(host=self.host, port=self.port)
            if not self._client.connect():  # 연결 실패 시
                raise ModbusConnectionError(
                    f"Modbus 서버 연결 실패 - host: {self.host}, port: {self.port}"
                )
            yield self._client
        finally:
            if self._client:
                self._client.close()

    async def test_connection(self):
        try:
            with self.connect():
                return True
        except Exception:
            return False
