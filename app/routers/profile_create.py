"""
Profile creation endpoint: Extracts robust facial embeddings and gender from an uploaded image, stores them in ChromaDB with optional user metadata (user_id, name, extra), and returns the profile data. Handles errors gracefully and logs all operations.

Request:
- file: image file (required)
- user_id: str (optional)
- name: str (optional)
- extra: JSON string (optional, for arbitrary metadata)

Response:
- embedding: List[float]
- gender: str
- user_id: str (if provided)
- name: str (if provided)
- extra: dict (if provided)
"""

from fastapi import APIRouter, File, UploadFile, HTTPException, Form, status
from pydantic import BaseModel, Field
from PIL import Image
from io import BytesIO
from typing import List, Optional, Dict, Any
from ..services.facial_analysis import analyze_face
from app.services.logging_config import setup_logging
from app.services.chromadb_service import chromadb_service
from app.services.standard_response import StandardResponse
from app.config import settings
import uuid
from datetime import datetime, UTC
import json

router = APIRouter(prefix=f"/{settings.API_VERSION}", tags=["Profile"])
logger = setup_logging()

class ProfileMetadata(BaseModel):
    """Metadata for a facial profile."""

    user_id: Optional[str] = Field(None, json_schema_extra={"example": "user123"}, description="User identifier.")
    name: Optional[str] = Field(None, json_schema_extra={"example": "John Doe"}, description="User's name.")
    extra: Optional[Dict[str, Any]] = Field(None, json_schema_extra={"example": {"foo": "bar"}}, description="Additional metadata.")

class Profile(BaseModel):
    """Facial profile data."""
    embedding: List[float] = Field(..., json_schema_extra={"example": [0.1]*512}, description="512-dimensional facial embedding vector.")
    gender: str = Field(..., json_schema_extra={"example": "male"}, description="Predicted gender: 'male' or 'female'.")
    user_id: Optional[str] = Field(None, json_schema_extra={"example": "user123"}, description="User identifier.")
    name: Optional[str] = Field(None, json_schema_extra={"example": "John Doe"}, description="User's name.")
    extra: Optional[Dict[str, Any]] = Field(None, json_schema_extra={"example": {"foo": "bar"}}, description="Additional metadata.")

@router.post(
    "/create-profile",
    response_model=StandardResponse,
    summary="Create a facial profile",
    description="Upload an image to extract facial features and store the profile with optional metadata in ChromaDB.",
    tags=["Profile"]
)
async def create_profile(
    file: UploadFile = File(...),
    user_id: Optional[str] = Form(None),
    name: Optional[str] = Form(None),
    extra: Optional[str] = Form(None)  # JSON string for arbitrary metadata
) -> StandardResponse:
    """Create a facial profile from an uploaded image and store it in ChromaDB."""
    logger.info("Received request to create profile")
    # Check file size before reading (e.g., 10MB limit)
    MAX_SIZE = 10 * 1024 * 1024  # 10 MB
    file.file.seek(0, 2)  # Seek to end
    size = file.file.tell()
    file.file.seek(0)
    if size > MAX_SIZE:
        logger.error(f"File too large: {size} bytes")
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail={"code": 413, "message": "File too large. Max 10MB allowed."})
    try:
        img = Image.open(BytesIO(await file.read()))
    except Exception as e:
        logger.error(f"Invalid image file: {e}", exc_info=True)
        # Return 415 for unsupported media type (not an image)
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail={"code": 415, "message": "Unsupported file type. Please upload a valid image."})
    try:
        profile_data = analyze_face(img)
    except Exception as e:
        logger.error(f"Face analysis service error: {e}", exc_info=True)
        
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={"code": 500, "message": "Face analysis failed."})
    if "error" in profile_data:
        logger.warning(f"Face analysis failed: {profile_data['error']}")
        
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"code": 422, "message": profile_data["error"]})
    # Store embedding in ChromaDB
    embedding_id = str(uuid.uuid4())
    metadata = {
        "filename": file.filename,
        "gender": profile_data["gender"],
        "created_at": datetime.now(UTC).isoformat(),
        "user_id": user_id,
        "name": name,
    }
    if extra:
        try:
            extra_dict = json.loads(extra)
            metadata["extra"] = json.dumps(extra_dict)  # Store as JSON string
        except Exception as e:
            logger.warning(f"Failed to parse extra metadata: {e}", exc_info=True)
            extra_dict = None
    else:
        extra_dict = None
    # Remove None values from metadata
    metadata = {k: v for k, v in metadata.items() if v is not None}
    logger.debug(f"Metadata to be stored in ChromaDB: {metadata}")
    try:
        chromadb_service.add_embedding(embedding_id, profile_data["embedding"], metadata)
    except Exception as e:
        logger.error(f"ChromaDB storage failed: {e}", exc_info=True)
        return StandardResponse(success=False, data=None, error={"code": 500, "message": "Failed to store profile in vector database."})
    logger.info(f"Profile created and stored with id {embedding_id}")
    return StandardResponse(
        success=True,
        data={
            **profile_data,
            "user_id": user_id,
            "name": name,
            "extra": extra_dict
        },
        error=None
    )
