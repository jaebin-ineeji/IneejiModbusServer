import requests
import json

def get_tag_values():
    # 조회할 기계 이름들과 태그 이름들을 리스트로 설정.
    machine_names = ['oil_main', 'oil_1l', 'oil_2l','oil_3l','oil_4l','oil_5l','oil_1r','oil_2r','oil_3r','oil_4r','oxy_main','oxy_1l','oxy_2l','oxy_3l','oxy_4l','oxy_5l','oxy_1r','oxy_2r','oxy_3r','oxy_4r']  # 설정된 기계 이름
    tag_names = ['pv', 'sv']

    # 최종 결과를 저장할 딕셔너리.
    aggregated_results = {}

    # 각 기계별로 API 호출을 수행.
    for machine in machine_names:
        url = f"http://localhost:4444/machine/{machine}/values"
        # 태그 이름을 콤마(,)로 연결하여 쿼리 파라미터로 전달.
        params = {"tag_names": ','.join(tag_names)}
        
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                json_data = response.json()
                if json_data.get("success"):
                    # 기계 이름을 key로 하여 해당 기계의 태그 값을 저장합니다.
                    aggregated_results[machine] = json_data.get("data")
                else:
                    aggregated_results[machine] = {"error": json_data.get("message")}
            else:
                aggregated_results[machine] = {"error": f"HTTP 오류 {response.status_code}"}
        except Exception as e:
            aggregated_results[machine] = {"error": str(e)}
    return aggregated_results


result = json.dumps(get_tag_values(), indent=2, ensure_ascii=False)

print(result)