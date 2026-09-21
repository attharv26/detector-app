import os
import cloudinary
import cloudinary.uploader
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Enable CORS to allow requests from your frontend application
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://symphonious-churros-b7bbf9.netlify.app"],  # Change to your specific frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Cloudinary securely using environment variables
# (Make sure to add CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, and CLOUDINARY_API_SECRET
# in your hosting provider's dashboard environment settings)
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True,
)


@app.post("/upload-image")
async def upload_image(file: UploadFile = File(...)):
  try:
    # Read the incoming image file bytes from the frontend request
    file_bytes = await file.read()

    # Upload the image directly into Cloudinary memory under a specific folder
    upload_result = cloudinary.uploader.upload(
        file_bytes, folder="scanner_app_uploads"
    )

    # Extract the secure public URL of the saved image
    image_url = upload_result.get("secure_url")

    return {
        "status": "success",
        "url": image_url,
        "message": "Image captured and stored successfully in Cloudinary!",
    }

  except Exception as e:
    raise HTTPException(
        status_code=500, detail=f"Failed to upload image: {str(e)}"
    )