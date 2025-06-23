import io
import json
from fastapi.testclient import TestClient
from PIL import Image
from app.main import app

client = TestClient(app)

def create_test_image():
    # Create a simple black square image for testing
    img = Image.new('RGB', (160, 160), color='black')
    buf = io.BytesIO()
    img.save(buf, format='JPEG')
    buf.seek(0)
    return buf
