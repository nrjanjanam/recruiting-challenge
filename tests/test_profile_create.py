import json
import pytest
import requests
import os
import threading

API_URL = "http://localhost:8000/v1/create-profile"
TEST_DIR = "images/test/"

@pytest.mark.parametrize("filename,mimetype,expected_status", [
    ("test.txt", "text/plain", 415),
])
def test_wrong_mime_create(tmp_path, filename, mimetype, expected_status):
    file_path = tmp_path / filename
    file_path.write_text("This is not an image.")
    with open(file_path, "rb") as f:
        resp = requests.post(API_URL, files={"file": (filename, f, mimetype)})
    assert resp.status_code == expected_status

def test_huge_image_create(tmp_path):
    big_path = tmp_path / "huge_dummy.jpg"
    big_path.write_bytes(b"0" * 21_000_000)  # 21 MB
    with open(big_path, "rb") as f:
        resp = requests.post(API_URL, files={"file": ("huge_dummy.jpg", f, "image/jpeg")})
    assert resp.status_code in (413, 400, 422)

def test_non_face_image_create():
    img_path = os.path.join(TEST_DIR, "non_face.jpg")
    if not os.path.exists(img_path):
        pytest.skip("non_face.jpg not found.")
    with open(img_path, "rb") as f:
        resp = requests.post(API_URL, files={"file": ("non_face.jpg", f, "image/jpeg")})
    assert resp.status_code == 422

def test_malicious_filename_create():
    img_path = os.path.join(TEST_DIR, "11.jpeg")
    if not os.path.exists(img_path):
        pytest.skip("11.jpeg not found for malicious filename test.")
    with open(img_path, "rb") as f:
        resp = requests.post(API_URL, files={"file": ("../../etc/passwd", f, "image/jpeg")})
    assert resp.status_code in (200, 422, 400)

def test_concurrency_create():
    img_path = os.path.join(TEST_DIR, "12.jpeg")
    if not os.path.exists(img_path):
        pytest.skip("12.jpeg not found for concurrency test.")
    results = []
    def send_req():
        with open(img_path, "rb") as f:
            resp = requests.post(API_URL, files={"file": ("12.jpeg", f, "image/jpeg")})
            results.append(resp.status_code)
    threads = [threading.Thread(target=send_req) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert all(code in (200, 422, 400) for code in results)

def test_multiple_faces_create():
    img_path = os.path.join(TEST_DIR, "multiple_faces.jpg")
    if not os.path.exists(img_path):
        pytest.skip("multiple_faces.jpeg not found for multiple faces test.")
    with open(img_path, "rb") as f:
        resp = requests.post(API_URL, files={"file": (img_path, f, "image/jpeg")})
    assert resp.status_code in (422, 400)

def test_create_profile_empty_file():
    resp = requests.post(API_URL, files={"file": ("empty.jpg", b"", "image/jpeg")})
    assert resp.status_code in (415, 422)

def test_create_profile_no_file_field():
    resp = requests.post(API_URL, data={"user_id": "u1"})
    assert resp.status_code == 422

def test_create_profile_unsupported_media_type(tmp_path):
    file_path = tmp_path / "file.gif"
    file_path.write_bytes(b"GIF89a")
    with open(file_path, "rb") as f:
        resp = requests.post(API_URL, files={"file": ("file.gif", f, "image/gif")})
    assert resp.status_code in (415, 422)

def test_create_profile_large_metadata(tmp_path):
    file_path = tmp_path / "1.jpeg"
    file_path.write_bytes(b"\xff\xd8\xff")  # minimal JPEG header
    large_extra = "x" * 100_000
    with open(file_path, "rb") as f:
        resp = requests.post(
            API_URL,
            files={"file": ("1.jpeg", f, "image/jpeg")},
            data={"user_id": "u1", "name": "Test", "extra": large_extra}
        )
    assert resp.status_code in (200, 413, 415, 422)

def test_create_profile_invalid_json_extra(tmp_path):
    file_path = tmp_path / "1.jpeg"
    file_path.write_bytes(b"\xff\xd8\xff")
    with open(file_path, "rb") as f:
        resp = requests.post(
            API_URL,
            files={"file": ("1.jpeg", f, "image/jpeg")},
            data={"user_id": "u1", "name": "Test", "extra": "{notjson}"}
        )
    assert resp.status_code in (415, 422)
