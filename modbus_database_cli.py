import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.config import settings

# SQLite 데이터베이스 파일 경로
DB_NAME = settings.SAVER_DB_NAME
DB_FILE_ROOT = f'{settings.PROJECT_DIR}/{DB_NAME}.db'

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


if __name__ == "__main__":
    import sys
    import argparse
    

    # 인자가 없는 경우 대화형 입력 모드로 전환
    if len(sys.argv) == 1:
        print("\033[1;36m모드버스 데이터 조회 프로그램 - 대화형 모드\033[0m")
        
        # 값 타입 입력
        while True:
            value_type = input("\033[1;33m조회할 값 타입 (pv, sv, all) [기본값: all]: \033[0m").strip().lower()
            if value_type == "":
                value_type = "all"
                break
            if value_type in ['pv', 'sv', 'all']:
                break
            print("잘못된 입력입니다. 'pv', 'sv', 'all' 중에서 입력해주세요.")
        
        # 시간 입력
        while True:
            try:
                hours_input = input("\033[1;33m몇 시간 전 데이터부터 가져올지 [기본값: 1]: \033[0m").strip()
                hours = 1 if hours_input == "" else int(hours_input)
                break
            except ValueError:
                print("숫자를 입력해주세요.")
        
        # 시작 시간 입력
        start_time = input("\033[1;33m시작 시간 (YYYY-MM-DD HH:MM:SS) [미입력 시 hours 시간 전]: \033[0m").strip()
        start_time = None if start_time == "" else start_time
        
        # 종료 시간 입력
        end_time = input("\033[1;33m종료 시간 (YYYY-MM-DD HH:MM:SS) [미입력 시 현재 시간]: \033[0m").strip()
        end_time = None if end_time == "" else end_time
        
        # 페이지 크기 입력
        while True:
            try:
                page_size_input = input("\033[1;33m한 페이지에 표시할 행 수 [기본값: 10]: \033[0m").strip()
                page_size = 10 if page_size_input == "" else int(page_size_input)
                break
            except ValueError:
                print("숫자를 입력해주세요.")
                
        # 인수에 따라 함수 호출
        result = get_modbus_data(
            value_type=value_type,
            hours=hours,
            start_time=start_time,
            end_time=end_time
        )
    else: 
        # 기존 명령행 인자 처리 방식
        parser = argparse.ArgumentParser(description='모드버스 데이터 조회 프로그램')
        parser.add_argument('type', type=str, choices=['pv', 'sv', 'all'], nargs='?', default='all',
                            help='조회할 값 타입 (pv, sv, all)')
        parser.add_argument('hours', type=float, nargs='?', default=1,
                            help='몇 시간 전 데이터부터 가져올지')
        parser.add_argument('start', type=str, nargs='?', default=None,
                            help='시작 시간 (YYYY-MM-DD HH:MM:SS 형식)')
        parser.add_argument('end', type=str, nargs='?', default=None,
                            help='종료 시간 (YYYY-MM-DD HH:MM:SS 형식)')
        parser.add_argument('page_size', type=int, nargs='?', default=10,
                            help='한 페이지에 표시할 행 수')
        
        # 기존 명령행 인자 형식도 계속 지원
        parser.add_argument('--type', type=str, choices=['pv', 'sv', 'all'], dest='type_opt',
                            help='조회할 값 타입 (pv, sv, all)')
        parser.add_argument('--hours', type=float, dest='hours_opt',
                            help='몇 시간 전 데이터부터 가져올지')
        parser.add_argument('--start', type=str, dest='start_opt',
                            help='시작 시간 (YYYY-MM-DD HH:MM:SS 형식)')
        parser.add_argument('--end', type=str, dest='end_opt',
                            help='종료 시간 (YYYY-MM-DD HH:MM:SS 형식)')
        parser.add_argument('--page-size', type=int, dest='page_size_opt',
                            help='한 페이지에 표시할 행 수')
        
        args = parser.parse_args()
        
        # 위치 인자와 옵션 인자 중 옵션 인자가 우선함
        value_type = args.type_opt if args.type_opt is not None else args.type
        hours = args.hours_opt if args.hours_opt is not None else args.hours
        start_time = args.start_opt if args.start_opt is not None else args.start
        end_time = args.end_opt if args.end_opt is not None else args.end
        page_size = args.page_size_opt if args.page_size_opt is not None else args.page_size
        
        # 인수에 따라 함수 호출
        result = get_modbus_data(
            value_type=value_type,
            hours=hours,
            start_time=start_time,
            end_time=end_time
        )
    
    # 페이지 탐색 기능 구현
    total_rows = len(result)
    total_pages = (total_rows + page_size - 1) // page_size
    current_page = 1
    
    try:
        from tabulate import tabulate
    
        while True:
            # 화면 지우기
            os.system('cls' if os.name == 'nt' else 'clear')
            
            # 현재 페이지 정보 출력
            print(f"\033[1;36m{value_type} 데이터 (페이지 {current_page}/{total_pages}, 총 {total_rows}행)\033[0m")
            
            # 현재 페이지 데이터 계산
            start_idx = (current_page - 1) * page_size
            end_idx = min(start_idx + page_size, total_rows)
            
            # 현재 페이지 데이터 출력 (인덱스 포함)
            page_data = result.iloc[start_idx:end_idx]
            print(tabulate(page_data.reset_index().values.tolist(), 
                        headers=list(page_data.reset_index().columns), 
                        tablefmt='fancy_grid', floatfmt='.1f'))
            
            # 명령어 안내
            print("\n\033[1;33m명령어: [ n ]다음 페이지, [ b ]이전 페이지, [ q ]종료, [ g 숫자 ]특정 페이지로 이동\033[0m")
            
            # 사용자 입력 받기
            cmd = input("> ").lower().strip()
            
            if cmd == 'q':
                break
            elif cmd == 'n' and current_page < total_pages:
                current_page += 1
            elif cmd == 'b' and current_page > 1:
                current_page -= 1
            elif cmd.startswith('g '):
                try:
                    page_num = int(cmd[2:])
                    if 1 <= page_num <= total_pages:
                        current_page = page_num
                except ValueError:
                    pass
    
    except ImportError:
        print("tabulate 패키지가 설치되어 있지 않습니다.")
        print("설치하려면: pip install tabulate")
        print("\n기본 출력:")
        print(result)
    except KeyboardInterrupt:
        print("\n프로그램을 종료합니다.")