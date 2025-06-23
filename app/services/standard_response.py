"""
Standardized API response envelope for all endpoints.
"""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class StandardResponse(BaseModel):
    """Standardized API response envelope."""
    success: bool = Field(..., json_schema_extra={"example": True}, description="Indicates if the request was successful.")
    data: Optional[dict] = Field(
        None,
        json_schema_extra={"example": {"embedding": [0.1]*512, "gender": "male"}},
        description="Returned data if successful."
    )
    error: Optional[dict] = Field(
        None,
        json_schema_extra={"example": {"code": 400, "message": "Invalid image file."}},
        description="Error details if any."
    )
