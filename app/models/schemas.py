from pydantic import BaseModel
from typing import Any, Optional


class ApiResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None
