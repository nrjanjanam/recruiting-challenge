from .conftest import client, create_test_image

def test_verify_profile_no_match(monkeypatch):
    # Patch analyze_face and ChromaDB
    monkeypatch.setattr(
        'app.routers.profile_verify.analyze_face',
        lambda img: {"embedding": [0.1]*512, "gender": "male"}
    )
    class FakeChromaDB:
        def query_embedding(self, embedding, n_results=1):
            return {"ids": [[]], "distances": [[]], "metadatas": [[]]}
    monkeypatch.setattr('app.routers.profile_verify.chromadb_service', FakeChromaDB())
    img_buf = create_test_image()
    response = client.post(
        "/verify-profile",
        files={"file": ("test.jpg", img_buf, "image/jpeg")}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["error"] is None
    d = data["data"]
    assert d["match"] is False
    assert d["message"] == "No match found."

def test_verify_profile_no_match_branch(monkeypatch):
    # Patch analyze_face and ChromaDBService to return no match
    monkeypatch.setattr(
        'app.routers.profile_verify.analyze_face',
        lambda img: {"embedding": [0.1]*512, "gender": "male"}
    )
    class FakeChromaDB:
        def query_embedding(self, embedding, n_results=1):
            return {"ids": [[]], "distances": [[]], "metadatas": [[]]}
    monkeypatch.setattr('app.routers.profile_verify.chromadb_service', FakeChromaDB())
    img_buf = create_test_image()
    response = client.post(
        "/verify-profile",
        files={"file": ("test.jpg", img_buf, "image/jpeg")}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["error"] is None
    d = data["data"]
    assert d["match"] is False
    assert d["message"] == "No match found."
    assert d["distance"] is None
    assert d["matched_profile"] is None

def test_verify_profile_match(monkeypatch):
    monkeypatch.setattr(
        'app.routers.profile_verify.analyze_face',
        lambda img: {"embedding": [0.1]*512, "gender": "male"}
    )
    class FakeChromaDB:
        def query_embedding(self, embedding, n_results=1):
            return {
                "ids": [["abc"]],
                "distances": [[0.5]],
                "metadatas": [[{"user_id": "testuser", "gender": "male"}]]
            }
    monkeypatch.setattr('app.routers.profile_verify.chromadb_service', FakeChromaDB())
    img_buf = create_test_image()
    response = client.post(
        "/verify-profile",
        files={"file": ("test.jpg", img_buf, "image/jpeg")}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["error"] is None
    d = data["data"]
    assert d["match"] is True
    assert d["matched_profile"]["user_id"] == "testuser"

def test_verify_profile_invalid_image():
    response = client.post(
        "/verify-profile",
        files={"file": ("bad.txt", b"notanimage", "text/plain")}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert data["data"] is None
    assert data["error"]["code"] == 400
    assert "Invalid image file" in data["error"]["message"]

def test_verify_profile_face_analysis_error(monkeypatch):
    # Simulate face analysis raising an exception
    def raise_error(img):
        raise RuntimeError("Face model error!")
    monkeypatch.setattr('app.routers.profile_verify.analyze_face', raise_error)
    img_buf = create_test_image()
    response = client.post(
        "/verify-profile",
        files={"file": ("test.jpg", img_buf, "image/jpeg")}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert data["data"] is None
    assert data["error"]["code"] == 500
    assert "Face analysis failed" in data["error"]["message"]

def test_verify_profile_chromadb_error(monkeypatch):
    monkeypatch.setattr(
        'app.routers.profile_verify.analyze_face',
        lambda img: {"embedding": [0.1]*512, "gender": "male"}
    )
    class FakeChromaDB:
        def query_embedding(self, embedding, n_results=1):
            raise RuntimeError("ChromaDB is down!")
    monkeypatch.setattr('app.routers.profile_verify.chromadb_service', FakeChromaDB())
    img_buf = create_test_image()
    response = client.post(
        "/verify-profile",
        files={"file": ("test.jpg", img_buf, "image/jpeg")}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert data["data"] is None
    assert data["error"]["code"] == 500
    assert "Failed to query vector database" in data["error"]["message"]
