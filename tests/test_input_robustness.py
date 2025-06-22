"""
Pytest test cases for Input & API Robustness Edge Cases in facial verification.
"""
import pytest
import requests
import os
import threading

API_URL = "http://localhost:8000/v1/verify-profile"
TEST_DIR = "images/test/"

@pytest.mark.parametrize("filename,mimetype,expected_status", [
    ("test.txt", "text/plain", 415),
])
def test_wrong_mime(tmp_path, filename, mimetype, expected_status):
    # Create a dummy text file
    file_path = tmp_path / filename
    file_path.write_text("This is not an image.")
    with open(file_path, "rb") as f:
        resp = requests.post(API_URL, files={"file": (filename, f, mimetype)})
    assert resp.status_code == expected_status

def test_huge_image(tmp_path):
    big_path = tmp_path / "huge_dummy.jpg"
    big_path.write_bytes(b"0" * 21_000_000)  # 21 MB
    with open(big_path, "rb") as f:
        resp = requests.post(API_URL, files={"file": ("huge_dummy.jpg", f, "image/jpeg")})
    assert resp.status_code in (413, 400, 422)  # Acceptable: Payload Too Large or Unprocessable

def test_non_face_image():
    img_path = os.path.join(TEST_DIR, "non_face.jpg")
    if not os.path.exists(img_path):
        pytest.skip("non_face.jpg not found.")
    with open(img_path, "rb") as f:
        resp = requests.post(API_URL, files={"file": ("non_face.jpg", f, "image/jpeg")})
    assert resp.status_code == 422


def test_malicious_filename():
    img_path = os.path.join(TEST_DIR, "11.jpeg")
    if not os.path.exists(img_path):
        pytest.skip("11.jpeg not found for malicious filename test.")
    with open(img_path, "rb") as f:
        resp = requests.post(API_URL, files={"file": ("../../etc/passwd", f, "image/jpeg")})
    assert resp.status_code in (200, 422, 400)  # Should not crash or leak files


def test_concurrency():
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

def test_multiple_faces():
    img_path = os.path.join(TEST_DIR, "multiple_faces.jpg")
    if not os.path.exists(img_path):
        pytest.skip("multiple_faces.jpeg not found for multiple faces test.")
    with open(img_path, "rb") as f:
        resp = requests.post(API_URL, files={"file": (img_path, f, "image/jpeg")})
    # Should return 422 (unprocessable entity) or 400 if multiple faces are not allowed
    assert resp.status_code in (422, 400)
