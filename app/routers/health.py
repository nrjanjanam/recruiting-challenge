"""
Health check endpoint for the API. Returns status and version.
"""
from fastapi import APIRouter
from app.config import settings
from app.services.standard_response import StandardResponse

router = APIRouter(tags=["Health"])

@router.get("/health", summary="Health check", description="Returns the health and version of the API.", response_model=StandardResponse)
def health():
    return StandardResponse(success=True, data={"status": "ok", "version": settings.API_VERSION}, error=None)
