# Modbus 통신 관리 시스템

## 프로젝트 개요
이 프로젝트는 산업 장비와 Modbus TCP/IP 프로토콜을 통해 통신하여 데이터를 수집하고 제어하는 시스템입니다. 아날로그 및 디지털 신호를 처리하며, FastAPI 기반의 RESTful API를 통해 장비와의 통신을 관리합니다.

## 주요 기능
- **Modbus 통신**: TCP/IP 프로토콜을 통한 산업 장비 통신
- **기계 관리**: 연결된 장비의 추가, 삭제, 설정 관리
- **태그 관리**: 장비별 태그 추가, 삭제, 업데이트
- **아날로그 신호 관리**: 아날로그 값 읽기 및 쓰기 기능 제공
- **디지털 신호 관리**: 디지털 값 읽기 및 쓰기 기능 제공
- **자동 제어 시스템**: 정의된 스케줄에 따라 장비를 자동으로 제어
- **실시간 모니터링**: 웹소켓을 통한 실시간 태그 값 모니터링
- **장비 상태 모니터링**: 연결된 장비의 상태 확인 및 건강 상태 모니터링
- **데이터베이스 관리**: 장비 및 태그 정보 관리를 위한 SQLite 데이터베이스
- **제어 로깅**: 모든 제어 작업에 대한 자세한 로그 기록

## API 엔드포인트

### 건강 상태 확인
- `GET /health`: 시스템 상태 확인

### 기계 관리
- `GET /machine`: 모든 기계 목록 조회
- `GET /machine/{machine_name}`: 특정 기계의 설정 조회
- `POST /machine/{machine_name}`: 새로운 기계 추가
- `DELETE /machine/{machine_name}`: 기계 삭제

### 태그 관리
- `GET /machine/{machine_name}/tags`: 특정 기계의 모든 태그 조회
- `GET /machine/{machine_name}/tags/{tag_name}/config`: 특정 태그의 설정 조회
- `POST /machine/{machine_name}/tags`: 새로운 태그 추가
- `PUT /machine/{machine_name}/tags/{tag_name}`: 태그 설정 업데이트
- `DELETE /machine/{machine_name}/tags/{tag_name}`: 태그 삭제

### 태그 값 읽기/쓰기
- `GET /machine/{machine_name}/tags/{tag_name}`: 특정 태그의 값 읽기
- `POST /machine/{machine_name}/tags/{tag_name}`: 특정 태그에 값 쓰기
- `GET /machine/{machine_name}/values`: 선택한 여러 태그의 값을 한 번에 조회

### 실시간 모니터링
- `WebSocket /machine/{machine_name}/ws`: 특정 기계의 태그 값 실시간 모니터링
- `WebSocket /machine/ws`: 모든 기계의 태그 값 실시간 모니터링

### 자동 제어 관리
- `POST /autocontrol`: 자동 제어 설정 구성 (제어할 기계와 태그 설정)
- `POST /autocontrol/execute`: 자동 제어 즉시 실행 (기존 설정 또는 새 설정으로)
- `PUT /autocontrol/toggle`: 자동 제어 모드 활성화/비활성화
- `GET /autocontrol`: 현재 자동 제어 상태 및 설정 조회

## 데이터베이스 구조

### 장비 테이블 (machines)
```
id INTEGER PRIMARY KEY AUTOINCREMENT
name TEXT UNIQUE NOT NULL            # 장비 이름
ip_address TEXT NOT NULL             # 장비 IP 주소
port INTEGER NOT NULL                # 통신 포트
slave INTEGER NOT NULL               # 슬레이브 주소
```

### 태그 테이블 (tags)
```
id INTEGER PRIMARY KEY AUTOINCREMENT
machine_id INTEGER NOT NULL          # 연결된 장비 ID
tag_name TEXT NOT NULL               # 태그 이름
tag_type TEXT NOT NULL               # 태그 유형 (아날로그/디지털)
logical_register TEXT NOT NULL       # 논리적 레지스터 주소
real_register TEXT NOT NULL          # 실제 레지스터 주소
permission TEXT NOT NULL             # 접근 권한 (읽기/쓰기)
```

## 기술 스택
- **백엔드**: Python 3.10, FastAPI
- **통신 프로토콜**: Modbus TCP/IP
- **데이터베이스**: SQLite
- **데이터 처리**: Pandas
- **로깅**: 로그 파일 및 Parquet 파일을 통한 데이터 저장
- **기타**: Modbus 통신을 위한 PyModbus

## 오프라인 환경 설치 가이드

### 패키지 다운로드 및 압축
```bash
mkdir -p packages  # 패키지를 저장할 디렉토리 생성
pip download --platform manylinux2014_x86_64 --only-binary=:all: -d packages -r requirements.txt
```

### 압축 파일 생성
```bash
tar -czvf python_env.tar.gz packages requirements.txt
# 필요시 추가 파일 포함
# logging_config.py main.py middleware.py schemas.py utils.py README.md
```

### 압축 해제
```bash
tar -xzvf python_env.tar.gz
```

## 리눅스 환경 설정

### 파이썬 3.10.5 설치
```bash
curl -O https://www.python.org/ftp/python/3.10.5/Python-3.10.5-linux-x86_64.tar.xz
mv /path/to/USB/Python-3.10.5-linux-x86_64.tar.xz ~/
tar -xzvf Python-3.10.5-linux-x86_64.tar.xz
cd Python-3.10.5
./bin/python3.10 --version
```

### 가상환경 설정
```bash
./bin/python3.10 -m venv .venv
source .venv/bin/activate
```

### 오프라인 패키지 설치
```bash
pip install --no-index --find-links=packages -r requirements.txt
```

## 프로젝트 구조
```
project/
├── app/
│   ├── __init__.py
│   ├── api/                  # API 레이어
│   │   ├── __init__.py
│   │   ├── routes/           # API 엔드포인트 정의
│   │   │   ├── __init__.py
│   │   │   ├── analog.py     # 아날로그 신호 관련 엔드포인트
│   │   │   ├── digital.py    # 디지털 신호 관련 엔드포인트
│   │   │   ├── autocontrol.py # 자동 제어 관련 엔드포인트
│   │   │   └── health.py     # 시스템 상태 확인 엔드포인트
│   │   └── dependencies.py   # API 의존성 (인증, 권한 등)
│   ├── core/                 # 핵심 설정 및 유틸리티
│   │   ├── __init__.py
│   │   ├── config.py         # 애플리케이션 설정
│   │   └── logging_config.py # 로깅 설정
│   ├── models/               # 데이터 모델 정의
│   │   ├── __init__.py
│   │   └── schemas.py        # 데이터 스키마 정의
│   └── services/             # 비즈니스 로직 구현
│       ├── __init__.py
│       ├── modbus/           # Modbus 통신 서비스
│       │   ├── __init__.py
│       │   ├── client.py     # Modbus 클라이언트 구현
│       │   ├── analog.py     # 아날로그 신호 처리
│       │   ├── digital.py    # 디지털 신호 처리
│       │   └── autocontrol.py # 자동 제어 로직
│       └── exceptions.py     # 서비스 예외 정의
├── tests/                    # 테스트 코드
│   ├── __init__.py
│   ├── test_analog.py        # 아날로그 신호 테스트
│   └── test_digital.py       # 디지털 신호 테스트
├── logs/                     # 로그 디렉토리
│   └── autocontrol/          # 자동 제어 로그 (Parquet 파일)
├── .env                      # 환경 변수
├── .gitignore
├── requirements.txt          # 의존성 목록
└── README.md                 # 프로젝트 문서
```

## 애플리케이션 실행
```bash
# 개발 환경
uvicorn app.main:app --reload

# 프로덕션 환경
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 시스템 요구사항
- Python 3.10 이상
- 인터넷 연결 (패키지 설치 시) 또는 오프라인 패키지
- Modbus TCP/IP 지원 장비

## 문제 해결
- 연결 문제: 장비의 IP 주소, 포트, 슬레이브 주소가 올바르게 설정되었는지 확인
- 통신 오류: 로그 파일을 확인하여 구체적인 오류 메시지 확인
- 데이터베이스 문제: SQLite 데이터베이스 파일의 권한 및 경로 확인
- 자동 제어 문제: logs/autocontrol 디렉토리에 저장된 Parquet 로그 파일 확인

## 자동 제어 기능 설명

자동 제어 기능은 다음과 같은 특징을 가지고 있습니다:

1. **설정 관리**: 여러 기계 및 태그에 대한 목표 값을 설정하고 관리합니다.
2. **수동/자동 전환**: 자동 제어 모드를 활성화하거나 비활성화할 수 있습니다.
3. **즉시 실행**: 현재 설정으로 자동 제어를 즉시 실행할 수 있습니다.
4. **로그 기록**: 모든 제어 작업은 Parquet 파일 형식으로 로그가 저장됩니다.
5. **상태 확인**: 현재 설정된 자동 제어 설정과 마지막 실행 시간을 확인할 수 있습니다.

자동 제어 설정 예시:
```json
{
  "enabled": true,
  "machines": [
    {
      "machine_name": "machine1",
      "tags": [
        {
          "tag_name": "temperature",
          "target_value": "25"
        },
        {
          "tag_name": "pressure",
          "target_value": "100"
        }
      ]
    }
  ]
}
```

## 기계 관리 및 태그 로직 설명

### 기계 관리 기능

기계 관리 기능은 다음과 같은 작업을 수행합니다:

1. **기계 조회**: 시스템에 등록된 모든 기계 목록과 설정을 조회합니다.
2. **기계 추가**: 새로운 기계를 시스템에 등록합니다. 기계 이름, IP 주소, 포트, 슬레이브 주소를 설정합니다.
3. **기계 삭제**: 더 이상 사용하지 않는 기계를 시스템에서 제거합니다.
4. **기계 설정 조회**: 특정 기계의 상세 설정을 조회합니다.

기계 추가 요청 예시:
```json
{
  "ip": "192.168.1.100",
  "port": 502,
  "slave": 1,
  "tags": {}
}
```

### 태그 관리 기능

각 기계별로 다음과 같은 태그 관리 기능을 제공합니다:

1. **태그 목록 조회**: 특정 기계에 등록된 모든 태그를 조회합니다.
2. **태그 추가**: 새로운 태그를 기계에 등록합니다. 태그 이름, 유형, 레지스터 주소, 권한 등을 설정합니다.
3. **태그 수정**: 기존 태그의 설정을 변경합니다.
4. **태그 삭제**: 더 이상 사용하지 않는 태그를 제거합니다.
5. **태그 설정 조회**: 특정 태그의 상세 설정을 조회합니다.

태그 추가 요청 예시:
```json
{
  "tag_type": "ANALOG",
  "logical_register": "1000",
  "real_register": "1000",
  "permission": "READ_WRITE"
}
```

### 태그 값 읽기/쓰기 기능

태그 값 관리 기능은 다음과 같은 작업을 수행합니다:

1. **태그 값 읽기**: Modbus 프로토콜을 통해 기계의 특정 태그 값을 읽어옵니다.
2. **태그 값 쓰기**: Modbus 프로토콜을 통해 기계의 특정 태그에 값을 씁니다.
3. **다중 태그 값 읽기**: 한 번의 요청으로 여러 태그 값을 동시에 읽어옵니다.
4. **토글 기능**: 디지털 태그의 경우 현재 값을 반대로 토글할 수 있습니다.

태그 타입별 특징:
- **ANALOG**: 아날로그 값(정수)을 처리합니다.
- **DIGITAL**: ON/OFF 상태를 처리합니다.
- **DIGITAL_AM**: AUTO/MANUAL 모드를 처리합니다.
- **DIGITAL_RM**: REMOTE/LOCAL 모드를 처리합니다.

### 실시간 모니터링

WebSocket을 활용한 실시간 모니터링 기능:

1. **단일 기계 모니터링**: 특정 기계의 모든 태그 값을 실시간으로 모니터링합니다.
2. **다중 기계 모니터링**: 여러 기계의 태그 값을 동시에 모니터링합니다.
3. **실시간 업데이트**: 값이 변경될 때마다 클라이언트에 자동으로 업데이트됩니다.

## 라이센스
이 프로젝트는 내부 용도로 개발되었으며, 모든 권리는 인이지에 있습니다.