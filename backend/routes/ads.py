

from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse
from config import db
import os, shutil, uuid

router = APIRouter()

# ---------------------------
# Helper: convert MongoDB doc → JSON
# ---------------------------
def serialize_ad(ad):
    ad["_id"] = str(ad["_id"])
    return ad

# ---------------------------
# Get all adsa
# ---------------------------
@router.get("/ads")
async def get_ads():
    print("📢 /ads route called!")  # DEBUG
    ads = await db.ads.find().to_list(100)
    print(f"📢 Found {len(ads)} ads in DB")  # DEBUG
    ads = [serialize_ad(ad) for ad in ads]
    return JSONResponse(content=ads)

# ---------------------------
# Create new ad
# ---------------------------
@router.post("/ads")
async def create_ad(
    name: str = Form(...),
    description: str = Form(""), 
    video: UploadFile = File(...),
    image: UploadFile = File(...),
):
    print(f"📢 Uploading new ad: {name}")  # DEBUG

    # Directories
    video_dir = "static/videos"
    image_dir = "static/images"
    os.makedirs(video_dir, exist_ok=True)
    os.makedirs(image_dir, exist_ok=True)

    # Create unique ID for filenames
    ad_id = str(uuid.uuid4())

    # ---- Save Video ----
    video_ext = os.path.splitext(video.filename)[1]  # keep .mp4/.mov/etc
    video_filename = f"{ad_id}_video{video_ext}"
    video_path = os.path.join(video_dir, video_filename)
    with open(video_path, "wb") as buffer:
        shutil.copyfileobj(video.file, buffer)
    print(f"📢 Video saved at {video_path}")

    # ---- Save Image ----
    image_ext = os.path.splitext(image.filename)[1]  # keep .png/.jpg
    image_filename = f"{ad_id}_image{image_ext}"
    image_path = os.path.join(image_dir, image_filename)
    with open(image_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)
    print(f"📢 Image saved at {image_path}")

    # URLs for frontend
    video_url = f"/static/videos/{video_filename}"
    image_url = f"/static/images/{image_filename}"

    # Save to MongoDB
    ad_doc = {
        "name": name,
        "description": description, 
        "videoUrl": video_url,
        "imageUrl": image_url,
    }
    result = await db.ads.insert_one(ad_doc)
    ad_doc["_id"] = str(result.inserted_id)

    print("📢 Ad inserted with ID:", ad_doc["_id"])
    return JSONResponse(content=ad_doc)
