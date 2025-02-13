# app/core/config.py
from pydantic import Field
from pydantic_settings import SettingsConfigDict, BaseSettings


class Settings(BaseSettings):
    MODBUS_DEFAULT_PORT: int = Field(default=502)
    MODBUS_TIMEOUT: int = Field(default=3)
    MODBUS_RETRY_COUNT: int = Field(default=3)
    MODBUS_SLAVE: int = Field(default=1)
    
    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
