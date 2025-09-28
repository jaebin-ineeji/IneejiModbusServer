import sqlite3
import pandas as pd
from datetime import datetime, timedelta

DB_NAME = 'modbus_data.db'
DB_FILE_ROOT = f'/home/dongwon/IneejiModbusTester/{DB_NAME}'

def _format_machine_name(name):
    """
    기계 이름 포맷팅 함수
    
    Parameters:
    - name: 원래 기계 이름 (대문자, 언더스코어 포함)
    
    Returns:
    - str: 포맷팅된 기계 이름
    """
    # 특수 케이스 처리
    if 'ARCH_' in name:
        # ARCH_3 -> ARCH #3
        number = name.split('_')[1]
        return f"ARCH #{number}"
    else:
        # OIL_MAIN -> OIL MAIN
        return name.replace('_', ' ')

def get_modbus_data(value_type='all', hours=1, start_time=None, end_time=None):
    """
    특정 타입의 기계 데이터를 가져오는 함수
    
    Parameters:
    - value_type: 'pv', 'sv', 'all' 중 하나 (기본값: 'all')
    - hours: 몇 시간 전 데이터부터 가져올지 (기본값: 1, start_time이 지정된 경우 무시됨)
    - start_time: 시작 시간 (datetime 객체 또는 문자열 'YYYY-MM-DD HH:MM:SS' 형식, 기본값: None)
    - end_time: 종료 시간 (datetime 객체 또는 문자열 'YYYY-MM-DD HH:MM:SS' 형식, 기본값: 현재 시간)
    
    Returns:
    - DataFrame: 조회된 데이터
    """
    # 현재 시간과 지정된 시간 전 계산
    now = datetime.now()
    
    # end_time 처리
    if end_time is None:
        end_time = now
    elif isinstance(end_time, str):
        end_time = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
    
    # start_time 처리
    if start_time is None:
        start_time = end_time - timedelta(hours=hours)
    elif isinstance(start_time, str):
        start_time = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
    
    # 시간 문자열로 변환
    start_time_str = start_time.strftime('%Y-%m-%d %H:%M:%S')
    end_time_str = end_time.strftime('%Y-%m-%d %H:%M:%S')

    # 데이터베이스 연결
    conn = sqlite3.connect(DB_FILE_ROOT)
    
    # SQL 쿼리 실행
    if value_type.lower() == 'pv':
        column_list = "timestamp, " + ", ".join([col for col in ['oil_main_pv', 'oil_1l_pv', 'oil_2l_pv', 'oil_3l_pv', 'oil_4l_pv', 'oil_5l_pv', 'oil_1r_pv', 'oil_2r_pv', 'oil_3r_pv', 'oil_4r_pv', 'oxy_main_pv', 'oxy_1l_pv', 'oxy_2l_pv', 'oxy_3l_pv', 'oxy_4l_pv', 'oxy_5l_pv', 'oxy_1r_pv', 'oxy_2r_pv', 'oxy_3r_pv', 'oxy_4r_pv', 'arch_3_pv']])
        query = f"""
        SELECT {column_list} FROM {DB_NAME} 
        WHERE timestamp BETWEEN ? AND ?
        ORDER BY timestamp
        """
    elif value_type.lower() == 'sv':
        column_list = "timestamp, " + ", ".join([col for col in ['oil_main_sv', 'oil_1l_sv', 'oil_2l_sv', 'oil_3l_sv', 'oil_4l_sv', 'oil_5l_sv', 'oil_1r_sv', 'oil_2r_sv', 'oil_3r_sv', 'oil_4r_sv', 'oxy_main_sv', 'oxy_1l_sv', 'oxy_2l_sv', 'oxy_3l_sv', 'oxy_4l_sv', 'oxy_5l_sv', 'oxy_1r_sv', 'oxy_2r_sv', 'oxy_3r_sv', 'oxy_4r_sv', 'arch_3_sv']])
        query = f"""
        SELECT {column_list} FROM {DB_NAME} 
        WHERE timestamp BETWEEN ? AND ?
        ORDER BY timestamp
        """
    else:
        query = f"""
        SELECT * FROM {DB_NAME} 
        WHERE timestamp BETWEEN ? AND ?
        ORDER BY timestamp
        """

    # 결과를 DataFrame으로 읽기
    df = pd.read_sql_query(query, conn, params=(start_time_str, end_time_str))
    
    # 데이터베이스 연결 종료
    conn.close()
    
    # timestamp 컬럼을 datetime 형식으로 변환
    df['Date'] = pd.to_datetime(df['timestamp'])
    df.drop(columns=['timestamp'], inplace=True)

    # timestamp 컬럼을 인덱스로 설정
    df.set_index('Date', inplace=True)
    
    # value_type에 따라 컬럼 필터링
    if value_type.lower() == 'pv':
        df = df.filter(like='_pv')
    elif value_type.lower() == 'sv':
        df = df.filter(like='_sv')
    
    # 컬럼명 변경
    new_columns = {}
    for col in df.columns:
        if value_type.lower() == 'all':
            # all 일 때는 _pv, _sv 유지하고 앞부분만 대문자로 변환 후 포맷팅
            if '_pv' in col:
                machine_name = col.replace('_pv', '')
                formatted_name = _format_machine_name(machine_name.upper())
                new_name = formatted_name + ' PV'
            elif '_sv' in col:
                machine_name = col.replace('_sv', '')
                formatted_name = _format_machine_name(machine_name.upper())
                new_name = formatted_name + ' SV'
            else:
                new_name = _format_machine_name(col.upper())
        else:
            # pv나 sv만 선택했을 때는 _pv, _sv 제거하고 전체 대문자로 변환 후 포맷팅
            if '_pv' in col:
                machine_name = col.replace('_pv', '')
                new_name = _format_machine_name(machine_name.upper())
            elif '_sv' in col:
                machine_name = col.replace('_sv', '')
                new_name = _format_machine_name(machine_name.upper())
            else:
                new_name = _format_machine_name(col.upper())
        new_columns[col] = new_name
    
    # 컬럼명 변경 적용
    df = df.rename(columns=new_columns)
    
    return df

# 사용 예시
# pv만 조회하기
pv_data = get_modbus_data('pv', hours=1)
print("pv 데이터:")
print(pv_data)

