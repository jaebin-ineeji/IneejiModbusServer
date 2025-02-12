from pymodbus.client import ModbusTcpClient


def set_digital_status_bit(
    host: str,
    port: int,
    register_address: int,
    bit_position: int,
    slave: int,
    new_state: bool,
    type: int,
) -> str:
    """
    특정 비트 위치의 값을 변경
    :param host: 호스트 주소 ex) host = "172.30.1.97"
    :param register_address: 레지스터 주소 ex) dev_addr = 42008
    :param bit_position: 비트 위치 ex) bit_position = 0
    :param new_state: 새로운 상태 ex) new_state = True
    :param type: 타입 ex) type = 0: AUTO/MANUAL, 1: REMOTE/LOCAL
    :return: 변경된 값
    """
    client = ModbusTcpClient(host=host, port=port)
    try:
        response = client.read_holding_registers(register_address, count=1, slave=slave)
        register_digital_value = response.registers[0]  # 16비트 전체 값

        if new_state:
            result = register_digital_value | (1 << bit_position)  # 특정 비트 설정
        else:
            result = register_digital_value & ~(1 << bit_position)  # 특정 비트 클리어

        # 변경된 값을 레지스터에 쓰기
        write_response = client.write_register(register_address, result, slave=slave)
        if not write_response.isError():
            print(f"Successfully wrote value: {result}")
        else:
            print(f"Error writing to register: {write_response}")
    finally:
        client.close()
        return _get_digital_status_message(result, type, bit_position=bit_position)


def get_digital_status_bit(
    host: str,
    port: int,
    register_address: int,
    bit_position: int,
    slave: int,
    type: int,
) -> str:
    """특정 비트 위치의 값을 가져오기"""
    client = ModbusTcpClient(host=host, port=port)
    try:
        response = client.read_holding_registers(register_address, count=1, slave=slave)
        register_digital_value = response.registers[0]  # 16비트 전체 값
        result = (register_digital_value >> bit_position) & 1  # 특정 비트 값 추출
    finally:
        client.close()
        return _get_digital_status_message(result, type)


def get_analog_value(
    host: str,
    port: int,
    register_address: int,
    slave: int,
) -> int:
    """아날로그 값 불러오기"""
    client = ModbusTcpClient(host=host, port=port, retries=1)
    try:
        response = client.read_holding_registers(register_address, count=1, slave=slave)
        if response is None or response.isError():
            raise Exception(f"Modbus 응답 오류가 발생했습니다")

        if not response.registers:
            raise Exception("레지스터 값을 읽을 수 없습니다")

        return response.registers[0]  # 16비트 전체 값
    except Exception as e:
        raise Exception(f"아날로그 값 불러오기 오류: {e}")
    finally:
        client.close()


def test_connection(host: str, port: int):
    """테스트 연결 확인"""
    client = ModbusTcpClient(host=host, port=port)
    try:
        response = client.connect()
        if response:
            return {"message": "연결 성공"}
        else:
            return {"message": "연결 실패"}
    except Exception as e:
        return {"message": f"연결 확인 오류: {e}"}
    finally:
        client.close()


def get_all_analog_values(host: str, port: int):
    """모든 아날로그 값 불러오기"""
    client = ModbusTcpClient(host=host, port=port)
    register_map = {}
    try:
        # 레지스터 범위 정의
        register_ranges = [
            (1220, 6),  # 1220-1225
            (2000, 11),  # 2000-2010
            (2100, 21),  # 2100-2120
            (2300, 11),  # 2300-2310
            (2330, 6),  # 2330-2335
            (2500, 11),  # 2500-2510
            (2701, 5),  # 2701-2705
            (2901, 2),  # 2901-2902
            (1200, 11),  # 1200-1210
        ]
        for start_addr, count in register_ranges:
            response = client.read_holding_registers(start_addr, count=count, slave=1)
            if response and not response.isError():
                # 각 레지스터 주소와 값을 매핑
                for i, value in enumerate(response.registers):
                    register_map[start_addr + i] = value
            else:
                print(f"Error reading registers {start_addr}-{start_addr+count-1}")

        return register_map
    finally:
        client.close()


def _get_digital_status_message(
    result: int, type: int, *, bit_position: int = 0
) -> str:
    if type == 0:
        return "AUTO" if (result >> bit_position & 1) == 0 else "MANUAL"
    else:
        return "LOCAL" if (result >> bit_position & 1) == 0 else "REMOTE"
