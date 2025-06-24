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

from fastapi import APIRouter, File, UploadFile, HTTPException, Form, status, Depends
from starlette.concurrency import run_in_threadpool
from pydantic import BaseModel, Field
from PIL import Image
from io import BytesIO
from typing import List, Optional, Dict, Any
from app.services.facial_analysis import analyze_face
from app.services.logging_config import setup_logging
from app.services.chromadb_service import chromadb_service
from app.services.standard_response import StandardResponse
from app.services.spoof_model import get_spoof_model
from app.config import settings
import uuid
from datetime import datetime, UTC
import json
from tempfile import NamedTemporaryFile
import os

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
    extra: Optional[str] = Form(None),  # JSON string for arbitrary metadata
    spoof_model = Depends(get_spoof_model)
) -> StandardResponse:
    """Create a facial profile from an uploaded image and store it in ChromaDB."""
    logger.info("Received request to create profile")

    contents = await file.read()
    # Check file size before reading (e.g., 10MB limit)
    MAX_SIZE = 10 * 1024 * 1024  # 10 MB
    size = len(contents)
    if size > MAX_SIZE:
        logger.error(f"File too large: {size} bytes")
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail={"code": 413, "message": "File too large. Max 10MB allowed."})
    try:
        img = Image.open(BytesIO(contents))
    except Exception as e:
        logger.error(f"Invalid image file: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail={"code": 415, "message": "Unsupported file type. Please upload a valid image."})
    try:
        profile_data = analyze_face(img)
    except Exception as e:
        logger.error(f"Face analysis service error: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={"code": 500, "message": "Face analysis failed."})
    if "error" in profile_data:
        logger.warning(f"Face analysis failed: {profile_data['error']}")
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"code": 422, "message": profile_data["error"]})

    # Run anti-spoofing and age/gender analysis
    with NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        tmp.write(contents)
        tmp_path = tmp.name
    try:
        if not spoof_model:
            raise HTTPException(status_code=500, detail={"code": 500, "message": "Spoof model not available."})
        spoof_result = await run_in_threadpool(spoof_model.analyze_image, tmp_path)
        logger.info(f"Anti-spoofing/age/gender result: {spoof_result}")
        if spoof_result.get("dominant_spoof") != "Real":
            logger.warning("Anti-spoofing check failed: not a real face")
            raise HTTPException(status_code=400, detail={"code": 400, "message": "Image failed anti-spoofing check. Not a real face."})
        # Extract age and dominant_gender for metadata
        age = spoof_result.get("age")
        dominant_gender = spoof_result.get("dominant_gender")
    finally:
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.remove(tmp_path)

    # Store embedding in ChromaDB
    embedding_id = str(uuid.uuid4())
    metadata = {
        "filename": file.filename,
        "age": age,
        "dominant_gender": dominant_gender,
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
            "extra": extra_dict,
            "age": age,
            "dominant_gender": dominant_gender
        },
        error=None
    )
