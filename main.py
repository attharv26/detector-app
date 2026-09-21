import io
import os
import cloudinary
import cloudinary.uploader
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, ImageDraw, ImageFont

app = FastAPI()

# Enable CORS for your frontend
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
BG_COLOR = (255, 0, 0)  # Red Background
TEXT_COLOR = (255, 255, 0)  # Yellow Text
FONT_PATH = "MTCORSVA.TTF"


def process_image_with_banner(image_bytes: bytes) -> bytes:
  """Adds a red caption banner with yellow text to the top of the image bytes."""
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
    max_text_width = orig_width - 40
    font_size = int(BANNER_HEIGHT * 0.45)

    # Dynamically find the right font size
    while font_size > 10:
      try:
        font = ImageFont.truetype(FONT_PATH, font_size)
      except IOError:
        font = ImageFont.load_default()
        break

      bbox = draw.textbbox((0, 0), CAPTION_TEXT, font=font)
      text_width = bbox[2] - bbox[0]

      if text_width <= max_text_width:
        break
      font_size -= 2

    # Final text dimensions for centering
    bbox = draw.textbbox((0, 0), CAPTION_TEXT, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    text_x = max(20, (orig_width - text_width) // 2)
    text_y = (BANNER_HEIGHT - text_height) // 2 - bbox[1]

    # Draw text
    draw.text((text_x, text_y), CAPTION_TEXT, fill=TEXT_COLOR, font=font)

    # 5. Save modified image to bytes buffer instead of a file
    output_buffer = io.BytesIO()
    new_img.save(output_buffer, format="JPEG")
    output_buffer.seek(0)
    return output_buffer.read()

  except Exception as e:
    print(f"Image processing error: {e}")
    # Fallback: if banner script fails, return original bytes so upload doesn't break
    return image_bytes


@app.post("/upload-image")
async def upload_image(file: UploadFile = File(...)):
  try:
    # Read incoming image from frontend
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