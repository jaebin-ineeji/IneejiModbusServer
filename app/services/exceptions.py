# app/services/exceptions.py
class ModbusError(Exception):
    def __init__(self, message: str, error_code: int = 500):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class ModbusConnectionError(ModbusError):
    pass


class ModbusReadError(ModbusError):
    pass


class ModbusWriteError(ModbusError):
    pass
