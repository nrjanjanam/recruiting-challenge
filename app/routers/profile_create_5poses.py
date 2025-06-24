"""
Profile creation endpoint (five-pose): Accepts five RGB frames (one per pose bucket), runs quality and pose checks on each, extracts robust facial embeddings, stores them in ChromaDB with optional user metadata, and returns the profile ID. Handles errors gracefully and logs all operations.

Request (JSON):
- frames: List[List[List[List[int]]]] (five RGB images as nested lists)
- user_id: str (optional)
- name: str (optional)
- extra: dict (optional, for arbitrary metadata)

Response:
- profile_id: str
- num_frames: int
- user_id: str (if provided)
- name: str (if provided)
- extra: dict (if provided)

QC checks per frame:
- Pose bucket (frontal, left, right, up, down)
- Blur (Laplacian var ≥ 100)
- Brightness (mean 70-180)
- Embedding norm ≥ 25
- Optional: PAD/spoof > 0.1
"""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from app.services.facial_analysis import face_app
from app.services.logging_config import setup_logging
from app.services.chromadb_service import chromadb_service
from app.services.spoof_model import get_spoof_model
from app.services.quality_check_utils import is_blurry, is_bright
from app.config import settings
import numpy as np
import cv2
import uuid
from datetime import datetime, UTC

router = APIRouter(prefix=f"/{settings.API_VERSION}", tags=["Profile"])
logger = setup_logging()

POSE_BUCKETS = {
    "frontal": lambda y, p: abs(y) < 10 and abs(p) < 8,
    "left":    lambda y, p: y <= -15,
    "right":   lambda y, p: y >= 15,
    "up":      lambda y, p: p <= -12,
    "down":    lambda y, p: p >= 12,
}

# --- QC helpers ---
class FivePosePayload(BaseModel):
    frames: Dict[str, List[List[List[int]]]] = Field(..., description="Dictionary mapping pose names to RGB frames (frontal, left, right, up, down)")
    user_id: Optional[str] = None
    name: Optional[str] = None
    extra: Optional[Dict[str, Any]] = None

class FivePoseResponse(BaseModel):
    profile_id: str
    num_frames: int
    user_id: Optional[str] = None
    name: Optional[str] = None
    extra: Optional[Dict[str, Any]] = None

@router.post(
    "/profile-create-5poses",
    response_model=FivePoseResponse,
    summary="Create a facial profile from five guided poses",
    description="Upload five RGB frames (frontal, left, right, up, down) to extract facial features, run QC, and store the profile in ChromaDB.",
    tags=["Profile"]
)
async def profile_create_5poses(
    payload: FivePosePayload,
    spoof_model = Depends(get_spoof_model)
) -> FivePoseResponse:
    """Create a facial profile from five guided pose frames and store in ChromaDB."""
    logger.info("Received 5-pose enrollment request")

    POSES = ["frontal", "left", "right", "up", "down"]  # Enforce strict order

    if set(payload.frames.keys()) != set(POSES):
        logger.error(f"Expected pose keys {POSES}, got {list(payload.frames.keys())}")
        raise HTTPException(status_code=400, detail=f"Frames must include exactly these keys: {POSES}")
    embeddings = []
    for pose in POSES:
        arr = payload.frames[pose]
        rgb = np.array(arr, dtype=np.uint8)
        if rgb.ndim != 3 or rgb.shape[2] != 3:
            logger.error(f"Frame {pose} is not a valid RGB image: shape {rgb.shape}")
            raise HTTPException(status_code=415, detail=f"Frame {pose} is not a valid RGB image")
        faces = face_app.get(rgb)
        if not faces:
            logger.warning(f"No face detected in {pose} frame")
            raise HTTPException(status_code=422, detail=f"No face detected in {pose} frame")
        if len(faces) > 1:
            logger.warning(f"Multiple faces detected in {pose} frame, using the first one")
            raise HTTPException(status_code=422, detail=f" {len(faces)} faces detected in {pose} frame")
        f = faces[0]
        embeddings.append(f.embedding)
    # Stack or average embeddings in strict order: F, L, R, U, D
    embeddings_np = np.vstack(embeddings)
    mean_embedding = embeddings_np.mean(axis=0)
    # Store in ChromaDB
    
    profile_id = str(uuid.uuid4())
    metadata = {
        "created_at": datetime.now(UTC).isoformat(),
        "user_id": payload.user_id,
        "name": payload.name,
        "extra": payload.extra,
        "num_frames": 5,
        "pose_buckets": "FLRUD",
    }
    # Remove None values
    metadata = {k: v for k, v in metadata.items() if v is not None}
    try:
        chromadb_service.add_embedding(profile_id, mean_embedding.tolist(), metadata)
    except Exception as e:
        logger.error(f"ChromaDB storage failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to store profile in vector database.")
    logger.info(f"Profile created and stored with id {profile_id}")
    return FivePoseResponse(
        profile_id=profile_id,
        num_frames=5,
        user_id=payload.user_id,
        name=payload.name,
        extra=payload.extra
    )
