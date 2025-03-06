from fastapi import APIRouter, Depends, status, Query
from typing import Optional
from app.api.dependencies import get_database_client
from app.models.schemas import ApiResponse, GlobalAutoControlConfig
from app.services.modbus.autocontrol import AutoControlService
from app.services.modbus.machine import MachineService

router = APIRouter(prefix="/autocontrol", tags=["autocontrol"])

def get_auto_control_service(
    machine_service: MachineService = Depends(lambda db=Depends(get_database_client): MachineService(db))
) -> AutoControlService:
    return AutoControlService(machine_service)

@router.post(
    "",
    status_code=status.HTTP_200_OK,
    summary="자동 제어 설정",
    description="자동 제어 모드를 설정합니다. 설정에 따라 1분마다 지정된 기계와 태그를 제어하며 로그를 단일 파일에 저장합니다.",
)
async def configure_auto_control(
    config: GlobalAutoControlConfig,
    auto_control_service: AutoControlService = Depends(get_auto_control_service),
):
    """자동 제어 설정 구성"""
    result = auto_control_service.configure_auto_control(config)
    return ApiResponse(
        success=result.success, message=result.message, data=result.data
    ).model_dump(exclude_none=True)

@router.post(
    "/execute",
    status_code=status.HTTP_200_OK,
    summary="자동 제어 실행",
    description="자동 제어를 즉시 실행합니다. 설정값이 제공되면 그 설정대로 제어하고, 그렇지 않으면 기존 저장된 설정값으로 제어합니다.",
)
async def execute_auto_control(
    config: Optional[GlobalAutoControlConfig] = None,
    auto_control_service: AutoControlService = Depends(get_auto_control_service),
):
    """자동 제어 즉시 실행"""
    result = await auto_control_service.execute_control(config)
    return ApiResponse(
        success=result.success, message=result.message, data=result.data
    ).model_dump(exclude_none=True)

@router.put(
    "/toggle",
    status_code=status.HTTP_200_OK,
    summary="자동 제어 모드 토글",
    description="자동 제어 모드를 켜거나 끕니다.",
)
async def toggle_auto_control(
    enabled: bool = Query(..., description="활성화 여부"),
    auto_control_service: AutoControlService = Depends(get_auto_control_service),
):
    """자동 제어 모드 토글"""
    result = auto_control_service.toggle_auto_control(enabled)
    return ApiResponse(
        success=result.success, message=result.message, data=result.data
    ).model_dump(exclude_none=True)

@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="자동 제어 상태 조회",
    description="현재 자동 제어 모드 상태를 조회합니다.",
)
async def get_auto_control_status(
    auto_control_service: AutoControlService = Depends(get_auto_control_service),
):
    """자동 제어 상태 조회"""
    result = auto_control_service.get_auto_control_status()
    return ApiResponse(
        success=result.success, message=result.message, data=result.data
    ).model_dump(exclude_none=True)