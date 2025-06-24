"""
Singleton lazy loader for DeepFaceAntiSpoofing model for use across the app.
"""
from deepface_antispoofing import DeepFaceAntiSpoofing
from app.services.logging_config import setup_logging
from fastapi import Request, HTTPException

logger = setup_logging()

def load_spoof_model():
    try:
        _spoof_model = DeepFaceAntiSpoofing()
        logger.info("DeepFaceAntiSpoofing model initialized successfully.")
        assert _spoof_model.age_gender_model_path.exists(), f"Missing {_spoof_model.age_gender_model_path}"
        assert _spoof_model.anti_spoofing_model_path.exists(), f"Missing {_spoof_model.anti_spoofing_model_path}"
    except ImportError:
        _spoof_model = None
        logger.warning("DeepFaceAntiSpoofing could not be imported. Spoofing checks will be unavailable.")
    except Exception as e:
        _spoof_model = None
        logger.error(f"Failed to initialize DeepFaceAntiSpoofing: {e}")
    return _spoof_model

def get_spoof_model(request: Request):
    """
    Dependency which returns the pre-loaded model from app.state
    """
    model = getattr(request.app.state, "spoof_model", None)
    if model is None:
        logger.error("Anti-spoofing model not loaded in app state.")
        raise HTTPException(status_code=500, detail="Anti-spoofing model not loaded")
    logger.info("Returning anti-spoofing model from app state. Model type: {}".format(type(model)))
    return model