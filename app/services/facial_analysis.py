# Facial analysis service for extracting facial features
from PIL import Image
import numpy as np
import insightface
from insightface.app import FaceAnalysis
from app.services.logging_config import setup_logging
from app.config import settings
import torch
import cv2

# Initialize the face analysis model once (global, for performance)
face_app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
face_app.prepare(ctx_id=0)
logger = setup_logging()
logger.remove()
logger.add(
    "logs/app.log",
    rotation="1 week",
    retention="4 weeks",
    level=settings.LOG_LEVEL,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}"
)

def analyze_face(image: Image.Image) -> dict:
    logger.info("Analyzing face for embedding and gender.")
    img_array = np.array(image.convert("RGB"))
    faces = face_app.get(img_array)
    if not faces:
        logger.warning("No face detected in the image.")
        return {"error": "No face detected."}
    if len(faces) > 1:
        logger.warning(f"Multiple faces detected: {len(faces)} faces.")
        return {"error": f"Multiple faces detected: {len(faces)} faces. Please upload an image with only one face."}
    face = faces[0]
    embedding = face.embedding.tolist()  # 512D vector
    gender = face.sex  # F: female, M: male
    logger.info(f"Face analysis successful. Raw gender value: {gender}")
    return {
        "embedding": embedding,
        "gender": gender
    }

def verify_embeddings(ref_embedding, new_embedding, metric: str = "euclidean") -> dict:
    logger.info("Verifying embeddings.")
    # Convert to numpy arrays first
    ref_embedding = np.array(ref_embedding)
    new_embedding = np.array(new_embedding)
    # Handle all-zeros vectors to avoid division by zero
    if np.all(ref_embedding == 0) and np.all(new_embedding == 0):
        logger.info("Both embeddings are all zeros. Returning perfect match.")
        return {
            "match": True,
            "distance": 0.0,
            "threshold": 1.0,
            "message": "Match"
        }
    # Flatten new_embedding if it has extra dimensions (e.g., (1,1,512))
    if new_embedding.ndim > 1:
        new_embedding = new_embedding.reshape(-1)
    if ref_embedding.ndim > 1:
        ref_embedding = ref_embedding.reshape(-1)
    # L2-normalize both embeddings
    ref_embedding = ref_embedding / np.linalg.norm(ref_embedding)
    new_embedding = new_embedding / np.linalg.norm(new_embedding)
    if metric == "cosine":
        threshold = 0.9  # Cosine similarity threshold for match
        similarity = np.dot(ref_embedding, new_embedding)
        match = bool(np.isclose(similarity, 1.0) or similarity > threshold)
        logger.info(f"Verification {'match' if match else 'no match'} (cosine similarity: {similarity}, threshold: {threshold})")
        return {
            "match": match,
            "similarity": float(similarity),
            "threshold": threshold,
            "message": "Match" if match else "No match"
        }
    else:
        # Euclidean distance: 0 = identical, 2 = opposite (for unit vectors)
        threshold = 1.0  # Euclidean distance threshold for match
        distance = np.linalg.norm(ref_embedding - new_embedding)
        match = bool(np.isclose(distance, 0.0) or distance < threshold)
        logger.info(f"Verification {'match' if match else 'no match'} (euclidean distance: {distance}, threshold: {threshold})")
        return {
            "match": match,
            "distance": float(distance),
            "threshold": threshold,
            "message": "Match" if match else "No match"
        }
