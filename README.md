# Validia Recruiting Challenge

Objective: Develop a FastAPI application that allows users to upload an image and generates a "facial profile" that describes key characteristics of the face which define its reality.
Timeframe: You have until June 29th! Just let us know when you start so we can keep track. The project in total shouldn't take longer than 3 days, however we understand some may have busy schedules!

Tasks:
1. Setup FastAPI Server: Develop a basic FastAPI server to handle image uploads.
2. Facial Analysis: Implement a method (or use a library) to analyze facial features from the uploaded image.
3. API Endpoint: Create an endpoint that receives an image, processes it to extract facial features, and saves a "profile" of these features.
4. Create a use case showing how this "facial profile" could be used to identify a separate image as real.


## What we are looking for:

1. Well structured code
2. A Creative Solution that shows an understanding of the problem
3. Documentation supporting why you made the decisions you made!

## Bonus Points
1. Additional API endpoints that support the detection aspect (using the profile)
2. Deep documentation on how to use the API using the FastAPI docs
3. Highly creative profile creation

# Facial Profile Creator Project Skeleton Code

## Development Setup
- Python 3.8+
- FastAPI
- Libraries for image processing and facial analysis (e.g., OpenCV, dlib)

## Installation
1. Clone the repository:
```git clone https://github.com/Identif-AI/recruiting-challenge.git ```
2. Install dependencies:
``` pip install -r requirements.txt ```
3. Run the server locally:
``` uvicorn app.main --reload```

## Usage
- Navigate to `http://127.0.0.1:8000/docs` to see the API documentation and interact with the API.


## Skeleton Code

```
from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel
from io import BytesIO
from PIL import Image

app = FastAPI()

class Profile(BaseModel):
    description: str

@app.post("/create-profile", response_model=Profile)
async def create_profile(file: UploadFile = File(...)):
    img = Image.open(BytesIO(await file.read()))
    # Placeholder for facial analysis
    profile_description = analyze_face(img)
    return {"description": profile_description}

def analyze_face(image):
    # Implement facial analysis logic or use a model/library
    # Example: "Face with high cheekbones, oval shape, and light brown eyes."
    return "Example facial profile based on analysis."


```



