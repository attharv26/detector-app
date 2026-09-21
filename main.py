import io
import os
import cloudinary
import cloudinary.uploader
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, ImageDraw, ImageFont

app = FastAPI()

# Enable CORS for your frontend application
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Cloudinary using Render's environment variables
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True,
)

# --- BANNER CONFIGURATION ---
CAPTION_TEXT = "LODU HALL OF FAME"
BANNER_HEIGHT = 100
BG_COLOR = (255, 0, 0)  # Static Red Background
TEXT_COLOR = (255, 255, 0)  # Static Yellow Text
FONT_PATH = "MTCORSVA.TTF"


def process_image_with_banner(image_bytes: bytes) -> bytes:
  """Adds a red caption banner with yellow text to the top of the image bytes,

  using your exact static font size configuration without shrinking.
  """
  try:
    # 1. Open image from raw bytes
    original_img = Image.open(io.BytesIO(image_bytes))
    orig_width, orig_height = original_img.size

    # 2. Create a new image with extra height for the banner
    new_height = orig_height + BANNER_HEIGHT
    new_img = Image.new("RGB", (orig_width, new_height), BG_COLOR)

    # 3. Paste original image below the banner
    new_img.paste(original_img, (0, BANNER_HEIGHT))

    # 4. Draw setup
    draw = ImageDraw.Draw(new_img)

    # Fixed font size configuration
    font_size = int(BANNER_HEIGHT * 0.45)

    try:
      font = ImageFont.truetype(FONT_PATH, font_size)
    except IOError:
      font = ImageFont.load_default()

    # Get final text dimensions for centering
    bbox = draw.textbbox((0, 0), CAPTION_TEXT, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # 5. Center the text horizontally and vertically inside the banner
    text_x = max(20, (orig_width - text_width) // 2)
    text_y = (BANNER_HEIGHT - text_height) // 2 - bbox[1]

    # Draw the caption text
    draw.text((text_x, text_y), CAPTION_TEXT, fill=TEXT_COLOR, font=font)

    # 6. Save modified image to bytes buffer instead of a file
    output_buffer = io.BytesIO()
    new_img.save(output_buffer, format="JPEG")
    output_buffer.seek(0)
    return output_buffer.read()

  except Exception as e:
    print(f"Image processing error: {e}")
    # Fallback to original bytes if banner processing fails
    return image_bytes


@app.post("/upload-image")
async def upload_image(file: UploadFile = File(...)):
  try:
    # Read incoming image from frontend request
    file_bytes = await file.read()

    # Process image to add the custom red/yellow banner
    processed_image_bytes = process_image_with_banner(file_bytes)

    # Upload the edited image directly to Cloudinary
    upload_result = cloudinary.uploader.upload(
        processed_image_bytes, folder="scanner_app_uploads"
    )

    image_url = upload_result.get("secure_url")

    return {
        "status": "success",
        "url": image_url,
        "message": (
            "Image processed with banner and stored successfully in Cloudinary!"
        ),
    }

  except Exception as e:
    raise HTTPException(
        status_code=500, detail=f"Failed to process and upload image: {str(e)}"
    )