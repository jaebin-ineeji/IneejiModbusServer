from fastapi import APIRouter
from app.models.schemas import ApiResponse

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health_check():
    return ApiResponse(success=True, message="서비스가 정상 동작중입니다.")
