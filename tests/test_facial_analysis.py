import numpy as np
from app.services.facial_analysis import analyze_face, verify_embeddings
from PIL import Image
import pytest

def test_verify_embeddings_match():
    ref = [0.0]*512
    new = [0.0]*512
    result = verify_embeddings(ref, new)
    assert bool(result["match"]) is True
    assert result["distance"] == 0.0
    assert result["message"] == "Match"

def test_verify_embeddings_no_match():
    ref = [0.0]*512
    new = [10.0]*512
    result = verify_embeddings(ref, new)
    assert bool(result["match"]) is False
    assert result["message"] == "No match"

def test_analyze_face_no_face(monkeypatch):
    # Patch the model to return no faces
    class FakeFaceApp:
        def get(self, img): return []
    monkeypatch.setattr("app.services.facial_analysis.face_app", FakeFaceApp())
    img = Image.new('RGB', (160, 160), color='black')
    result = analyze_face(img)
    assert "error" in result
    assert result["error"] == "No face detected."

def test_analyze_face_male_branch(monkeypatch):
    # Patch the model to return a face with gender=1 (male)
    class FakeFace:
        embedding = type('emb', (), {'tolist': lambda self: [0.1]*512})()
        sex = 1
    class FakeFaceApp:
        def get(self, img): return [FakeFace()]
    monkeypatch.setattr("app.services.facial_analysis.face_app", FakeFaceApp())
    img = Image.new('RGB', (160, 160), color='black')
    result = analyze_face(img)
    assert result["gender"] == "male"
    assert len(result["embedding"]) == 512

def test_analyze_face_female_branch(monkeypatch):
    # Patch the model to return a face with gender=0 (female)
    class FakeFace:
        embedding = type('emb', (), {'tolist': lambda self: [0.1]*512})()
        sex = 0
    class FakeFaceApp:
        def get(self, img): return [FakeFace()]
    monkeypatch.setattr("app.services.facial_analysis.face_app", FakeFaceApp())
    img = Image.new('RGB', (160, 160), color='black')
    result = analyze_face(img)
    assert result["gender"] == "female"
    assert len(result["embedding"]) == 512
