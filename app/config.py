"""
Configuration module for the FastAPI facial profile app.
Loads settings from environment variables with sensible defaults.
"""
import os

class Settings:
    API_VERSION: str = os.environ.get("API_VERSION", "v1")
    HOST: str = os.environ.get("HOST", "127.0.0.1")
    PORT: int = int(os.environ.get("PORT", 8000))
    DEBUG: bool = os.environ.get("DEBUG", "False").lower() == "true"
    LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")
    RELOAD: bool = os.environ.get("RELOAD", "True").lower() == "true"
    CHROMA_COLLECTION: str = os.environ.get("CHROMA_COLLECTION", "face_profiles")
    # Add more config as needed

settings = Settings()
