import sys
import PyInstaller.__main__


def get_hidden_imports():
    return [
        # FastAPI 관련
        "fastapi",
        "uvicorn.logging",
        "uvicorn.lifespan.on",
        "uvicorn.lifespan.off",
        "uvicorn.protocols.http.auto",
        "starlette.middleware.cors",
        # 프로젝트 라우터
        "app.api.routes.health",
        "app.api.routes.machine",
        "app.api.routes.config",
        "app.api.routes.direct.analog",
        "app.api.routes.direct.digital",
        # 프로젝트 서비스
        "app.services.modbus.client",
        "app.services.modbus.machine",
        "app.services.modbus.analog",
        "app.services.modbus.digital",
        "app.services.modbus.websocket_service",
        "app.services.config",
        "app.services.exceptions",
        # 프로젝트 코어
        "app.core.config",
        "app.core.logging_config",
        "app.models.schemas",
        "app.models.validator",
        "app.models.swagger_docs",
        "app.models.exceptions",
        # 기타 필수 패키지
        "pymodbus",
        "pydantic",
        "pydantic_settings",
        "python-dotenv"
        # uvicorn 관련 추가
        "uvicorn",
        "uvicorn.config",
        "uvicorn.main",
        "uvicorn.loops",
        "uvicorn.loops.auto",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.websockets",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan",
    ]


def get_data_files():
    separator = ";" if sys.platform == "win32" else ":"
    return [
        f"requirements.txt{separator}.",
        f".env{separator}.",
        f"main.py{separator}.",
        f"app{separator}app",
    ]


def build_executable():
    options = [
        "main.py",
        "--name=ineeji_modbus_server",
        "--onefile",
        "--console",
        "--noconfirm",
        "--clean",
        "--collect-all",
        "uvicorn",
    ]

    for import_name in get_hidden_imports():
        options.extend(["--hidden-import", import_name])

    for data in get_data_files():
        options.extend(["--add-data", data])

    PyInstaller.__main__.run(options)


if __name__ == "__main__":
    build_executable()
