# 자동 제어 시스템 가이드

Modbus 통신 관리 시스템의 자동 제어 기능에 대한 상세한 사용 가이드입니다.

## 📖 개요

자동 제어 시스템은 사전 정의된 설정에 따라 여러 기계의 태그 값을 자동으로 설정하는 기능입니다. 스케줄 기반으로 실행되며, 모든 제어 작업은 상세한 로그로 기록됩니다.

### 주요 특징
- **다중 기계 제어**: 여러 기계를 동시에 제어
- **태그별 목표 값**: 기계별로 여러 태그의 목표 값 설정 가능
- **실행 모드**: 수동 실행 및 활성화/비활성화 토글
- **상세 로깅**: Parquet 파일 형식으로 모든 제어 작업 기록
- **에러 처리**: 개별 태그 제어 실패가 전체 작업에 영향을 주지 않음

## 🛠 기본 사용법

### 1. 자동 제어 설정 구성

**API 엔드포인트**: `POST /autocontrol`

```bash
curl -X POST "http://localhost:4444/autocontrol" \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": true,
    "machines": [
      {
        "machine_name": "oil_main",
        "tags": [
          {
            "tag_name": "pv",
            "target_value": "250"
          },
          {
            "tag_name": "sv", 
            "target_value": "300"
          }
        ]
      },
      {
        "machine_name": "oxy_main",
        "tags": [
          {
            "tag_name": "pv",
            "target_value": "150"
          }
        ]
      }
    ]
  }'
```

**Python 예시**:
```python
import requests

config = {
    "enabled": True,
    "machines": [
        {
            "machine_name": "oil_main",
            "tags": [
                {"tag_name": "pv", "target_value": "250"},
                {"tag_name": "sv", "target_value": "300"}
            ]
        }
    ]
}

response = requests.post("http://localhost:4444/autocontrol", json=config)
print(response.json())
```

### 2. 즉시 실행

**API 엔드포인트**: `POST /autocontrol/execute`

#### 기존 설정으로 실행
```bash
curl -X POST "http://localhost:4444/autocontrol/execute" \
  -H "Content-Type: application/json" \
  -d '{}'
```

#### 새로운 설정으로 즉시 실행
```bash
curl -X POST "http://localhost:4444/autocontrol/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "machines": [
      {
        "machine_name": "oil_main",
        "tags": [
          {
            "tag_name": "pv",
            "target_value": "280"
          }
        ]
      }
    ]
  }'
```

### 3. 자동 제어 활성화/비활성화

**API 엔드포인트**: `PUT /autocontrol/toggle`

```bash
# 활성화
curl -X PUT "http://localhost:4444/autocontrol/toggle" \
  -H "Content-Type: application/json" \
  -d '{"enabled": true}'

# 비활성화  
curl -X PUT "http://localhost:4444/autocontrol/toggle" \
  -H "Content-Type: application/json" \
  -d '{"enabled": false}'
```

### 4. 현재 상태 조회

**API 엔드포인트**: `GET /autocontrol`

```bash
curl -X GET "http://localhost:4444/autocontrol"
```

**응답 예시**:
```json
{
  "success": true,
  "data": {
    "enabled": true,
    "last_execution": "2024-01-01T12:00:00Z",
    "machines": [
      {
        "machine_name": "oil_main",
        "tags": [
          {
            "tag_name": "pv",
            "target_value": "250"
          }
        ]
      }
    ]
  }
}
```

## 📋 상세 설정 옵션

### 설정 스키마

```json
{
  "enabled": boolean,      // 자동 제어 활성화 여부
  "machines": [            // 제어할 기계 목록
    {
      "machine_name": "string",  // 기계 이름
      "tags": [                  // 제어할 태그 목록
        {
          "tag_name": "string",     // 태그 이름
          "target_value": "string"  // 목표 값 (문자열로 전달)
        }
      ]
    }
  ]
}
```

### 태그 타입별 목표 값

#### ANALOG (아날로그)
```json
{
  "tag_name": "temperature",
  "target_value": "25.5"    // 숫자 값을 문자열로 전달
}
```

#### DIGITAL (디지털)
```json
{
  "tag_name": "pump_status",
  "target_value": "ON"      // "ON", "OFF", "1", "0" 가능
}
```

#### DIGITAL_AM (Auto/Manual)
```json
{
  "tag_name": "control_mode",
  "target_value": "AUTO"    // "AUTO", "MANUAL" 가능
}
```

#### DIGITAL_RM (Remote/Local)
```json
{
  "tag_name": "operation_mode", 
  "target_value": "REMOTE"  // "REMOTE", "LOCAL" 가능
}
```

## 📊 로그 시스템

### 로그 파일 위치
자동 제어 실행 시마다 다음 위치에 Parquet 파일이 생성됩니다:
```
logs/autocontrol/autocontrol_YYYYMMDD_HHMMSS.parquet
```

### 로그 데이터 구조

```python
# Pandas DataFrame 형태로 저장
{
    'timestamp': '2024-01-01 12:00:00',
    'machine_name': 'oil_main',
    'tag_name': 'pv',
    'target_value': '250',
    'status': 'success',  # 'success' 또는 'error'
    'error_message': None  # 에러 시에만 메시지 포함
}
```

### 로그 조회 예시

#### Python으로 로그 분석
```python
import pandas as pd
import glob
import os

# 최신 로그 파일 찾기
log_files = glob.glob('logs/autocontrol/*.parquet')
latest_log = max(log_files, key=os.path.getctime)

# 로그 데이터 읽기
df = pd.read_parquet(latest_log)

# 성공/실패 통계
print(df['status'].value_counts())

# 기계별 결과 확인
print(df.groupby('machine_name')['status'].value_counts())

# 실패한 제어 작업 확인
failed_operations = df[df['status'] == 'error']
print(failed_operations[['machine_name', 'tag_name', 'error_message']])
```

#### CLI로 로그 확인
```bash
# 로그 파일 목록 확인
ls -la logs/autocontrol/

# 최신 10개 로그 파일
ls -t logs/autocontrol/*.parquet | head -10

# Python으로 로그 내용 간단 확인
python -c "
import pandas as pd
import sys
df = pd.read_parquet(sys.argv[1])
print(df.to_string())
" logs/autocontrol/autocontrol_20240101_120000.parquet
```

## 🔄 실행 흐름

### 자동 제어 실행 과정

```
1. 설정 검증
   ├── 기계 존재 여부 확인
   ├── 태그 존재 여부 확인
   └── 권한 확인 (READ_WRITE, WRITE_ONLY)

2. 개별 제어 실행
   ├── 기계별 순차 처리
   ├── 태그별 병렬 처리
   └── 에러 발생 시 개별 기록

3. 결과 기록
   ├── 성공/실패 상태 기록
   ├── 에러 메시지 기록
   └── Parquet 파일 저장

4. 응답 반환
   ├── 전체 실행 결과
   ├── 개별 태그 결과
   └── 실행 시간 정보
```

### 에러 처리 로직

```python
# 예시: 개별 태그 제어 실패가 전체에 영향을 주지 않음
for machine in machines:
    for tag in machine.tags:
        try:
            result = control_tag(machine, tag)
            log_success(machine, tag, result)
        except Exception as e:
            log_error(machine, tag, str(e))
            continue  # 다음 태그 계속 처리
```

## 📈 고급 사용 예시

### 1. 복합 제어 시나리오

온도 제어 시스템에서 여러 기계를 동시에 설정:

```json
{
  "enabled": true,
  "machines": [
    {
      "machine_name": "oil_main",
      "tags": [
        {"tag_name": "pv", "target_value": "250"},
        {"tag_name": "sv", "target_value": "300"},
        {"tag_name": "pump_control", "target_value": "AUTO"}
      ]
    },
    {
      "machine_name": "oil_1l", 
      "tags": [
        {"tag_name": "pv", "target_value": "180"},
        {"tag_name": "sv", "target_value": "200"}
      ]
    },
    {
      "machine_name": "oxy_main",
      "tags": [
        {"tag_name": "pv", "target_value": "150"},
        {"tag_name": "operation_mode", "target_value": "REMOTE"}
      ]
    }
  ]
}
```

### 2. 조건부 실행 (외부 스크립트)

외부 조건에 따른 자동 제어 실행:

```python
import requests
import datetime

def should_execute_control():
    # 시간, 온도, 기타 조건 확인
    current_hour = datetime.datetime.now().hour
    return 8 <= current_hour <= 18  # 업무시간에만 실행

def execute_daytime_control():
    config = {
        "machines": [
            {
                "machine_name": "oil_main",
                "tags": [{"tag_name": "pv", "target_value": "280"}]
            }
        ]
    }
    
    if should_execute_control():
        response = requests.post(
            "http://localhost:4444/autocontrol/execute",
            json=config
        )
        return response.json()

# 스케줄러로 주기적 실행
# crontab: 0 */2 * * * python execute_control.py
```

### 3. 배치 제어 스크립트

여러 설정을 순차적으로 적용:

```python
import requests
import time

def batch_control():
    # 단계 1: 초기 설정
    config1 = {
        "machines": [
            {
                "machine_name": "oil_main",
                "tags": [{"tag_name": "pv", "target_value": "200"}]
            }
        ]
    }
    
    # 단계 2: 중간 설정 (5분 후)
    config2 = {
        "machines": [
            {
                "machine_name": "oil_main", 
                "tags": [{"tag_name": "pv", "target_value": "250"}]
            }
        ]
    }
    
    # 단계 3: 최종 설정 (10분 후)
    config3 = {
        "machines": [
            {
                "machine_name": "oil_main",
                "tags": [{"tag_name": "pv", "target_value": "300"}]
            }
        ]
    }
    
    # 순차 실행
    for i, config in enumerate([config1, config2, config3], 1):
        print(f"단계 {i} 실행...")
        response = requests.post(
            "http://localhost:4444/autocontrol/execute",
            json=config
        )
        print(f"결과: {response.json()}")
        
        if i < 3:  # 마지막 단계가 아니면 대기
            time.sleep(300)  # 5분 대기

if __name__ == "__main__":
    batch_control()
```

## 🚨 모니터링 및 알림

### 실행 결과 모니터링

```python
import requests
import pandas as pd
import glob

def check_recent_executions():
    # 최근 로그 파일들 확인
    log_files = glob.glob('logs/autocontrol/*.parquet')
    recent_logs = sorted(log_files, key=os.path.getctime, reverse=True)[:5]
    
    for log_file in recent_logs:
        df = pd.read_parquet(log_file)
        error_count = len(df[df['status'] == 'error'])
        
        if error_count > 0:
            print(f"⚠️  {log_file}에서 {error_count}개 에러 발견")
            print(df[df['status'] == 'error'][['machine_name', 'tag_name', 'error_message']])
        else:
            print(f"✅ {log_file} - 모든 제어 작업 성공")

def send_alert_if_needed():
    # 최근 실행 상태 확인
    response = requests.get("http://localhost:4444/autocontrol")
    data = response.json()
    
    if not data.get('success'):
        # 알림 전송 (이메일, Slack, SMS 등)
        send_notification("자동 제어 시스템 오류 발생")

# 주기적 실행 (예: cron job)
if __name__ == "__main__":
    check_recent_executions()
    send_alert_if_needed()
```

## ⚠️ 주의사항 및 모범 사례

### 1. 안전 고려사항

- **테스트 환경**: 프로덕션 환경에 적용하기 전 반드시 테스트
- **단계적 적용**: 한 번에 모든 기계를 제어하지 말고 단계적으로 적용
- **백업 계획**: 원래 설정값을 기록하고 롤백 계획 준비
- **모니터링**: 제어 후 시스템 상태를 지속적으로 모니터링

### 2. 성능 최적화

- **배치 크기**: 한 번에 너무 많은 태그를 제어하지 않도록 주의
- **실행 간격**: 너무 빈번한 실행은 시스템에 부하를 줄 수 있음
- **로그 관리**: 오래된 로그 파일은 정기적으로 정리

### 3. 모범 사례

```python
# ✅ 좋은 예: 단계적 제어
def gradual_temperature_control():
    current_temp = get_current_temperature()
    target_temp = 300
    step_size = 25
    
    while abs(current_temp - target_temp) > step_size:
        if current_temp < target_temp:
            next_temp = min(current_temp + step_size, target_temp)
        else:
            next_temp = max(current_temp - step_size, target_temp)
            
        execute_control(next_temp)
        time.sleep(180)  # 3분 대기
        current_temp = get_current_temperature()

# ❌ 나쁜 예: 급격한 변경
def bad_temperature_control():
    execute_control(300)  # 현재 온도와 관계없이 즉시 300도로 설정
```

### 4. 에러 복구

```python
def robust_control_execution(config, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.post(
                "http://localhost:4444/autocontrol/execute",
                json=config,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    return result
                    
        except requests.RequestException as e:
            print(f"시도 {attempt + 1} 실패: {e}")
            if attempt < max_retries - 1:
                time.sleep(5)  # 5초 대기 후 재시도
                
    raise Exception("최대 재시도 횟수 초과")
```

## 🔧 문제 해결

### 일반적인 문제들

#### 1. 제어 명령이 실행되지 않음
```bash
# 자동 제어 상태 확인
curl http://localhost:4444/autocontrol

# 응답에서 "enabled": false인 경우
curl -X PUT "http://localhost:4444/autocontrol/toggle" \
  -H "Content-Type: application/json" \
  -d '{"enabled": true}'
```

#### 2. 특정 태그 제어 실패
- 태그 권한 확인 (READ_WRITE 또는 WRITE_ONLY)
- Modbus 연결 상태 확인
- 로그 파일에서 상세 에러 메시지 확인

#### 3. 로그 파일이 생성되지 않음
```bash
# 로그 디렉토리 권한 확인
ls -la logs/
mkdir -p logs/autocontrol
chmod 755 logs/autocontrol
```

이 가이드를 참고하여 안전하고 효율적인 자동 제어 시스템을 구축하고 운영할 수 있습니다.
