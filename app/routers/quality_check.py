# FastAPI endpoints for five-pose guided enrollment QC only

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from starlette.concurrency import run_in_threadpool
from tempfile import NamedTemporaryFile
import numpy as np
import cv2
from app.services.facial_analysis import face_app
from app.services.spoof_model import get_spoof_model
from app.services.logging_config import setup_logging
from app.services.quality_check_utils import is_blurry, is_bright

router = APIRouter(prefix="/enroll", tags=["Enroll"])
logger = setup_logging()

POSE_BUCKETS = {
    "frontal": lambda y, p: abs(y) < 10 and abs(p) < 8,
    "left":    lambda y, p: y <= -15,
    "right":   lambda y, p: y >= 15,
    "up":      lambda y, p: p <= -12,
    "down":    lambda y, p: p >= 12,
}

@router.post("/qc/{bucket}")
async def quick_check(bucket: str, frame: UploadFile = File(...), spoof_model = Depends(get_spoof_model)):
    logger.info(f"QC request for bucket: {bucket}")
    if bucket not in POSE_BUCKETS:
        logger.error(f"Invalid pose bucket: {bucket}")
        raise HTTPException(400, "bad bucket")
    contents = await frame.read()
    rgb = cv2.imdecode(np.frombuffer(contents, np.uint8), cv2.IMREAD_COLOR)[:, :, ::-1]
    rgb = rgb[:, ::-1, :] 
    faces = face_app.get(rgb)
    if not faces:
        logger.warning(f"No face detected for bucket: {bucket}")
        return {"ok": False, "reason": "no face"}
    f = faces[0]
    yaw, pitch = f.pose[:2]
    logger.info(f"Detected pose for {bucket}: yaw={yaw}, pitch={pitch}")
    # if not POSE_BUCKETS[bucket](yaw, pitch):
    #     logger.warning(f"Wrong pose for {bucket}: yaw={yaw}, pitch={pitch}")
    #     return {"ok": False, "reason": "wrong pose"}
    if is_blurry(rgb):
        logger.warning(f"Blurry image for {bucket}")
        return {"ok": False, "reason": "blurry"}
    if not is_bright(rgb):
        logger.warning(f"Bad lighting for {bucket}")
        return {"ok": False, "reason": "bad_light"}

    if spoof_model:
        with NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp.write(contents)
            tmp_path = tmp.name
        try:
            spoof_result = await run_in_threadpool(spoof_model.analyze_image, tmp_path)
            logger.info(f"Spool result {bucket}: {spoof_result}")
            if spoof_result.get("dominant_spoof") != "Real":
                logger.warning(f"Spoof detected for {bucket}")
                return {"ok": False, "reason": "spoof"}
        except Exception as e:
            logger.error(f"Spoof model error for {bucket}: {e}")
    logger.info(f"QC passed for {bucket}")
    return {"ok": True}
