import os
import shutil
import uuid
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Enable CORS to allow requests from your frontend application
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to restrict origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directory to save uploaded images
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.post("/upload-image")
async def upload_image(file: UploadFile = File(...)):
  try:
    # Generate unique filename to avoid overwriting
    file_extension = (
        file.filename.split(".")[-1] if "." in file.filename else "jpg"
    )
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    # Save the file to disk
    with open(file_path, "wb") as buffer:
      shutil.copyfileobj(file.file, buffer)

    return {
        "status": "success",
        "filename": unique_filename,
        "message": "Image captured and stored successfully",
    }
  except Exception as e:
    raise HTTPException(
        status_code=500, detail=f"Failed to save image: {str(e)}"
    )