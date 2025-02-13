# app/services/modbus/client.py
from collections.abc import Iterator
import sqlite3
from typing import Dict, Optional
from pymodbus.client import ModbusTcpClient
from contextlib import contextmanager
import os
from app.core.logging_config import setup_logger
from app.models.schemas import DataType, MachineConfig, Permission, TagConfig
from app.core.config import settings
from app.services.exceptions import ModbusConnectionError

logger = setup_logger(__name__)


class ModbusClientManager:
    _instances: Dict[str, "ModbusClientManager"] = {}
    _clients: Dict[str, ModbusTcpClient] = {}

    def __new__(cls, host: str, port: int = 502, slave: int = 1):
        # IP 주소별로 단일 인스턴스 유지
        key = f"{host}:{port}"
        if key not in cls._instances:
            cls._instances[key] = super().__new__(cls)
            cls._instances[key]._initialized = False

        return cls._instances[key]

    def __init__(self, host: str, port: int = 502, slave: int = 1):
        if not hasattr(self, "_initialized") or not self._initialized:
            self.host = host
            self.port = port
            self.slave = slave
            self._key = f"{host}:{port}"
            self._client: Optional[ModbusTcpClient] = None
            self._initialized = True

    def _ensure_connection(self):
        """연결이 없거나 끊어진 경우 새로운 연결 생성"""
        if self._client is None or not self._client.connected:
            try:
                self._client = ModbusTcpClient(
                    host=self.host, port=self.port, timeout=3, retries=3
                )
                if not self._client.connect():
                    raise ModbusConnectionError(
                        f"Modbus 서버 연결 실패 - host: {self.host}, port: {self.port}"
                    )
                # 연결 성공 시 _clients에 저장
                self._clients[self._key] = self._client
                logger.debug(f"Modbus 연결 성공: {self._key}")
            except Exception as e:
                logger.error(f"Modbus 연결 오류: {self._key} - {str(e)}")
                raise

    async def test_connection(self):
        try:
            with self.connect():
                return True
        except Exception:
            return False

    @contextmanager
    def connect(self) -> Iterator[ModbusTcpClient]:
        """컨텍스트 매니저로 연결 제공"""
        self._ensure_connection()
        if self._client is None:  # 타입 체크를 위한 추가 검사
            raise ConnectionError("Modbus 클라이언트가 초기화되지 않았습니다")
        try:
            yield self._client
        except Exception as e:
            logger.error(f"Modbus 통신 오류: {self._key} - {str(e)}")
            # 연결에 문제가 있다면 다음 시도에서 재연결하도록 None으로 설정
            self._client = None
            raise

    @classmethod
    def close_all(cls):
        """모든 연결 종료 (필요한 경우에만 사용)"""
        close_list = []
        for key, client in cls._clients.items():
            try:
                if client.connected:
                    client.close()
                    close_list.append(key)
            except Exception as e:
                logger.error(f"Modbus 연결 종료 오류: {key} - {str(e)}")
        logger.info(f"Modbus 연결 종료: {close_list}")
        cls._clients.clear()


class DatabaseClientManager:
    def __init__(self, db_name: str):
        """데이터베이스 클라이언트 매니저 초기화

        Args:
            db_name (str): 데이터베이스 파일 경로
        """
        self.db_name = db_name
        self._connection: Optional[sqlite3.Connection] = None
        self.initialize_database()
        self.load_modbus_config()

    @contextmanager
    def get_connection(self):
        """데이터베이스 연결을 제공하는 컨텍스트 매니저

        Yields:
            sqlite3.Connection: 데이터베이스 연결 객체

        Raises:
            sqlite3.Error: 데이터베이스 연결 또는 조작 중 발생하는 오류
        """
        if self._connection is None:
            try:
                self._connection = sqlite3.connect(
                    self.db_name,
                    detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
                )
                # 외래 키 제약 조건 활성화
                self._connection.execute("PRAGMA foreign_keys = ON")
                # Row를 딕셔너리 형태로 반환하도록 설정
                self._connection.row_factory = sqlite3.Row

            except sqlite3.Error as e:
                logger.error(f"데이터베이스 연결 실패: {e}")
                raise

        try:
            yield self._connection
            self._connection.commit()
        except Exception as e:
            self._connection.rollback()
            logger.error(f"데이터베이스 작업 실패: {e}")
            raise
        finally:
            if self._connection:
                self._connection.close()
                self._connection = None

    def initialize_database(self):
        db_exists = os.path.exists(self.db_name)

        if not db_exists:
            try:
                with self.get_connection() as conn:
                    cursor = conn.cursor()

                    # machines 테이블 생성
                    cursor.execute(
                        """
                    CREATE TABLE machines (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT UNIQUE NOT NULL,
                        ip_address TEXT NOT NULL
                    )
                    """
                    )

                    # tags 테이블 생성
                    cursor.execute(
                        """
                    CREATE TABLE tags (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        machine_id INTEGER NOT NULL,
                        logical_name TEXT NOT NULL,
                        data_type TEXT NOT NULL,
                        logical_register TEXT NOT NULL,
                        real_register TEXT NOT NULL,
                        permission TEXT NOT NULL,
                        slave INTEGER NOT NULL,
                        FOREIGN KEY (machine_id) REFERENCES machines(id) ON DELETE CASCADE
                    )
                    """
                    )

                    logger.info(
                        f"데이터베이스 '{self.db_name}'와 테이블들이 성공적으로 생성되었습니다."
                    )
            except sqlite3.Error as e:
                logger.error(f"데이터베이스 생성 중 오류 발생: {e}")
                raise
        else:
            logger.info(
                f"데이터베이스 '{self.db_name}'가 이미 존재해서 생성을 건너뜁니다."
            )

    def execute_query(self, query: str, params: tuple = ()) -> list:
        """SQL 쿼리를 실행하고 결과를 반환

        Args:
            query (str): 실행할 SQL 쿼리
            params (tuple, optional): 쿼리 파라미터. Defaults to ().

        Returns:
            list: 쿼리 실행 결과

        Raises:
            sqlite3.Error: 쿼리 실행 중 발생하는 오류
        """
        with self.get_connection() as conn:
            try:
                cursor = conn.cursor()
                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
            except sqlite3.Error as e:
                logger.error(f"쿼리 실행 실패: {e}\n쿼리: {query}\n파라미터: {params}")
                raise

    def execute_many(self, query: str, params_list: list[tuple]) -> None:
        """여러 SQL 쿼리를 한 번에 실행

        Args:
            query (str): 실행할 SQL 쿼리 템플릿
            params_list (list[tuple]): 쿼리 파라미터 리스트

        Raises:
            sqlite3.Error: 쿼리 실행 중 발생하는 오류
        """
        with self.get_connection() as conn:
            try:
                cursor = conn.cursor()
                cursor.executemany(query, params_list)
            except sqlite3.Error as e:
                logger.error(f"대량 쿼리 실행 실패: {e}\n쿼리: {query}")
                raise

    def load_modbus_config(self) -> Dict[str, MachineConfig]:
        """SQLite에서 모든 기계의 IP 및 등록된 태그 데이터를 불러오는 함수"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 기계 정보 불러오기
            cursor.execute("SELECT name, ip_address FROM machines")
            machines: Dict[str, MachineConfig] = {
                name: MachineConfig(ip=ip, tags={}) for name, ip in cursor.fetchall()
            }

            # 태그 정보 불러오기 (각 기계 ID별 태그 리스트)
            cursor.execute(
                """
                SELECT machines.name, tags.logical_name, tags.data_type, tags.logical_register, tags.real_register, 
                    tags.permission, tags.slave
                FROM tags 
                JOIN machines ON machines.id = tags.machine_id
            """
            )

            for (
                machine_name,
                logical_name,
                data_type,
                logical_register,
                real_register,
                permission,
                slave,
            ) in cursor.fetchall():
                if machine_name in machines:
                    machines[machine_name].tags[logical_name] = TagConfig(
                        data_type=DataType(data_type),
                        logical_register=logical_register,
                        real_register=real_register,
                        permission=Permission(permission),
                        slave=slave,
                    )

            logger.info(f"{len(machines)} 대의 기계설정이 로드되었습니다.")
            settings.update_machines_config(machines)
            return machines
