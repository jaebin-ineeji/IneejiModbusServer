from fastapi import APIRouter, Depends, HTTPException
from typing import Dict
from app.models.schemas import ApiResponse, MachineConfigFormat
from app.services.config import ConfigService
from app.api.dependencies import get_database_client
from app.services.modbus.client import DatabaseClientManager

router = APIRouter(prefix="/config", tags=["config"])


@router.post("/import")
async def import_config(
    config: Dict[str, MachineConfigFormat],
    db: DatabaseClientManager = Depends(get_database_client),
):
    """기계와 태그 설정을 일괄 등록"""
    try:
        config_service = ConfigService(db)
        await config_service.import_config(config)
        return ApiResponse(
            success=True,
            message="기계 및 태그 설정이 성공적으로 일괄 등록되었습니다.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"설정 일괄 등록 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/export")
async def export_config(
    db: DatabaseClientManager = Depends(get_database_client),
):
    """등록된 모든 기계와 태그 설정을 JSON 형식으로 추출"""
    try:
        config_service = ConfigService(db)
        result = await config_service.export_config()
        return ApiResponse(
            success=True,
            data=result,
            message=f"설정이 성공적으로 추출되었으며 {result['saved_path']}에 저장되었습니다.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"설정 추출 중 오류가 발생했습니다: {str(e)}"
        )
