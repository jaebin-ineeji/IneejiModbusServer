import requests
import sqlite3
from datetime import datetime
import logging
import time
import os
import signal
import atexit
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.config import settings

# 로그 디렉토리 설정
LOG_DIR = f'{settings.PROJECT_DIR}/logs/dblog'
os.makedirs(LOG_DIR, exist_ok=True)

# SQLite 데이터베이스 파일 경로
DB_NAME = settings.SAVER_DB_NAME
DB_FILE_ROOT = f'{settings.PROJECT_DIR}/{DB_NAME}.db'


def setup_logger():
    """날짜별로 로그 파일을 생성하는 로거를 설정합니다."""
    # 오늘 날짜로 로그 파일 이름 생성
    today = datetime.now().strftime('%Y-%m-%d')
    log_file = os.path.join(LOG_DIR, f'modbus_db_saver_{today}.log')
    
    # 로거 설정
    logger = logging.getLogger('modbus_db_saver')
    logger.setLevel(logging.INFO)
    
    # 기존 핸들러 제거 (재설정 시 중복 방지)
    if logger.handlers:
        for handler in logger.handlers:
            logger.removeHandler(handler)
    
    # 파일 핸들러 추가
    file_handler = logging.FileHandler(log_file)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger

# 글로벌 로거 객체 초기화
logger = setup_logger()

def is_save_time():
    """현재 시간이 저장 시간(30초 또는 0초)인지 확인합니다."""
    now = datetime.now()
    return now.second in [0, 30]


def init_database():
    """데이터베이스와 테이블을 초기화합니다."""
    try:
        conn = sqlite3.connect(DB_FILE_ROOT)
        cursor = conn.cursor()
        
        # 테이블이 없으면 생성
        cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS {DB_NAME} (
            timestamp TEXT PRIMARY KEY,
            oil_main_pv REAL,
            oil_main_sv REAL,
            oil_1l_pv REAL,
            oil_1l_sv REAL,
            oil_2l_pv REAL,
            oil_2l_sv REAL,
            oil_3l_pv REAL,
            oil_3l_sv REAL,
            oil_4l_pv REAL,
            oil_4l_sv REAL,
            oil_5l_pv REAL,
            oil_5l_sv REAL,
            oil_1r_pv REAL,
            oil_1r_sv REAL,
            oil_2r_pv REAL,
            oil_2r_sv REAL,
            oil_3r_pv REAL,
            oil_3r_sv REAL,
            oil_4r_pv REAL,
            oil_4r_sv REAL,
            oxy_main_pv REAL,
            oxy_main_sv REAL,
            oxy_1l_pv REAL,
            oxy_1l_sv REAL,
            oxy_2l_pv REAL,
            oxy_2l_sv REAL,
            oxy_3l_pv REAL,
            oxy_3l_sv REAL,
            oxy_4l_pv REAL,
            oxy_4l_sv REAL,
            oxy_5l_pv REAL,
            oxy_5l_sv REAL,
            oxy_1r_pv REAL,
            oxy_1r_sv REAL,
            oxy_2r_pv REAL,
            oxy_2r_sv REAL,
            oxy_3r_pv REAL,
            oxy_3r_sv REAL,
            oxy_4r_pv REAL,
            oxy_4r_sv REAL,
            arch_3_pv REAL,
            arch_3_sv REAL
        )''')
        # 타임스탬프 인덱스 생성
        cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_timestamp ON {DB_NAME} (timestamp)')

        conn.commit()
        conn.close()
        logger.info("데이터베이스 테이블 초기화 완료")
        return True
    except Exception as e:
        logger.error(f"데이터베이스 초기화 오류: {str(e)}")
        return False

def get_tag_values():
    """기계별 태그 값을 가져옵니다."""
    # 조회할 기계 이름들과 태그 이름들을 리스트로 설정
    machine_names = ['oil_main', 'oil_1l', 'oil_2l','oil_3l','oil_4l','oil_5l','oil_1r','oil_2r','oil_3r','oil_4r','oxy_main','oxy_1l','oxy_2l','oxy_3l','oxy_4l','oxy_5l','oxy_1r','oxy_2r','oxy_3r','oxy_4r'] # 3로에서는 'arch_3' 제외
    tag_names = ['pv', 'sv']

    # 최종 결과를 저장할 딕셔너리
    aggregated_results = {}

    # 각 기계별로 API 호출을 수행
    logger.info(f"== □ □ □ 데이터 조회 시작 ==")

    for machine in machine_names:
        url = f"http://localhost:4444/machine/{machine}/values"
        # 태그 이름을 콤마(,)로 연결하여 쿼리 파라미터로 전달
        params = {"tag_names": ','.join(tag_names)}
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                json_data = response.json()
                if json_data.get("success"):
                    # 기계 이름을 key로 하여 해당 기계의 태그 값을 저장
                    aggregated_results[machine] = json_data.get("data")
                else:
                    logger.warning(f"기계 {machine}의 데이터 가져오기 실패: {json_data.get('message')}")
            else:
                logger.warning(f"기계 {machine}의 HTTP 오류: {response.status_code}")
        except Exception as e:
            logger.warning(f"기계 {machine} 조회 중 예외 발생: {str(e)}")
    
    logger.info(f"== ■ □ □ 데이터 조회 완료 ==")
    return aggregated_results

def process_value(machine, value):
    """기계와 값에 따라 적절한 변환을 적용합니다."""
    try:
        # 값이 None이거나 빈 문자열이면 None 반환
        if value is None or value == '':
            logger.warning(f"기계 {machine}에서 빈 값 발견")
            return None
            
        # 숫자로 변환
        num_value = float(value)
        
        # oil_main, oxy_main은 그대로 유지하고 소수점 추가
        if machine in ['oil_main', 'oxy_main']:
            processed_value = round(num_value, 1)  # 소수점 한 자리로 반올림
        else:
            # 나머지는 10으로 나누고 소수점 한 자리로 반올림
            processed_value = round(num_value / 10, 1)
            
        return processed_value
    except (ValueError, TypeError) as e:
        logger.warning(f"값 처리 중 오류: {str(e)}, machine: {machine}, value: {value}")
        return None

def save_to_database(tag_values):
    """태그 값을 데이터베이스에 저장합니다."""
    try:
        if not tag_values:
            logger.warning("저장할 태그 값이 없습니다")
            return False
            
        # 현재 시간을 YYYY-MM-DD HH:MM:SS 형식으로 가져옴
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        logger.info(f"== ■ ■ □ 데이터 저장 시작 ==")
        # 데이터베이스 연결
        conn = sqlite3.connect(DB_FILE_ROOT)
        cursor = conn.cursor()
        
        # INSERT 쿼리 생성을 위한 컬럼과 값 준비
        columns = ['timestamp']
        values = [current_time]
        placeholders = ['?']
        
        # 각 기계의 태그 값을 컬럼과 값 목록에 추가
        for machine, data in tag_values.items():
            if isinstance(data, dict) and 'error' not in data:
                  for tag_name in ['pv', 'sv']:
                    tag_key = next((k for k in data.keys() if k.lower() == tag_name.lower()), None)
                    if tag_key:
                        column_name = f"{machine}_{tag_name}"
                        columns.append(column_name)
                        processed_value = process_value(machine, data[tag_key])
                        if processed_value is not None:
                            values.append(str(processed_value))
                            placeholders.append('?')
        
        # INSERT 쿼리 실행
        query = f"INSERT INTO {DB_NAME} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
        cursor.execute(query, values)
        conn.commit()
        conn.close()
        
        logger.info(f"== ■ ■ ■ 데이터베이스에 {current_time} 시간의 데이터 저장 완료 ==")
        return True
    except Exception as e:
        logger.error(f"데이터베이스 저장 오류: {str(e)}")
        return False

def check_logger_date():
    """날짜가 변경되었는지 확인하고 필요시 로거를 재설정합니다."""
    global logger
    
    # 현재 로그 파일의 날짜 확인
    current_date = datetime.now().strftime('%Y-%m-%d')
    for handler in logger.handlers:
        if isinstance(handler, logging.FileHandler):
            log_file_path = handler.baseFilename
            log_file_date = os.path.basename(log_file_path).split('_')[-1].split('.')[0]
            
            # 날짜가 변경되었으면 로거 재설정
            if log_file_date != current_date:
                logger = setup_logger()
                logger.info(f"날짜 변경으로 로그 파일 교체: {log_file_date} -> {current_date}")
                break

def wait_for_next_save_time():
    """다음 저장 시간(0초 또는 30초)까지 대기합니다."""
    now = datetime.now()
    seconds = now.second
    
    # 다음 실행 시간 계산 (다음 30초 또는 0초)
    if seconds < 30:
        wait_seconds = 30 - seconds
    else:
        wait_seconds = 60 - seconds
        
    # 밀리초 추가 고려
    wait_seconds -= now.microsecond / 1000000
    if wait_seconds <= 0:
        wait_seconds += 30
        
    logger.info(f"{now.strftime('%Y-%m-%d %H:%M:%S')} - 다음 저장 시간까지 {wait_seconds:.1f}초 대기")
    time.sleep(wait_seconds)

def main():
    """메인 실행 함수"""
    try:
        # 현재 시간이 저장 시간인지 확인
        if not is_save_time():
            logger.info("저장 시간이 아니므로 태그 값 저장을 건너뜁니다.")
            return
            
        # 날짜 변경 확인 및 로거 업데이트
        check_logger_date()
        
        # 태그 값 가져오기
        tag_values = get_tag_values()
        
        # 데이터베이스에 저장
        save_to_database(tag_values)
        
    except Exception as e:
        logger.error(f"실행 중 오류 발생: {str(e)}")


def handle_exit_signal(signum, frame):
    logger.info("================================================")
    logger.info(f"프로그램 종료 시그널({signum}) 감지. 종료 로그를 남깁니다.")
    sys.exit(0)

def on_exit():
    logger.info("프로그램이 정상적으로 종료되었습니다.")
    logger.info("================================================")

if __name__ == "__main__":
    signal.signal(signal.SIGINT, handle_exit_signal)
    signal.signal(signal.SIGTERM, handle_exit_signal)
    atexit.register(on_exit)

    logger.info("================================================")
    logger.info(f"== ** 데이터 수집을 시작합니다. ** ==")
    logger.info("================================================")
    init_database()

    while True:
        # 메인 함수 실행
        main()
        
        # 다음 저장 시간까지 대기
        wait_for_next_save_time()