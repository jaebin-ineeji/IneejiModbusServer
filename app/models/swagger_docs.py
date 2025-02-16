MACHINE_LIST_RESPONSE = {
    "description": "기계 목록 조회 성공",
    "content": {
        "application/json": {
            "example": {
                "success": True,
                "message": "기계 목록 조회 성공",
                "data": {
                    "MACHINE1": {
                        "ip": "172.30.1.97",
                        "port": 502,
                        "slave": 1,
                        "tags": {
                            "TAG1": {
                                "tag_type": "Analog",
                                "logical_register": "40001",
                                "real_register": "2000",
                                "permission": "Read"
                            }
                        }
                    }
                }
            }
        }
    }
}

MACHINE_ADD_RESPONSE = {
    201: {
        "description": "기계 추가 성공",
        "content": {
            "application/json": {
                "example": {
                "success": True,
                "message": "기계 추가 완료",
                "data": {
                    "machine_name": "MACHINE1",
                    "config": {
                        "ip": "172.30.1.97",
                        "port": 502,
                        "slave": 1,
                        "tags": {}
                    }
                }
            }
        }
    }
    },
    409: {
        "description": "기계 추가 실패",
        "content": {
            "application/json": {
                "example": {
                    "success": False,
                    "message": "기계 추가중 오류가 발생했습니다: 기계 'OIL_MAIN'가 이미 존재합니다",
                    "error": {
                        "code": "MACHINE_ADD_ERROR",
                        "message": "기계 추가중 오류가 발생했습니다: 기계 'OIL_MAIN'가 이미 존재합니다"
                    }
                }
            }
        }
}
}