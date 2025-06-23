import json
from .conftest import client, create_test_image

def test_create_profile_success(monkeypatch):
    # Patch analyze_face to return a fake embedding and gender
    monkeypatch.setattr(
        'app.routers.profile_create.analyze_face',
        lambda img: {"embedding": [0.1]*512, "gender": "male"}
    )
    img_buf = create_test_image()
    response = client.post(
        "/create-profile",
        files={"file": ("test.jpg", img_buf, "image/jpeg")},
        data={"user_id": "testuser", "name": "Test User", "extra": json.dumps({"foo": "bar"})}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["error"] is None
    d = data["data"]
    assert d["gender"] == "male"
    assert d["user_id"] == "testuser"
    assert d["name"] == "Test User"
    assert d["extra"]["foo"] == "bar"
    assert len(d["embedding"]) == 512

def test_create_profile_no_extra(monkeypatch):
    # Patch analyze_face to return a fake embedding and gender
    monkeypatch.setattr(
        'app.routers.profile_create.analyze_face',
        lambda img: {"embedding": [0.1]*512, "gender": "male"}
    )
    img_buf = create_test_image()
    response = client.post(
        "/create-profile",
        files={"file": ("test.jpg", img_buf, "image/jpeg")},
        data={"user_id": "testuser", "name": "Test User"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["error"] is None
    d = data["data"]
    assert d["gender"] == "male"
    assert d["user_id"] == "testuser"
    assert d["name"] == "Test User"
    assert d["extra"] is None
    assert len(d["embedding"]) == 512

def test_create_profile_invalid_image():
    from .conftest import client
    import io
    response = client.post(
        "/create-profile",
        files={"file": ("bad.txt", io.BytesIO(b"notanimage"), "text/plain")}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert data["data"] is None
    assert data["error"]["code"] == 400
    assert "Invalid image file" in data["error"]["message"]

def test_create_profile_missing_file():
    response = client.post("/create-profile", data={"user_id": "u1"})
    assert response.status_code == 422 or response.status_code == 200
    if response.status_code == 200:
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == 400

def test_create_profile_face_analysis_error(monkeypatch):
    def raise_error(img):
        raise RuntimeError("Face model error!")
    monkeypatch.setattr('app.routers.profile_create.analyze_face', raise_error)
    img_buf = create_test_image()
    response = client.post(
        "/create-profile",
        files={"file": ("test.jpg", img_buf, "image/jpeg")},
        data={"user_id": "u1"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == 500
    assert "Face analysis failed" in data["error"]["message"]

def test_create_profile_chromadb_error(monkeypatch):
    monkeypatch.setattr(
        'app.routers.profile_create.analyze_face',
        lambda img: {"embedding": [0.1]*512, "gender": "male"}
    )
    class FakeChromaDB:
        def add_embedding(self, *a, **kw):
            raise RuntimeError("ChromaDB is down!")
    monkeypatch.setattr('app.routers.profile_create.chromadb_service', FakeChromaDB())
    img_buf = create_test_image()
    response = client.post(
        "/create-profile",
        files={"file": ("test.jpg", img_buf, "image/jpeg")},
        data={"user_id": "u1"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == 500
    assert "Failed to store profile in vector database" in data["error"]["message"]
