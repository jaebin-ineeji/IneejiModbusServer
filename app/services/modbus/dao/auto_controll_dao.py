from datetime import datetime
from zoneinfo import ZoneInfo
from app.services.modbus.client import DatabaseClientManager
from app.models.schemas import ServiceResult
from app.core.logging_config import setup_logger

logger = setup_logger(__name__)

class AutoControllDAO:
    """자동운전 상태를 데이터베이스에서 관리하는 클래스"""
    
    def __init__(self, db_client: DatabaseClientManager):
        self.db_client = db_client
        self._ensure_table()
    
    def _ensure_table(self):
        """자동운전 테이블이 있는지 확인하고 없으면 생성합니다."""
        with self.db_client.get_connection() as conn:
            cursor = conn.cursor()

            # 테이블 존재 여부 확인
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='autocontrol'
            """)

            if not cursor.fetchone():
                # 테이블 생성
                cursor.execute("""
                    CREATE TABLE autocontrol (
                        id INTEGER PRIMARY KEY CHECK (id = 1),
                        enabled BOOLEAN NOT NULL DEFAULT 0,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                logger.info("autocontrol 테이블이 생성되었습니다.")
    
    def set_autocontrol(self, enabled: bool) -> ServiceResult:
        """시스템 전체의 자동운전 상태를 설정합니다."""
        with self.db_client.get_connection() as conn:
            cursor = conn.cursor()
            try:
                # 레코드가 있는지 확인
                cursor.execute("SELECT COUNT(*) as count FROM autocontrol")
                if cursor.fetchone()["count"] == 0:
                    # 첫 번째 레코드 삽입
                    cursor.execute(
                        "INSERT INTO autocontrol (id, enabled, last_updated) VALUES (1, ?, CURRENT_TIMESTAMP)",
                        (enabled,)
                    )
                else:
                    # 기존 레코드 업데이트
                    cursor.execute(
                        "UPDATE autocontrol SET enabled = ?, last_updated = CURRENT_TIMESTAMP WHERE id = 1",
                        (enabled,)
                    )

                state_text = "활성화" if enabled else "비활성화"
                return ServiceResult(
                    success=True,
                    message=f"자동운전이 {state_text} 되었습니다.",
                    data={"enabled": enabled}
                )
            except Exception as e:
                logger.error(f"자동운전 상태 변경 중 오류: {e}")
                return ServiceResult(
                    success=False,
                    message=f"자동운전 상태 변경 중 오류가 발생했습니다: {e}"
                )
    
    def get_autocontrol(self) -> ServiceResult:
        """시스템의 자동운전 상태를 조회합니다."""
        with self.db_client.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT enabled, last_updated FROM autocontrol WHERE id = 1")
                result = cursor.fetchone()

                if not result:
                    # 설정이 없는 경우
                    return ServiceResult(
                        success=True,
                        message="자동운전 상태가 설정되지 않았습니다. 기본값은 비활성화입니다.",
                        data={"enabled": False}
                    )
                
                utc_time = result["last_updated"]
                if utc_time.tzinfo is None:
                    utc_time = utc_time.replace(tzinfo=ZoneInfo("UTC"))
                kst_time = utc_time.astimezone(ZoneInfo("Asia/Seoul"))

                return ServiceResult(
                    success=True,
                    message="자동운전 상태를 조회했습니다.",
                    data={
                        "enabled": bool(result["enabled"]),
                        "last_updated": kst_time.isoformat()
                    }
                )
            except Exception as e:
                logger.error(f"자동운전 상태 조회 중 오류: {e}")
                return ServiceResult(
                    success=False,
                    message=f"자동운전 상태 조회 중 오류가 발생했습니다: {e}"
                )