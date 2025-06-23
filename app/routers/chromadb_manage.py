"""
ChromaDB management endpoints: list all data, delete by filename.
"""
from fastapi import APIRouter, HTTPException
from app.services.chromadb_service import chromadb_service
from app.services.standard_response import StandardResponse
import numpy as np

router = APIRouter(tags=["ChromaDB Management"])

@router.get("/chromadb/all", summary="List all ChromaDB data")
def get_all_chromadb():
    result = chromadb_service.collection.get(include=["embeddings", "documents", "metadatas"])
    # Convert numpy arrays to lists for JSON serialization
    if "embeddings" in result and isinstance(result["embeddings"], (list, dict, np.ndarray)):
        if isinstance(result["embeddings"], dict):
            result["embeddings"] = {k: (v.tolist() if isinstance(v, np.ndarray) else v) for k, v in result["embeddings"].items()}
        else:
            result["embeddings"] = [e.tolist() if isinstance(e, np.ndarray) else e for e in result["embeddings"]]
    return StandardResponse(success=True, data=result, error=None)

@router.delete("/chromadb/delete-by-filename/{filename}", summary="Delete embedding by filename")
def delete_embedding_by_filename(filename: str):
    # Try to delete by metadata 'filename' field
    try:
        chromadb_service.collection.delete(where={"filename": filename})
        return StandardResponse(success=True, data={"deleted": filename}, error=None)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete embedding: {e}")

@router.delete("/chromadb/clear", summary="Delete all face profiles in ChromaDB")
def clear_chromadb():
    try:
        all_ids = chromadb_service.collection.get().get("ids", [])
        if all_ids:
            chromadb_service.collection.delete(ids=all_ids)
        return StandardResponse(success=True, data={"message": "All face profiles deleted."}, error=None)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear ChromaDB: {e}")
