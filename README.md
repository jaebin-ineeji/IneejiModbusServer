# Modbus 통신 관리 시스템

산업 장비와 Modbus TCP/IP 프로토콜을 통해 통신하여 데이터를 수집하고 제어하는 FastAPI 기반 시스템입니다.

## 📋 주요 기능
- **Modbus 통신**: TCP/IP 프로토콜을 통한 산업 장비 통신
- **실시간 모니터링**: WebSocket을 통한 실시간 데이터 모니터링
- **자동 제어 시스템**: 스케줄에 따른 자동 제어
- **데이터 관리**: 태그 값 읽기/쓰기 및 히스토리 관리
- **RESTful API**: 완전한 REST API 제공

## 🚀 빠른 시작

### 서버 실행

#### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

#### 2. 서버 시작
```bash
# 개발 환경
python main.py

# 또는 uvicorn 직접 사용
uvicorn main:app --host 0.0.0.0 --port 4444

# 백그라운드 실행
nohup python main.py > server.log 2>&1 &
```

#### 3. API 문서 확인
서버 실행 후 다음 URL에서 API 문서를 확인할 수 있습니다:
- Swagger UI: `http://localhost:4444/docs`
- ReDoc: `http://localhost:4444/redoc`
- 상태 확인: `http://localhost:4444/health`

## 🔄 자동 시작 설정

### 재부팅 시 자동 실행 설정

시스템 재부팅 후 자동으로 서버와 데이터 수집기를 시작하도록 설정할 수 있습니다.

#### 1. 스크립트 파일들
프로젝트에는 다음 자동 실행 스크립트들이 준비되어 있습니다:

- `start_server.sh`: Modbus 서버 시작
- `start_saver.sh`: 데이터 수집기 시작  

#### 2. crontab 설정

**crontab 편집:**
```bash
crontab -e
```

**자동 시작 설정 추가:**
```bash
# 개별 설정
@reboot /코드경로/IneejiModbusServer/start_server.sh
@reboot sleep 30 && /코드경로/IneejiModbusServer/start_saver.sh
```

**crontab 확인:**
```bash
crontab -l
```

#### 3. 수동 제어 명령어

```bash
# 개별 시작
./start_server.sh  # 서버만
./start_saver.sh   # 데이터 수집기만
```

#### 4. 로그 확인

자동 시작 로그는 `logs/` 디렉토리에 저장됩니다:

```bash
# 자동 시작 로그
tail -f logs/startup_$(date +%Y-%m-%d).log

# 서버 개별 로그
tail -f logs/server_$(date +%Y-%m-%d).log

# 데이터 수집기 개별 로그
tail -f logs/saver_$(date +%Y-%m-%d).log
```

#### 5. 프로세스 상태 확인

```bash
# 실행 중인 프로세스 확인
ps aux | grep "python main.py\|modbus_database_saver.py" | grep -v grep

# 서버 상태 확인
curl http://localhost:4444/health

# 포트 사용 확인
lsof -i :4444
```

## 🛠 데이터베이스 CLI 도구들

### 설치 및 설정

#### 1. 필수 패키지 설치
```bash
pip install sqlite3 pandas tabulate requests
```

#### 2. 데이터베이스 경로 설정
CLI 도구를 사용하기 전에 각 파일의 DB 경로를 환경에 맞게 수정하세요:

```python
# DB 경로 설정 방법

# 1. .env 파일 생성 (프로젝트 루트에)
PROJECT_DIR=/your/path/IneejiModbusTester

# 2. modbus_database_getter.py 파일만 직접 경로 설정 (6번째 줄)
# (다른 경로에서 독립적으로 실행하는 파일)
DB_FILE_ROOT = f'/your/path/IneejiModbusTester/{DB_NAME}.db'

# 3. 나머지 파일들(cli.py, saver.py)은 .env에서 자동으로 불러옴
```

### 사용법

#### 1. 데이터 조회 CLI (`modbus_database_cli.py`)
히스토리 데이터를 조회하고 페이지 단위로 탐색할 수 있습니다.

```bash
# 대화형 모드 (권장)
python modbus_database_cli.py

# 명령행 모드
python modbus_database_cli.py pv 2    # PV 값만, 2시간 전부터
python modbus_database_cli.py sv 1    # SV 값만, 1시간 전부터  
python modbus_database_cli.py all 24  # 모든 값, 24시간 전부터

# 특정 시간 범위 지정
python modbus_database_cli.py all 1 "2024-01-01 00:00:00" "2024-01-01 23:59:59"
```

**대화형 모드 사용법:**
- 실행 후 값 타입(pv/sv/all), 조회 기간, 시간 범위 등을 대화식으로 입력
- 결과를 페이지 단위로 탐색 가능
- 명령어: `n`(다음), `b`(이전), `g 숫자`(페이지 이동), `q`(종료)

#### 2. 데이터 수집기 (`modbus_database_saver.py`)
Modbus 서버에서 30초마다 데이터를 자동 수집하여 SQLite DB에 저장합니다.

```bash
# 데이터 수집 시작 (포어그라운드)
python modbus_database_saver.py

# 백그라운드 실행
nohup python modbus_database_saver.py > saver.log 2>&1 &

# 로그 확인
tail -f /your/path/IneejiModbusTester/logs/dblog/modbus_db_saver_$(date +%Y-%m-%d).log
```

#### 3. 데이터 조회 함수 (`modbus_database_getter.py`)
다른 Python 스크립트에서 데이터를 조회할 때 사용합니다.

```python
from modbus_database_getter import get_modbus_data

# 최근 1시간 모든 데이터
data = get_modbus_data('all', hours=1)

# 최근 24시간 PV 데이터만
pv_data = get_modbus_data('pv', hours=24)

# 특정 시간 범위
data = get_modbus_data('all', 
    start_time='2024-01-01 00:00:00',
    end_time='2024-01-01 23:59:59')
```

## 📚 상세 문서

### 📖 문서 링크
- **[API 레퍼런스](./docs/API_REFERENCE.md)**: 모든 API 엔드포인트 상세 설명
- **[아키텍처 가이드](./docs/ARCHITECTURE.md)**: 프로젝트 구조, 데이터베이스 스키마
- **[설치 가이드](./docs/INSTALLATION.md)**: 오프라인 설치, 리눅스 환경 설정
- **[자동 제어 가이드](./docs/AUTOCONTROL.md)**: 자동 제어 시스템 사용법

### 🔧 시스템 요구사항
- Python 3.10 이상
- SQLite3
- Modbus TCP/IP 지원 장비
- 메모리: 최소 512MB RAM
- 디스크: 최소 1GB 여유 공간

### ⚡ 주요 API 엔드포인트 (요약)
```
GET  /health                              - 시스템 상태 확인
GET  /machine                             - 모든 기계 목록
POST /machine/{machine_name}              - 기계 추가
GET  /machine/{machine_name}/tags         - 태그 목록
POST /machine/{machine_name}/tags         - 태그 추가  
GET  /machine/{machine_name}/tags/{tag}   - 태그 값 읽기
POST /machine/{machine_name}/tags/{tag}   - 태그 값 쓰기
POST /autocontrol                         - 자동 제어 설정
WebSocket /machine/{machine_name}/ws      - 실시간 모니터링
```

## 🐛 문제 해결

### 자주 발생하는 문제들
1. **서버 연결 오류**: 포트 4444가 사용 중인지 확인
2. **DB 경로 오류**: CLI 도구의 DB_FILE_ROOT 경로 확인
3. **권한 오류**: 데이터베이스 파일/디렉토리 쓰기 권한 확인
4. **Modbus 통신 오류**: 장비 IP, 포트, 슬레이브 주소 확인

### 로그 확인
```bash
# 서버 로그
tail -f server.log

# 데이터 수집기 로그  
tail -f /path/to/logs/dblog/modbus_db_saver_$(date +%Y-%m-%d).log

# 자동 제어 로그
ls -la logs/autocontrol/
```

## 📝 라이센스
이 프로젝트는 인이지 내부 용도로 개발되었습니다.

---

**더 자세한 정보는 [문서 폴더](./docs/)의 각 가이드를 참고하세요.**
