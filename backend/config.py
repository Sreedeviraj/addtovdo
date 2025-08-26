

# import motor.motor_asyncio

# # MongoDB Atlas connection
# MONGO_DETAILS = "mongodb+srv://sreedeviraj:sree123@cluster0.oic5wy1.mongodb.net/parkease?retryWrites=true&w=majority&appName=Cluster0"

# client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_DETAILS)
# db = client["add2video"]   # expose db
# ads_collection = db["ads"] 

import os
import motor.motor_asyncio
from motor.motor_asyncio import AsyncIOMotorGridFSBucket
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse

# ------------------------------
# MongoDB connection
# ------------------------------
MONGO_DETAILS = os.environ.get(
    "MONGODB_URI",
    "mongodb+srv://sreedeviraj:sree123@cluster0.oic5wy1.mongodb.net/parkease?retryWrites=true&w=majority&appName=Cluster0"
)

client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_DETAILS)
db = client["add2video"]
ads_collection = db["ads"]

# ------------------------------
# Initialize GridFS
# ------------------------------
fs = AsyncIOMotorGridFSBucket(db)

# ------------------------------
# FastAPI app
# ------------------------------
app = FastAPI()

@app.post("/api/ads")
async def create_ad(
    name: str = Form(...),
    description: str = Form(""),
    image: UploadFile = File(...),
    video: UploadFile = File(...),
):
    # Store image in GridFS
    image_id = await fs.upload_from_stream(
        image.filename, 
        await image.read(),
        metadata={"content_type": image.content_type}
    )
    
    # Store video in GridFS
    video_id = await fs.upload_from_stream(
        video.filename, 
        await video.read(),
        metadata={"content_type": video.content_type}
    )
    
    # Save references in MongoDB
    doc = {
        "name": name,
        "description": description,
        "imageId": str(image_id),
        "videoId": str(video_id),
        "imageUrl": f"/api/images/{image_id}",
        "videoUrl": f"/api/videos/{video_id}",
    }

    result = await ads_collection.insert_one(doc)
    doc["_id"] = str(result.inserted_id)

    return JSONResponse(content=doc)



