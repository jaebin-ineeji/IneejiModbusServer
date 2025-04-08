import logging
from logging.handlers import TimedRotatingFileHandler
import os
from datetime import datetime
from zoneinfo import ZoneInfo

# 로그 디렉토리 생성
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# 로그 파일명 설정 (날짜별)
current_date = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d")
LOG_FILENAME = f"{LOG_DIR}/api_{current_date}.log"


# 로거 설정
def setup_logger(name: str):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # TimedRotatingFileHandler 사용 (매일 자정에 로그 파일 교체)
    file_handler = TimedRotatingFileHandler(
        LOG_FILENAME,
        when="midnight",
        interval=1,
        backupCount=30,  # 30일간의 로그 파일 보관
        encoding="utf-8",
    )

    # 로그 파일 이름 포맷 설정 (api_YYYY-MM-DD.log 형식으로 백업 파일 생성)
    file_handler.suffix = "%Y-%m-%d"

    # 로그 포맷 설정 - 한국 시간대 적용
    class KSTFormatter(logging.Formatter):
        def converter(self, timestamp):
            dt = datetime.fromtimestamp(timestamp)
            return dt.replace(tzinfo=ZoneInfo("Asia/Seoul"))

        def formatTime(self, record, datefmt=None):
            dt = self.converter(record.created)
            if datefmt:
                return dt.strftime(datefmt)
            return dt.strftime("%Y-%m-%d %H:%M:%S")

    # 로그 포맷 설정
    formatter = KSTFormatter(
        "%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    return logger
