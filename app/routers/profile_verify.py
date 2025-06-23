"""
Profile verification endpoint: Extracts facial embedding from an uploaded image, queries ChromaDB for nearest neighbors, and returns match result, distance, and metadata. Handles errors gracefully and logs all operations.

Request:
- file: image file (required)
- top_k: int (optional, number of nearest neighbors to consider)

Response:
- match: bool
- distance: float
- message: str
- matched_profile: dict (if match found, includes metadata)
"""

from fastapi import APIRouter, File, UploadFile, HTTPException, status
from pydantic import BaseModel, Field
from PIL import Image
from io import BytesIO
from typing import List, Optional, Dict, Any
from ..services.facial_analysis import analyze_face, verify_embeddings
from app.services.logging_config import setup_logging
from app.services.chromadb_service import chromadb_service
from app.config import settings
from app.services.standard_response import StandardResponse

router = APIRouter(prefix=f"/{settings.API_VERSION}", tags=["Profile"])
logger = setup_logging()

@router.post(
    "/verify-profile",
    response_model=StandardResponse,
    summary="Verify a facial profile",
    description="Upload an image to verify against stored profiles in ChromaDB. Returns match result and matched profile metadata if found."
)
async def verify_profile(
    file: UploadFile = File(...),
    top_k: int = 1
):
    logger.info("Received request to verify profile (ChromaDB)")
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
    embedding = profile_data["embedding"]
    try:
        results = chromadb_service.query_embedding(
            embedding, n_results=top_k)
        logger.info(f"Queried ChromaDB for nearest neighbors: {results["metadatas"]}")
        if not results["ids"] or not results["ids"][0]:
            logger.info("No matching profiles found in ChromaDB.")
            return StandardResponse(success=True, data={
                "match": False,
                "distance": None,
                "message": "No match found.",
                "matched_profile": None
            }, error=None)

        best_distance = results["distances"][0][0]
        best_metadata = results["metadatas"][0][0] if results["metadatas"] and results["metadatas"][0] else None

        match_result = verify_embeddings(embedding, results["embeddings"], metric="euclidean")
        match = match_result["match"]
        logger.info(f"Verification {'match' if match else 'no match'} (distance: {best_distance})")
        return StandardResponse(success=True, data={
            "match": match,
            "semantic_distance": best_distance,
            "euclidean_distance": match_result["distance"] if match_result.get("distance") is not None else None,
            "cosine_similarity": match_result["similarity"] if match_result.get("similarity") is not None else None,
            "message": "Match" if match else "No match",
            "matched_profile": best_metadata if match else None
        }, error=None)
    except Exception as e:
        logger.error(f"ChromaDB query failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail={"code": 500, "message": "Failed to query vector database."})
