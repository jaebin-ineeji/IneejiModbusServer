# 아키텍처 가이드

Modbus 통신 관리 시스템의 전체 아키텍처와 구조에 대한 상세한 설명입니다.

## 🏗 시스템 아키텍처

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Client    │    │   CLI Tools     │    │   External      │
│                 │    │                 │    │   Systems       │
│ - Browser       │    │ - Data Getter   │    │                 │
│                 │    │ - Data Saver    │    │ - Monitoring    │
│ - Dashboard     │    │ - CLI Query     │    │ - Analytics     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   FastAPI       │
                    │   Server        │
                    │                 │
                    │ - REST API      │
                    │ - WebSocket     │
                    │ - Auto Control  │
                    └─────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   SQLite DB     │    │   Modbus        │    │   Log System    │
│                 │    │   Client        │    │                 │
│ - Machines      │    │                 │    │ - App Logs      │
│ - Tags          │    │ - TCP/IP        │    │ - Control Logs  │
│ - History       │    │ - Communication │    │ - Error Logs    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Industrial    │
                    │   Equipment     │
                    │                 │
                    │ - PLCs          │
                    │ - Sensors       │
                    │ - Actuators     │
                    └─────────────────┘
```

## 📁 프로젝트 구조

```
IneejiModbusServer/
├── app/                          # 메인 애플리케이션
│   ├── __init__.py
│   ├── api/                      # API 레이어
│   │   ├── __init__.py
│   │   ├── dependencies.py       # API 의존성 관리
│   │   ├── exceptions.py         # API 예외 정의
│   │   ├── middleware.py         # 미들웨어 (로깅, CORS 등)
│   │   └── routes/               # API 엔드포인트
│   │       ├── __init__.py
│   │       ├── autocontrol.py    # 자동 제어 API
│   │       ├── config.py         # 설정 관리 API
│   │       ├── direct/           # 직접 제어 API
│   │       │   ├── analog.py     # 아날로그 신호 제어
│   │       │   └── digital.py    # 디지털 신호 제어
│   │       ├── health.py         # 헬스체크 API
│   │       └── machine.py        # 기계 관리 API
│   ├── core/                     # 핵심 설정
│   │   ├── __init__.py
│   │   ├── config.json           # 기본 설정 파일
│   │   ├── config.py             # 설정 클래스
│   │   └── logging_config.py     # 로깅 설정
│   ├── models/                   # 데이터 모델
│   │   ├── __init__.py
│   │   ├── schemas.py            # Pydantic 스키마
│   │   ├── swagger_docs.py       # Swagger 문서 정의
│   │   └── validator.py          # 데이터 검증
│   └── services/                 # 비즈니스 로직
│       ├── __init__.py
│       ├── config.py             # 설정 서비스
│       ├── exceptions.py         # 서비스 예외
│       └── modbus/               # Modbus 통신 서비스
│           ├── __init__.py
│           ├── analog.py         # 아날로그 신호 처리
│           ├── autocontrol.py    # 자동 제어 로직
│           ├── client.py         # Modbus 클라이언트
│           ├── dao/              # 데이터 액세스
│           │   └── auto_controll_dao.py
│           ├── digital.py        # 디지털 신호 처리
│           ├── machine.py        # 기계 관리 로직
│           └── websocket_service.py  # WebSocket 서비스
├── docs/                         # 문서
│   ├── API_REFERENCE.md          # API 문서
│   ├── ARCHITECTURE.md           # 아키텍처 문서
│   ├── INSTALLATION.md           # 설치 가이드
│   └── AUTOCONTROL.md            # 자동 제어 가이드
├── logs/                         # 로그 디렉토리
│   └── autocontrol/              # 자동 제어 로그
├── build.py                      # 빌드 스크립트
├── main.py                       # 애플리케이션 진입점
├── modbus_database_cli.py        # 데이터베이스 CLI 도구
├── modbus_database_getter.py     # 데이터 조회 도구
├── modbus_database_getter_local.py
├── modbus_database_saver.py      # 데이터 수집 도구
├── modbus_database_saver_local.py
├── requirements.txt              # Python 의존성
├── README.md                     # 메인 문서
└── test.py                       # 테스트 스크립트
```

## 🗄 데이터베이스 구조

### SQLite 스키마

#### machines 테이블
```sql
CREATE TABLE machines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,           -- 기계 이름 (예: "oil_main")
    ip_address TEXT NOT NULL,            -- IP 주소 (예: "192.168.1.100") 
    port INTEGER NOT NULL,               -- 포트 (예: 502)
    slave INTEGER NOT NULL               -- 슬레이브 주소 (예: 1)
);
```

#### tags 테이블  
```sql
CREATE TABLE tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    machine_id INTEGER NOT NULL,        -- 연결된 기계 ID (machines.id 참조)
    tag_name TEXT NOT NULL,             -- 태그 이름 (예: "pv", "sv")
    tag_type TEXT NOT NULL,             -- 태그 유형 (ANALOG, DIGITAL, DIGITAL_AM, DIGITAL_RM)
    logical_register TEXT NOT NULL,     -- 논리적 레지스터 주소 (예: "1000")
    real_register TEXT NOT NULL,        -- 실제 레지스터 주소 (예: "1000")
    permission TEXT NOT NULL,           -- 권한 (READ_ONLY, WRITE_ONLY, READ_WRITE)
    FOREIGN KEY (machine_id) REFERENCES machines (id)
);
```

#### modbus_data 테이블 (히스토리 데이터)
```sql
CREATE TABLE modbus_data (
    timestamp TEXT PRIMARY KEY,         -- 타임스탬프 (YYYY-MM-DD HH:MM:SS)
    oil_main_pv REAL,                   -- Oil Main PV 값
    oil_main_sv REAL,                   -- Oil Main SV 값
    oil_1l_pv REAL,                     -- Oil 1L PV 값
    oil_1l_sv REAL,                     -- Oil 1L SV 값
    -- ... 기타 기계별 PV/SV 값들
    arch_3_pv REAL,                     -- Arch #3 PV 값
    arch_3_sv REAL                      -- Arch #3 SV 값
);

CREATE INDEX idx_timestamp ON modbus_data (timestamp);
```

### 데이터 관계도

```
machines (1) ←──── (N) tags
    │
    ├── id
    ├── name ──────────┐
    ├── ip_address     │
    ├── port           │
    └── slave          │
                       │
                       │ (기계 이름 매핑)
                       ▼
                modbus_data
                    │
                    ├── timestamp
                    ├── {machine_name}_pv
                    └── {machine_name}_sv
```

## 🔧 핵심 컴포넌트

### 1. Modbus 클라이언트 (`client.py`)
- **역할**: Modbus TCP/IP 통신 담당
- **주요 기능**:
  - 연결 관리 (connect/disconnect)
  - 레지스터 읽기/쓰기 (read_registers/write_registers)
  - 코일 읽기/쓰기 (read_coils/write_coils)
  - 연결 상태 확인 (is_connected)

```python
class ModbusClient:
    def __init__(self, ip_address: str, port: int, slave: int)
    def connect() -> bool
    def disconnect() -> None
    def read_registers(address: int, count: int) -> List[int]
    def write_registers(address: int, values: List[int]) -> bool
    def read_coils(address: int, count: int) -> List[bool]
    def write_coils(address: int, values: List[bool]) -> bool
```

### 2. 기계 관리 (`machine.py`)
- **역할**: 기계 설정 및 연결 관리
- **주요 기능**:
  - 기계 등록/삭제
  - 태그 관리 (추가/수정/삭제)
  - 연결 상태 확인
  - 설정 검증

### 3. 신호 처리 (`analog.py`, `digital.py`)
- **Analog**: 아날로그 신호 (온도, 압력 등) 처리
- **Digital**: 디지털 신호 (On/Off, Auto/Manual 등) 처리
- **주요 기능**:
  - 값 읽기/쓰기
  - 데이터 타입 변환
  - 범위 검증

### 4. 자동 제어 (`autocontrol.py`)
- **역할**: 스케줄 기반 자동 제어
- **주요 기능**:
  - 제어 설정 관리
  - 스케줄 실행
  - 로그 기록 (Parquet 형식)
  - 예외 처리

### 5. WebSocket 서비스 (`websocket_service.py`)
- **역할**: 실시간 데이터 스트리밍
- **주요 기능**:
  - 클라이언트 연결 관리
  - 주기적 데이터 전송
  - 멀티캐스트 지원

## 🔄 데이터 플로우

### 1. 읽기 요청 플로우
```
Client → FastAPI → Machine Service → Modbus Client → Equipment
   ↑                                                      ↓
Response ← Data Processing ← Tag Service ←── Modbus Response
```

### 2. 쓰기 요청 플로우  
```
Client → FastAPI → Validation → Machine Service → Modbus Client → Equipment
   ↑                                                                ↓
Response ← Log Recording ← Success Check ←─────── Write Response ←──┘
```

### 3. 자동 제어 플로우
```
Scheduler → Auto Control Service → Target Value Check
    ↓                                      ↓
Log File ← Execution Results ←── Write Operation
```

### 4. 실시간 모니터링 플로우
```
Timer → Data Collection → WebSocket Service → Client
  ↓                            ↓
Equipment ← Modbus Client ←── Tag Service
```

## 🎯 기계 및 태그 관리 로직

### 기계 추가 프로세스
1. **요청 검증**: IP, 포트, 슬레이브 주소 유효성 확인
2. **중복 검사**: 동일한 이름의 기계가 있는지 확인
3. **연결 테스트**: Modbus 연결 가능 여부 확인
4. **데이터베이스 저장**: machines 테이블에 정보 저장
5. **태그 등록**: 함께 제공된 태그들 등록

### 태그 관리 로직
1. **태그 타입별 처리**:
   - `ANALOG`: 홀딩 레지스터 사용
   - `DIGITAL`: 코일 사용
   - `DIGITAL_AM`: Auto(1)/Manual(0) 매핑
   - `DIGITAL_RM`: Remote(1)/Local(0) 매핑

2. **레지스터 주소 관리**:
   - `logical_register`: 사용자가 보는 주소
   - `real_register`: 실제 Modbus 주소 (0-based 변환)

3. **권한 관리**:
   - `READ_ONLY`: 읽기만 가능
   - `WRITE_ONLY`: 쓰기만 가능 (드물게 사용)
   - `READ_WRITE`: 읽기/쓰기 모두 가능

### 값 처리 로직
```python
# 아날로그 값 처리 예시
def process_analog_value(raw_value: int, machine_name: str) -> float:
    if machine_name in ['oil_main', 'oxy_main']:
        return round(raw_value, 1)  # 그대로 유지
    else:
        return round(raw_value / 10, 1)  # 10으로 나누어 스케일링

# 디지털 값 처리 예시  
def process_digital_value(raw_value: bool, tag_type: str) -> str:
    if tag_type == 'DIGITAL':
        return 'ON' if raw_value else 'OFF'
    elif tag_type == 'DIGITAL_AM':
        return 'AUTO' if raw_value else 'MANUAL'
    elif tag_type == 'DIGITAL_RM':
        return 'REMOTE' if raw_value else 'LOCAL'
```

## 📊 성능 고려사항

### 1. 연결 관리
- **연결 풀링**: 기계별 연결을 재사용하여 오버헤드 감소
- **타임아웃 설정**: 응답 없는 연결의 빠른 감지 및 복구
- **재연결 로직**: 연결 끊어짐 시 자동 재연결 시도

### 2. 데이터 수집 최적화
- **배치 읽기**: 연속된 레지스터를 한 번에 읽어 효율성 증대
- **캐싱**: 자주 액세스되는 설정 정보 메모리 캐싱
- **비동기 처리**: 여러 기계의 동시 데이터 수집

### 3. 데이터베이스 최적화
- **인덱싱**: 타임스탬프 기준 인덱스로 조회 성능 향상
- **파티셔닝**: 대용량 히스토리 데이터의 효율적 관리
- **정리 작업**: 오래된 데이터의 자동 정리 또는 아카이빙

## 🔒 보안 및 안정성

### 1. 에러 처리
- **계층별 예외 처리**: Service → API → Client 순으로 명확한 에러 전파
- **로깅**: 모든 중요 작업과 에러에 대한 상세 로그 기록
- **복구 메커니즘**: 통신 오류 시 자동 재시도 및 대체 로직

### 2. 데이터 무결성
- **트랜잭션**: 관련된 여러 작업을 하나의 트랜잭션으로 처리
- **검증**: 입력 데이터의 철저한 검증 및 sanitization
- **백업**: 설정 및 히스토리 데이터의 정기적 백업

### 3. 모니터링
- **헬스체크**: 시스템 상태 실시간 모니터링
- **알림**: 중요한 이벤트 및 에러에 대한 알림 시스템
- **메트릭**: 성능 지표 수집 및 분석

## 🔧 확장성 고려사항

### 1. 수평 확장
- **마이크로서비스**: 기능별로 서비스를 분리하여 독립적 확장
- **로드 밸런싱**: 여러 인스턴스 간 부하 분산
- **메시지 큐**: 비동기 작업 처리를 위한 큐 시스템

### 2. 수직 확장
- **리소스 최적화**: 메모리 및 CPU 사용량 최적화
- **캐싱 전략**: 다단계 캐싱으로 성능 향상
- **데이터베이스 튜닝**: 쿼리 최적화 및 인덱스 전략

이 아키텍처는 안정적이고 확장 가능한 산업용 Modbus 통신 시스템을 제공하며, 실시간 모니터링과 자동 제어 기능을 통해 효율적인 장비 관리를 지원합니다.
