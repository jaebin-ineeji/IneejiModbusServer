import logging
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime

# 로그 디렉토리 생성
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# 로그 파일명 설정 (날짜별)
current_date = datetime.now().strftime("%Y-%m-%d")
LOG_FILENAME = f"{LOG_DIR}/api_{current_date}.log"


# 로거 설정
def setup_logger(name: str):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # 파일 핸들러 설정 (최대 10MB, 백업 5개)
    file_handler = RotatingFileHandler(
        LOG_FILENAME, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )

    # 로그 포맷 설정
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    return logger
