#!/bin/bash

# Modbus 데이터 수집기 자동 시작 스크립트
# 작성자: 자동 생성
# 목적: 시스템 재부팅 시 데이터 수집기를 자동으로 시작

# 스크립트가 있는 디렉토리 찾기
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# .env 파일에서 환경변수 로드 (스크립트와 같은 디렉토리에서)
if [ -f "$SCRIPT_DIR/.env" ]; then
    export $(cat "$SCRIPT_DIR/.env" | sed 's/#.*//g' | xargs)
    echo "$(date '+%Y-%m-%d %H:%M:%S') - .env 파일 로드됨: $SCRIPT_DIR/.env"
else
    echo "$(date '+%Y-%m-%d %H:%M:%S') - .env 파일을 찾을 수 없습니다: $SCRIPT_DIR/.env"
fi

# 프로젝트 경로 설정 (.env에서 가져오거나 스크립트 디렉토리 사용)
PROJECT_DIR=${PROJECT_DIR:-"$SCRIPT_DIR"}

echo "$(date '+%Y-%m-%d %H:%M:%S') - Modbus 데이터 수집기 시작 중..."

# 프로젝트 디렉토리로 이동
cd "$PROJECT_DIR"

# Python 가상환경이 있다면 활성화 (선택사항)
source .venv/bin/activate

# 기존 실행 중인 saver 확인 및 종료
PID=$(ps aux | grep "modbus_database_saver.py" | grep -v grep | awk '{print $2}')
if [ ! -z "$PID" ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - 기존 데이터 수집기 프로세스($PID) 종료 중..."
    kill -9 $PID
    sleep 2
fi

# 서버가 시작될 때까지 대기 (최대 30초)
echo "$(date '+%Y-%m-%d %H:%M:%S') - 서버 시작 대기 중..."
for i in {1..30}; do
    if curl -s http://localhost:4444/health > /dev/null 2>&1; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') - 서버 연결 확인됨 (${i}초 후)"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') - 경고: 서버 연결 실패, 데이터 수집기 시작을 계속 진행"
    fi
    sleep 1
done

# 데이터 수집기 시작 (로그는 애플리케이션 자체에서 관리)
echo "$(date '+%Y-%m-%d %H:%M:%S') - 데이터 수집기 실행 시작"
nohup python modbus_database_saver.py > /dev/null 2>&1 &

# 새 프로세스 ID 기록
NEW_PID=$!
echo "$(date '+%Y-%m-%d %H:%M:%S') - 데이터 수집기가 PID $NEW_PID로 시작되었습니다"

# PID 파일에 저장 (종료 시 사용)
echo $NEW_PID > "$PROJECT_DIR/saver.pid"

echo "$(date '+%Y-%m-%d %H:%M:%S') - 데이터 수집기 시작 완료 (상세 로그: $PROJECT_DIR/logs/dblog/)"
