# app/core/config.py
from pydantic import Field
from pydantic_settings import SettingsConfigDict, BaseSettings
from typing import Dict
from app.models.schemas import MachineConfig


class Settings(BaseSettings):
    DATABASE_NAME: str = Field(default="modbus_config.db")
    MODBUS_DEFAULT_PORT: int = Field(default=502)
    MODBUS_TIMEOUT: int = Field(default=3)
    MODBUS_RETRY_COUNT: int = Field(default=3)
    MODBUS_SLAVE: int = Field(default=1)

    MODBUS_MACHINES: Dict[str, MachineConfig] = Field(default={})

    def update_machines_config(self, machines: Dict[str, MachineConfig]):
        """기계 설정을 업데이트"""
        self.MODBUS_MACHINES = machines

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
