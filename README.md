# Validia Recruiting Challenge

## Overview

This project is a robust, production-grade FastAPI and Streamlit application for multi-pose facial profile creation and verification. It guides users through a five-pose (frontal, left, right, up, down) selfie capture process, performs real-time quality control (QC) on each pose, and stores a high-quality, pose-diverse facial template for future verification. The system is designed for high security and accuracy, following best practices from NIST, ISO, and state-of-the-art face recognition research.


## Demo Walkthrough

A full walkthrough of the application is available on YouTube:

Click [this link](https://youtu.be/fuGnz6R5_Es) to watch the demo video.

## Features

- **Five-Pose Guided Enrollment:**
  - Users are guided to capture selfies in five specific poses: Frontal, Left, Right, Up, Down.
  - Each pose is QC-checked for blur, brightness, embedding quality, anti-spoofing, and correct pose angle.
  - Only high-quality, correctly posed images are accepted.
- **Real-Time Feedback:**
  - Users receive instant feedback if a pose is rejected (e.g., "blurry", "bad lighting", "wrong pose").
  - UI guides the user with clear instructions for each pose.
- **Metadata Collection:**
  - User is prompted for their name before enrollment; this is stored with the profile.
- **Robust Backend:**
  - FastAPI endpoints for per-pose QC and final profile creation.
  - Embeddings are always stacked in the order [frontal, left, right, up, down].
  - All data is stored in ChromaDB with full metadata.
- **Modern UI:**
  - Streamlit frontend with a pose wheel, clean design, and sidebar/menus hidden at all times for a distraction-free experience.
  - Automatic redirect to landing page after successful enrollment.
- **Security:**
  - Anti-spoofing (PAD) checks on every pose using DeepFace.
  - Multi-pose template reduces pose-variance error and increases verification accuracy.


## Installation & Setup

### Prerequisites
- Python 3.12+
- [Poetry](https://python-poetry.org/) for dependency management

### Clone and Install
```bash
git clone https://github.com/Identif-AI/recruiting-challenge.git
cd recruiting-challenge
poetry install
```

### Run the Backend
```bash
poetry run uvicorn app.main:app
```

### Run the Streamlit UI
```bash
poetry run streamlit run ui/landing.py
```


## Usage

1. **Open the Streamlit UI** (usually at http://localhost:8501)
2. **Enter your name** on the enrollment page.
3. **Follow the guided pose capture** for Frontal, Left, Right, Up, Down. Each pose must pass QC to proceed.
4. **After all five are accepted,** your profile is created and you are redirected to the landing page.
5. **Verification** can be performed via the verify page.


## API Endpoints

### API Documentation
`GET /docs`
- Interactive Swagger UI for exploring and testing all available endpoints.
- Automatically generated from FastAPI with detailed request/response schemas and descriptions.

### Per-Pose QC
`POST /enroll/qc/{bucket}`
- Accepts: Image file (one pose at a time)
- Returns: `{ok: bool, reason: str}`
- QC checks: pose, blur, brightness, embedding norm, anti-spoofing

### Profile Creation (Five Poses)
`POST /v1/profile-create-5poses`
- Accepts: JSON with `frames` (dict of pose name to RGB array), `name`, and optional metadata
- Returns: `{profile_id, num_frames, name, ...}`
- Embeddings are always stacked in [frontal, left, right, up, down] order

### Profile Creation (Single Image)
`POST /v1/create-profile`
- Accepts: Image file, with optional user_id, name, and extra metadata
- Returns: `{embedding, gender, user_id, name, extra, ...}`
- Stores a single-pose profile in ChromaDB

### Profile Verification
`POST /v1/verify-profile`
- Accepts: Image file
- Returns: `{match: bool, semantic_distance, euclidean_distance, cosine_similarity, message, matched_profile, ...}`
- Uses vector search with distance metrics for robust matching


## Project Structure

```
recruiting-challenge/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── quality_check.py
│   │   ├── profile_create_5poses.py
│   │   ├── profile_create.py
│   │   ├── profile_verify.py
│   │   ├── register.py
│   │   └── ...
│   ├── services/
│   │   ├── __init__.py
│   │   ├── facial_analysis.py
│   │   ├── chromadb_service.py
│   │   ├── spoof_model.py
│   │   ├── logging_config.py
│   │   ├── quality_check_utils.py
│   │   └── ...
│   └── ...
├── ui/
│   ├── landing.py
│   └── pages/
│       ├── enroll.py
│       └── verify.py
├── models/
│   ├── age_gender_model.h5
│   ├── anti_spoofing_model.h5
│   └── ...
├── images/
│   ├── test/
│   └── train/
├── tests/
│   ├── __init__.py
│   ├── test_facial_analysis.py
│   ├── test_profile_create.py
│   ├── test_profile_verify.py
│   └── ...
├── conf/
│   └── full_runtime.yaml
├── chromadb_data/
│   └── ...
├── README.md
├── pyproject.toml
├── poetry.lock
└── ...
```

- `app/routers/` — FastAPI endpoints (QC, profile creation, verification, etc.)
- `app/services/` — Core logic: facial analysis, ChromaDB, spoofing, logging, QC helpers
- `ui/` — Streamlit UI (landing page, enrollment, verification)
- `models/` — Pretrained models (age/gender, anti-spoofing, etc.)
- `images/` — Example/test images
- `tests/` — Unit and integration tests
- `conf/` — Configuration files
- `chromadb_data/` — ChromaDB vector store data



## Key Implementation Details

- **Order Guarantee:**
  - Both UI and backend use a dictionary mapping pose names to frames. Backend enforces the presence and order of all five poses.
- **QC Logic:**
  - Pose angles are checked using InsightFace 3D pose estimation.
  - Blur is checked via Laplacian variance (≥100).
  - Brightness is checked (mean 70-180).
  - Embedding norm (≥25) ensures quality.
  - Anti-spoofing (PAD) must be >0.1.
- **Matching Logic:**
  - Vector search in ChromaDB is used for candidate retrieval, but final match is confirmed using distance metrics (cosine/euclidean) for accuracy.
  - This avoids false positives (e.g., Tom Cruise matching with 2.jpeg) and ensures robust verification.
- **UI/UX:**
  - User is guided for each pose, and only allowed to proceed if QC passes.
  - After enrollment, user is redirected to the landing page.
- **Security:**
  - Anti-spoofing checks are run on every pose and during verification.
  - Only real faces are accepted; spoofed or low-quality images are rejected.
- **Testing:**
  - Comprehensive tests for facial analysis, embedding verification, and API endpoints.
  - Test cases include with proper HTTP Codes returned:
    - Face match (positive verification)
    - No match (negative verification)
    - No face detected
    - Multiple faces detected
    - Invalid file type (415)
    - Oversized file (413)
    - Malformed or missing fields (422)



## My Flow & Design Decisions

### Enrollment & QC
- The user is guided through five specific poses, with real-time feedback for each.
- Each pose is checked for:
  - **Blur** (Laplacian variance)
  - **Brightness** (mean pixel value)
  - **Anti-spoofing** (PAD score)
- Only after all three pass, the profile is created and stored.

### Matching & Verification
- **Vector search** is used for fast candidate retrieval from ChromaDB.
- **Distance-based confirmation** (cosine/euclidean) is used to avoid false positives:
  - Example: Side portraits or celebrity images (e.g., Tom Cruise, Chris Hemsworth) may be close in vector space, but distance metrics help prevent incorrect matches.
- **Anti-spoofing** is run on the probe image during verification; only real faces are accepted.

### UI/UX
- Streamlit UI is designed for clarity and minimalism. User is redirected to landing page after successful enrollment. Proceed with enrollment first and then to verification.

### Lessons Learned & Challenges
- **Side Portraits:**
  - Matching can be tricky for side portraits; pose-specific embeddings and strict QC help mitigate this.
  - Some celebrity images (e.g., Chris Hemsworth) did not match as expected, highlighting the importance of pose and embedding quality.
- **Pose Correctness (Yaw/Pitch):**
  - Attempted to use yaw/pitch from InsightFace for pose correctness, but could not reliably distinguish left/right due to mirroring (both gave positive values). This check was not implemented in production.
- **Embedding Model Exploration (AdaFace):**
  - Attempted to use AdaFace for facial profile embeddings for improved robustness, but was unable to configure it due to issues with the config file. Tried multiple sources and approaches, but could not proceed with integration.
- **Other Approaches Tried:**
  - Explored using additional facial attributes (age, emotion) for profile storage, but found them too variable for reliable identification.
  - Considered merging biometric metadata with embeddings, but only stable features were ultimately used.
- **Vector Search vs. Distance Metrics:**
  - Relying solely on vector search can lead to incorrect matches (e.g., Tom Cruise matched with 2.jpeg).
  - Final match confirmation using cosine/euclidean distance is essential for accuracy.
- **Quality Control:**
  - Strict QC on blur and brightness is critical for robust enrollment and verification. Blur images didn't give good quality face profile (due to low quality embeddigs) which creates problems in verification process.

## Additional Design Notes & Decisions

- **Age and Emotion Features:**
  - Age and emotion are ignored for profile storage, as they can change between photos and are not reliable for identity.
  - Only robust, pose-invariant facial embeddings are stored.
- **Biometric Metadata:**
  - Considered merging biometric metadata with facial embeddings for richer profiles, but only stable features are used for matching.
- **Vector Store Choice:**
  - ChromaDB is used for storing and retrieving facial profiles due to its efficient vector search capabilities.
- **Standardized API Output:**
  - All endpoints return a standardized response format for consistency and easier frontend integration.
- **Port Selection:**
  - The backend auto-selects an available port in the 8000 series if 8000 is unavailable.
- **Modularization:**
  - Codebase is modularized for maintainability: routers, services, and utilities are separated.
- **Testing:**
  - Pytest-based tests cover at least four core cases (face match, no match, no face, multiple faces).
  - Near 100% test coverage; easy to add more tests for edge cases or new features.
- **Embedding Normalization:**
  - Direct thresholding on raw vector DB results is avoided because most face models output unnormalized embeddings (L2 norms can be very large).
  - Cosine or Euclidean distance is used for final match confirmation, not just vector search proximity.
- **Edge Cases & Demographic Parity:**
  - Tested with diverse images (skin tones, genders, ages, hair types) for fairness; system shows equal pass rates.
  - Side portraits and celebrity images (e.g., Chris Hemsworth, Oprah Winfrey) tested for robustness.
  - Tilted photos are rejected by the spoof check as not real faces, improving security.

## Improvements & Future Work
- Add voice and eye prints - multimodal biometrics! DeepIrisV3 ONNX and 	ECAPA-TDNN on HF (speechbrain/spkrec-ecapa-voxceleb) store voice print and iris print respectively, makes the face profile stonger.
- Maybe greyscale everything and work on it because the dress colors, skintone, eye color, haircolor is what people keep changing, the RGB embeddings may cause some restriction.
- Find models that do quality checks (MagFace has ID quality magnitude vector) - so I can remove the basic norm check based blur and quality check
- Add support for additional metadata prolly.



