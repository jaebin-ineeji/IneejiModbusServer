import asyncio
from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse
from app.api.dependencies import get_database_client, get_modbus_client_by_machine_name
from app.models.schemas import ApiResponse, MachineConfig, TagConfig, ErrorResponse
from app.models.swagger_docs import (
    MACHINE_LIST_RESPONSE,
    MACHINE_ADD_RESPONSE,
    MACHINE_CONFIG_RESPONSE,
)
from app.services.modbus.client import DatabaseClientManager, ModbusClientManager
from functools import lru_cache

from app.services.modbus.machine import MachineService
from fastapi import WebSocket, WebSocketDisconnect

from app.core.logging_config import setup_logger
from app.services.modbus.websocket_service import WebSocketService


logger = setup_logger(__name__)

router = APIRouter(prefix="/machine", tags=["machine"])


@lru_cache
def get_machine_service(db: DatabaseClientManager = Depends(get_database_client)):
    return MachineService(db)


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="기계 목록 조회",
    description="현재 등록된 모든 기계의 목록과 각 기계의 태그 설정을 반환합니다.",
    response_description="기계 목록 및 태그 설정",
    responses={200: MACHINE_LIST_RESPONSE},
)
async def get_machines_config(
    machine_service: MachineService = Depends(get_machine_service),
):
    """현재 등록된 기계 목록 및 태그 반환"""
    result = machine_service.get_all_machines()
    return ApiResponse(
        success=result.success, message=result.message, data=result.data
    ).model_dump(exclude_none=True)


@router.get(
    "/{machine_name}",
    status_code=status.HTTP_200_OK,
    summary="기계 설정 조회",
    description="특정 기계의 설정을 반환합니다.",
    response_description="기계 설정",
    responses={200: MACHINE_CONFIG_RESPONSE},
)
async def get_machine_config(
    machine_name: str,
    machine_service: MachineService = Depends(get_machine_service),
):
    """특정 기계의 설정을 반환"""
    result = machine_service.get_machine_config_response(machine_name)
    return ApiResponse(
        success=result.success, message=result.message, data=result.data
    ).model_dump(exclude_none=True)


@router.post(
    "/{machine_name}",
    status_code=status.HTTP_201_CREATED,
    summary="새로운 기계 추가",
    description="새로운 기계를 추가하고 설정을 갱신합니다.",
    response_description="기계 추가 결과",
    responses={201: MACHINE_ADD_RESPONSE[201], 409: MACHINE_ADD_RESPONSE[409]},
)
async def add_machine(
    machine_name: str,
    config: MachineConfig,
    machine_service: MachineService = Depends(get_machine_service),
):
    """새로운 기계를 추가하고 설정을 갱신"""
    result = machine_service.add_machine(machine_name, config)
    return ApiResponse(
        success=result.success, message=result.message, data=result.data
    ).model_dump(exclude_none=True)


@router.delete("/{machine_name}")
async def delete_machine(
    machine_name: str,
    machine_service: MachineService = Depends(get_machine_service),
):
    """기계를 삭제하고 설정을 갱신"""
    result = machine_service.delete_machine(machine_name)

    return ApiResponse(
        success=result.success, message=result.message, data=result.data
    ).model_dump(exclude_none=True)


@router.post("/{machine_name}/tags", status_code=status.HTTP_201_CREATED)
async def add_tag(
    machine_name: str,
    tag_name: str,
    tag_data: TagConfig,
    machine_service: MachineService = Depends(get_machine_service),
):
    """특정 기계에 태그 추가 후 설정 갱신"""
    result = machine_service.add_machine_tag(machine_name, tag_name, tag_data)
    return ApiResponse(
        success=result.success, message=result.message, data=result.data
    ).model_dump(exclude_none=True)


@router.delete("/{machine_name}/tags/{tag_name}", status_code=status.HTTP_200_OK)
async def delete_tag(
    machine_name: str,
    tag_name: str,
    machine_service: MachineService = Depends(get_machine_service),
):
    """특정 기계에서 태그 삭제 후 설정 갱신"""
    machine_service.delete_machine_tag(machine_name, tag_name)
    return ApiResponse(success=True, message=f"태그 {tag_name} 삭제 완료").model_dump(
        exclude_none=True
    )


@router.get("/{machine_name}/tags", status_code=status.HTTP_200_OK)
async def get_tags(
    machine_name: str,
    machine_service: MachineService = Depends(get_machine_service),
):
    """특정 기계의 모든 태그 반환"""
    tags = machine_service.get_machine_tags(machine_name)
    return ApiResponse(
        success=True, message=f"기계 {machine_name}의 태그 목록 조회 성공", data=tags
    ).model_dump(exclude_none=True)


@router.get("/{machine_name}/tags/{tag_name}/config", status_code=status.HTTP_200_OK)
async def get_tag_config(
    machine_name: str,
    tag_name: str,
    machine_service: MachineService = Depends(get_machine_service),
):
    """특정 기계의 특정 태그 설정 조회"""
    tag_config = machine_service.get_machine_tag_by_name(machine_name, tag_name)
    return ApiResponse(
        success=True,
        message=f"{machine_name.upper()} 기계의 태그 {tag_name.upper()} 설정 조회 성공",
        data=tag_config,
    ).model_dump(exclude_none=True)


@router.put("/{machine_name}/tags/{tag_name}", status_code=status.HTTP_200_OK)
async def update_tag(
    machine_name: str,
    tag_name: str,
    tag_data: TagConfig,
    machine_service: MachineService = Depends(get_machine_service),
):
    """특정 기계의 특정 태그 설정 수정"""
    machine_service.update_machine_tag(machine_name, tag_name, tag_data)
    return ApiResponse(success=True, message=f"태그 {tag_name} 수정 완료").model_dump(
        exclude_none=True
    )


@router.get("/{machine_name}/tags/{tag_name}", status_code=status.HTTP_200_OK)
async def get_tag_value(
    machine_name: str,
    tag_name: str,
    machine_service: MachineService = Depends(get_machine_service),
    client: ModbusClientManager = Depends(get_modbus_client_by_machine_name),
):
    try:
        machine_service.client_manager = client
        result = await machine_service.read_machine_tag_value(machine_name, tag_name)
        return ApiResponse(
            success=True,
            message=f"{machine_name.upper()} 기계의 태그 {tag_name.upper()} 값 조회 성공",
            data=result,
        ).model_dump(exclude_none=True)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content=ApiResponse(
                success=False,
                message="태그 값 조회 실패",
                error=ErrorResponse(code="TAG_READ_ERROR", message=str(e)),
            ).model_dump(),
        )


@router.get(
    "/{machine_name}/values",
    status_code=status.HTTP_200_OK,
    summary="선택한 태그 값 조회",
    description="클라이언트가 요청한 태그 이름 목록에 해당하는 태그 값을 반환합니다.",
)
async def get_selected_tag_values(
    machine_name: str,
    tag_names: str = Query(
        ..., description="조회할 태그들의 이름 리스트, 예: TAG1, TAG2"
    ),
    machine_service: MachineService = Depends(get_machine_service),
    client: ModbusClientManager = Depends(get_modbus_client_by_machine_name),
):
    try:
        machine_service.client_manager = client
        tag_list = [tag.strip() for tag in tag_names.split(",")]
        tasks = [
            machine_service.read_machine_tag_value(machine_name, tag.upper())
            for tag in tag_list
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        data = {}
        for tag, result in zip(tag_list, results):
            # 예외가 발생한 경우 에러 메시지를 기록합니다.
            if isinstance(result, Exception):
                data[tag.upper()] = f"오류 발생: {str(result)}"
            else:
                data[tag.upper()] = result
        return ApiResponse(
            success=True,
            message=f"{machine_name.upper()} 기계의 선택한 태그 값 조회 성공",
            data=data,
        ).model_dump(exclude_none=True)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content=ApiResponse(
                success=False,
                message="태그 값 조회 실패",
                error=ErrorResponse(code="TAG_READ_ERROR", message=str(e)),
            ).model_dump(),
        )


@router.post("/{machine_name}/tags/{tag_name}", status_code=status.HTTP_200_OK)
async def set_tag_value(
    machine_name: str,
    tag_name: str,
    tag_value: str = Query("*", description="태그 값"),
    machine_service: MachineService = Depends(get_machine_service),
    client: ModbusClientManager = Depends(get_modbus_client_by_machine_name),
):
    machine_service.client_manager = client
    result = await machine_service.write_machine_tag_value(
        machine_name, tag_name, tag_value
    )
    if result:
        return ApiResponse(
            success=result.success, message=result.message, data=result.data
        ).model_dump(exclude_none=True)


@router.websocket("/{machine_name}/ws")
async def websocket_tag_values(
    websocket: WebSocket,
    machine_name: str,
    machine_service: MachineService = Depends(get_machine_service),
    client: ModbusClientManager = Depends(get_modbus_client_by_machine_name),
):
    await websocket.accept()
    websocket_service = WebSocketService(machine_service)

    try:
        await websocket_service.handle_single_machine_monitoring(
            websocket, machine_name, client
        )
    except WebSocketDisconnect:
        logger.info(f"클라이언트 연결이 종료되었습니다: {machine_name}")
    except Exception as e:
        logger.error(f"웹소켓 에러 발생: {str(e)}")


@router.websocket("/ws")
async def websocket_multiple_machines_values(
    websocket: WebSocket,
    machine_service: MachineService = Depends(get_machine_service),
):
    await websocket.accept()
    websocket_service = WebSocketService(machine_service)

    try:
        await websocket_service.handle_multiple_machines_monitoring(websocket)
    except WebSocketDisconnect:
        logger.info("웹소켓 연결이 종료되었습니다")
    except Exception as e:
        logger.error(f"웹소켓 에러 발생: {str(e)}")
