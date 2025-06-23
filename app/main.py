# Main entrypoint for FastAPI app
from fastapi import FastAPI
import uvicorn
import os
from deepface_antispoofing import DeepFaceAntiSpoofing
from app.routers.register import register_routers
from app.services.logging_config import setup_logging
from app.services.openapi_schema import custom_openapi
from app.services.port_utils import get_available_port
from app.services.spoof_model import get__spoof_model
import numpy as np
import cv2
from app.config import settings


app = FastAPI()

# Setup logging
logger = setup_logging()

# Custom OpenAPI schema for enhanced documentation
app.openapi = lambda: custom_openapi(app)

# Include routers
register_routers(app)

# Use config for port/host
port = settings.PORT
host = settings.HOST

@app.on_event("startup")
def load_models():
    _spoof_model = get__spoof_model()
    # Warm-up: create a dummy image file and call analyze_image
    dummy_img = np.ones((256, 256, 3), dtype=np.uint8) * 127  # Gray image
    dummy_path = "images/test/dummy_warmup.jpg"
    cv2.imwrite(dummy_path, dummy_img)
    try:
        if _spoof_model:
            _spoof_model.analyze_image(dummy_path)
            logger.info("Spoof model warm-up call succeeded.")
            app.state.spoof_model = _spoof_model
    except Exception as e:
        logger.warning(f"Spoof model warm-up failed: {e}")
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


if __name__ == "__main__":
    logger.info("Starting FastAPI server with Loguru logging!")
    logger.info(f"Using port {port}")
    logger.info(f"⚙️  FastAPI working directory is {os.getcwd()}")
    uvicorn.run("app.main:app", host=host, port=port)
