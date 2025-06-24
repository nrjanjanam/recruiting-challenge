import cv2
import numpy as np

def is_blurry(rgb: np.ndarray) -> bool:
    """Return True if the image is blurry (Laplacian variance < 100)."""
    g = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    return cv2.Laplacian(g, cv2.CV_64F).var() < 100

def is_bright(rgb: np.ndarray) -> bool:
    """Return True if the image brightness is in the acceptable range (70 < mean < 180)."""
    m = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY).mean()
    return 70 < m < 180
