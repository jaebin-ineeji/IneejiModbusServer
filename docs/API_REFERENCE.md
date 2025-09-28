# API 레퍼런스

Modbus 통신 관리 시스템의 모든 API 엔드포인트에 대한 상세한 설명입니다.

## 🌐 기본 정보

- **Base URL**: `http://localhost:4444`
- **Content-Type**: `application/json`
- **API 문서**: 
  - Swagger UI: `http://localhost:4444/docs`
  - ReDoc: `http://localhost:4444/redoc`

---

## 📊 건강 상태 확인

### `GET /health`
시스템의 상태를 확인합니다.

**응답 예시:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

---

## 🏭 기계 관리

### `GET /machine`
등록된 모든 기계 목록을 조회합니다.

**응답 예시:**
```json
{
  "success": true,
  "data": [
    {
      "name": "oil_main",
      "ip_address": "192.168.1.100",
      "port": 502,
      "slave": 1
    }
  ]
}
```

### `GET /machine/{machine_name}`
특정 기계의 설정 정보를 조회합니다.

**파라미터:**
- `machine_name` (path): 기계 이름

**응답 예시:**
```json
{
  "success": true,
  "data": {
    "name": "oil_main",
    "ip_address": "192.168.1.100", 
    "port": 502,
    "slave": 1,
    "tags": {
      "pv": {
        "tag_type": "ANALOG",
        "logical_register": "1000",
        "real_register": "1000", 
        "permission": "READ_WRITE"
      }
    }
  }
}
```

### `POST /machine/{machine_name}`
새로운 기계를 등록합니다.

**파라미터:**
- `machine_name` (path): 등록할 기계 이름

**요청 본문:**
```json
{
  "ip": "192.168.1.100",
  "port": 502,
  "slave": 1,
  "tags": {
    "pv": {
      "tag_type": "ANALOG",
      "logical_register": "1000",
      "real_register": "1000",
      "permission": "READ_WRITE"
    }
  }
}
```

**응답 예시:**
```json
{
  "success": true,
  "message": "기계가 성공적으로 추가되었습니다"
}
```

### `DELETE /machine/{machine_name}`
기계를 삭제합니다.

**파라미터:**
- `machine_name` (path): 삭제할 기계 이름

**응답 예시:**
```json
{
  "success": true,
  "message": "기계가 성공적으로 삭제되었습니다"
}
```

---

## 🏷 태그 관리

### `GET /machine/{machine_name}/tags`
특정 기계의 모든 태그를 조회합니다.

**파라미터:**
- `machine_name` (path): 기계 이름

**응답 예시:**
```json
{
  "success": true,
  "data": {
    "pv": {
      "tag_type": "ANALOG",
      "logical_register": "1000",
      "real_register": "1000",
      "permission": "READ_WRITE"
    },
    "sv": {
      "tag_type": "ANALOG", 
      "logical_register": "1001",
      "real_register": "1001",
      "permission": "READ_WRITE"
    }
  }
}
```

### `GET /machine/{machine_name}/tags/{tag_name}/config`
특정 태그의 설정을 조회합니다.

**파라미터:**
- `machine_name` (path): 기계 이름
- `tag_name` (path): 태그 이름

**응답 예시:**
```json
{
  "success": true,
  "data": {
    "tag_type": "ANALOG",
    "logical_register": "1000",
    "real_register": "1000",
    "permission": "READ_WRITE"
  }
}
```

### `POST /machine/{machine_name}/tags`
새로운 태그를 추가합니다.

**파라미터:**
- `machine_name` (path): 기계 이름

**요청 본문:**
```json
{
  "tag_name": "temperature",
  "tag_type": "ANALOG",
  "logical_register": "1002",
  "real_register": "1002",
  "permission": "READ_WRITE"
}
```

**응답 예시:**
```json
{
  "success": true,
  "message": "태그가 성공적으로 추가되었습니다"
}
```

### `PUT /machine/{machine_name}/tags/{tag_name}`
태그 설정을 업데이트합니다.

**파라미터:**
- `machine_name` (path): 기계 이름  
- `tag_name` (path): 태그 이름

**요청 본문:**
```json
{
  "tag_type": "ANALOG",
  "logical_register": "1002",
  "real_register": "1002", 
  "permission": "READ_ONLY"
}
```

**응답 예시:**
```json
{
  "success": true,
  "message": "태그 설정이 성공적으로 업데이트되었습니다"
}
```

### `DELETE /machine/{machine_name}/tags/{tag_name}`
태그를 삭제합니다.

**파라미터:**
- `machine_name` (path): 기계 이름
- `tag_name` (path): 태그 이름

**응답 예시:**
```json
{
  "success": true,
  "message": "태그가 성공적으로 삭제되었습니다"
}
```

---

## 📖 태그 값 읽기/쓰기

### `GET /machine/{machine_name}/tags/{tag_name}`
특정 태그의 현재 값을 읽어옵니다.

**파라미터:**
- `machine_name` (path): 기계 이름
- `tag_name` (path): 태그 이름

**응답 예시:**
```json
{
  "success": true,
  "data": {
    "tag_name": "pv",
    "value": "250",
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

### `POST /machine/{machine_name}/tags/{tag_name}`
특정 태그에 값을 씁니다.

**파라미터:**
- `machine_name` (path): 기계 이름
- `tag_name` (path): 태그 이름

**요청 본문 (일반 쓰기):**
```json
{
  "value": "300"
}
```

**요청 본문 (디지털 토글):**
```json
{
  "action": "toggle"
}
```

**응답 예시:**
```json
{
  "success": true,
  "message": "값이 성공적으로 설정되었습니다",
  "data": {
    "tag_name": "pv",
    "old_value": "250",
    "new_value": "300"
  }
}
```

### `GET /machine/{machine_name}/values`
선택한 여러 태그의 값을 한 번에 조회합니다.

**파라미터:**
- `machine_name` (path): 기계 이름
- `tag_names` (query): 쉼표로 구분된 태그 이름들

**요청 예시:**
```
GET /machine/oil_main/values?tag_names=pv,sv,temperature
```

**응답 예시:**
```json
{
  "success": true,
  "data": {
    "pv": "250",
    "sv": "300", 
    "temperature": "25.5"
  }
}
```

---

## 🔄 자동 제어 관리

### `POST /autocontrol`
자동 제어 설정을 구성합니다.

**요청 본문:**
```json
{
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
    }
  ]
}
```

**응답 예시:**
```json
{
  "success": true,
  "message": "자동 제어 설정이 저장되었습니다"
}
```

### `POST /autocontrol/execute`
자동 제어를 즉시 실행합니다.

**요청 본문 (기존 설정 사용):**
```json
{}
```

**요청 본문 (새 설정으로 실행):**
```json
{
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
}
```

**응답 예시:**
```json
{
  "success": true,
  "message": "자동 제어가 실행되었습니다",
  "data": {
    "executed_at": "2024-01-01T12:00:00Z",
    "results": [
      {
        "machine": "oil_main",
        "tag": "pv", 
        "status": "success",
        "value": "280"
      }
    ]
  }
}
```

### `PUT /autocontrol/toggle`
자동 제어 모드를 활성화/비활성화합니다.

**요청 본문:**
```json
{
  "enabled": true
}
```

**응답 예시:**
```json
{
  "success": true,
  "message": "자동 제어가 활성화되었습니다"
}
```

### `GET /autocontrol`
현재 자동 제어 상태 및 설정을 조회합니다.

**응답 예시:**
```json
{
  "success": true,
  "data": {
    "enabled": true,
    "last_execution": "2024-01-01T11:30:00Z",
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

---

## 🌐 실시간 모니터링 (WebSocket)

### `WebSocket /machine/{machine_name}/ws`
특정 기계의 태그 값을 실시간으로 모니터링합니다.

**연결 예시 (JavaScript):**
```javascript
const ws = new WebSocket('ws://localhost:4444/machine/oil_main/ws');

ws.onmessage = function(event) {
  const data = JSON.parse(event.data);
  console.log('실시간 데이터:', data);
};
```

**수신 데이터 예시:**
```json
{
  "machine_name": "oil_main",
  "timestamp": "2024-01-01T12:00:00Z",
  "tags": {
    "pv": "250",
    "sv": "300",
    "temperature": "25.5"
  }
}
```

### `WebSocket /machine/ws`
모든 기계의 태그 값을 실시간으로 모니터링합니다.

**연결 예시 (JavaScript):**
```javascript
const ws = new WebSocket('ws://localhost:4444/machine/ws');

ws.onmessage = function(event) {
  const data = JSON.parse(event.data);
  console.log('전체 실시간 데이터:', data);
};
```

**수신 데이터 예시:**
```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "machines": {
    "oil_main": {
      "pv": "250",
      "sv": "300"
    },
    "oxy_main": {
      "pv": "150", 
      "sv": "200"
    }
  }
}
```

---

## 📋 태그 타입별 특징

### ANALOG (아날로그)
- 숫자 값을 처리 (정수, 실수)
- 읽기/쓰기 모두 지원
- 예시: 온도, 압력, 유량 등

### DIGITAL (디지털) 
- ON/OFF 상태 처리 (0 또는 1)
- 토글 기능 지원 (`{"action": "toggle"}`)
- 예시: 펌프 On/Off, 밸브 Open/Close

### DIGITAL_AM (Auto/Manual)
- AUTO 또는 MANUAL 모드 처리
- 값: AUTO = 1, MANUAL = 0

### DIGITAL_RM (Remote/Local)
- REMOTE 또는 LOCAL 모드 처리  
- 값: REMOTE = 1, LOCAL = 0

---

## ⚠️ 에러 응답

모든 API 엔드포인트에서 오류 발생 시 다음과 같은 형태로 응답합니다:

```json
{
  "success": false,
  "message": "오류 설명",
  "error_code": "ERROR_CODE",
  "details": "상세 오류 정보 (선택적)"
}
```

### 주요 에러 코드

- **400 Bad Request**: 잘못된 요청 파라미터
- **404 Not Found**: 존재하지 않는 기계 또는 태그
- **500 Internal Server Error**: 서버 내부 오류
- **503 Service Unavailable**: Modbus 통신 오류

---

## 📝 사용 팁

1. **배치 작업**: 여러 태그 값을 한 번에 읽을 때는 `/values` 엔드포인트 사용
2. **실시간 모니터링**: 지속적인 데이터 모니터링이 필요한 경우 WebSocket 사용
3. **자동 제어**: 정기적인 제어 작업은 자동 제어 시스템 활용
4. **오류 처리**: API 호출 시 항상 `success` 필드를 먼저 확인
