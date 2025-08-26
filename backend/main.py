import os
import cv2
import numpy as np
import asyncio
import json
from fastapi import FastAPI, UploadFile, File, Form, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Dict, Optional
import base64
import io
from PIL import Image
import time
from bson import ObjectId
import shutil
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve uploaded files
os.makedirs("static/images", exist_ok=True)
os.makedirs("static/videos", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# MongoDB
MONGO_DETAILS = "mongodb+srv://sreedeviraj:sree123@cluster0.oic5wy1.mongodb.net/parkease?retryWrites=true&w=majority"
client = AsyncIOMotorClient(MONGO_DETAILS)
db = client["add2video"]
ads_collection = db["ads"]

# Store active WebSocket connections
active_connections: List[WebSocket] = []

# Store ORB detectors for each ad
orb_detectors = {}

# Track detection state for each connection
detection_states = {}

# Pydantic model for ad update
class AdUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

# Initialize ORB detectors for existing ads
async def initialize_orb_detectors():
    ads = await ads_collection.find({}).to_list(1000)
    for ad in ads:
        ad_id = str(ad["_id"])
        image_path = ad["imageUrl"].replace("/static/", "static/")
        
        if os.path.exists(image_path):
            marker = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            if marker is not None:
                # Resize image to standard size for consistent feature detection
                marker = cv2.resize(marker, (500, 500))
                orb = cv2.ORB_create(1000)  # Reduced features for faster detection
                kp_marker, des_marker = orb.detectAndCompute(marker, None)
                orb_detectors[ad_id] = {
                    "kp": kp_marker,
                    "des": des_marker,
                    "shape": marker.shape,
                    "video_url": ad["videoUrl"],
                    "name": ad["name"]
                }
                print(f"Initialized detector for ad {ad_id} with {len(kp_marker)} features")

@app.on_event("startup")
async def startup_event():
    await initialize_orb_detectors()

# GET all ads
@app.get("/api/ads")
async def get_ads():
    ads = await ads_collection.find({}).to_list(1000)
    for ad in ads:
        ad["_id"] = str(ad["_id"])
    return ads

# GET single ad
@app.get("/api/ads/{ad_id}")
async def get_ad(ad_id: str):
    try:
        ad = await ads_collection.find_one({"_id": ObjectId(ad_id)})
        if ad:
            ad["_id"] = str(ad["_id"])
            return ad
        else:
            raise HTTPException(status_code=404, detail="Ad not found")
    except:
        raise HTTPException(status_code=400, detail="Invalid ad ID")

# POST new ad
@app.post("/api/ads")
async def create_ad(
    name: str = Form(...),
    description: str = Form(""),
    image: UploadFile = File(...),
    video: UploadFile = File(...),
):
    # Save image
    image_path = os.path.join("static/images", image.filename)
    with open(image_path, "wb") as f:
        f.write(await image.read())
    image_url = f"/static/images/{image.filename}"

    # Save video
    video_path = os.path.join("static/videos", video.filename)
    with open(video_path, "wb") as f:
        f.write(await video.read())
    video_url = f"/static/videos/{video.filename}"

    # Insert into MongoDB
    doc = {
        "name": name,
        "description": description,
        "imageUrl": image_url,
        "videoUrl": video_url,
    }
    result = await ads_collection.insert_one(doc)
    doc_id = str(result.inserted_id)
    doc["_id"] = doc_id

    # Initialize ORB detector for the new ad
    marker = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if marker is not None:
        # Resize image to standard size for consistent feature detection
        marker = cv2.resize(marker, (500, 500))
        orb = cv2.ORB_create(1000)  # Reduced features for faster detection
        kp_marker, des_marker = orb.detectAndCompute(marker, None)
        orb_detectors[doc_id] = {
            "kp": kp_marker,
            "des": des_marker,
            "shape": marker.shape,
            "video_url": video_url,
            "name": name
        }
        print(f"Initialized detector for new ad {doc_id} with {len(kp_marker)} features")

    return JSONResponse({"message": "Ad created successfully", **doc})

# PUT update ad
@app.put("/api/ads/{ad_id}")
async def update_ad(ad_id: str, ad_update: AdUpdate):
    try:
        update_data = {k: v for k, v in ad_update.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No data provided for update")
        
        result = await ads_collection.update_one(
            {"_id": ObjectId(ad_id)},
            {"$set": update_data}
        )
        
        if result.modified_count == 1:
            # Update the detector if name changed
            if "name" in update_data and ad_id in orb_detectors:
                orb_detectors[ad_id]["name"] = update_data["name"]
            
            return JSONResponse({"message": "Ad updated successfully"})
        else:
            raise HTTPException(status_code=404, detail="Ad not found")
    except:
        raise HTTPException(status_code=400, detail="Invalid ad ID")

# DELETE ad
@app.delete("/api/ads/{ad_id}")
async def delete_ad(ad_id: str):
    try:
        # Get ad data first to delete files
        ad = await ads_collection.find_one({"_id": ObjectId(ad_id)})
        
        if ad:
            # Delete associated files
            if "imageUrl" in ad:
                image_path = ad["imageUrl"].replace("/static/", "static/")
                if os.path.exists(image_path):
                    os.remove(image_path)
            
            if "videoUrl" in ad:
                video_path = ad["videoUrl"].replace("/static/", "static/")
                if os.path.exists(video_path):
                    os.remove(video_path)
            
            # Remove from MongoDB
            result = await ads_collection.delete_one({"_id": ObjectId(ad_id)})
            
            if result.deleted_count == 1:
                # Remove from ORB detectors
                if ad_id in orb_detectors:
                    del orb_detectors[ad_id]
                
                return JSONResponse({"message": "Ad deleted successfully"})
            else:
                raise HTTPException(status_code=404, detail="Ad not found")
        else:
            raise HTTPException(status_code=404, detail="Ad not found")
    except:
        raise HTTPException(status_code=400, detail="Invalid ad ID")

# WebSocket endpoint for real-time detection
@app.websocket("/ws/detect")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    
    # Initialize detection state for this connection
    connection_id = id(websocket)
    detection_states[connection_id] = {
        "active_ad": None,
        "active_since": None,
        "last_position": None,
        "detection_threshold": 3,  # Reduced threshold for faster detection
    }
    
    # Initialize BFMatcher for faster performance
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    
    try:
        while True:
            # Receive base64 encoded image from client
            data = await websocket.receive_text()
            
            # Decode base64 to image
            image_data = base64.b64decode(data)
            image = Image.open(io.BytesIO(image_data))
            frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Preprocess frame for better feature detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (3, 3), 0)  # Light blur for noise reduction
            
            # Detect ads
            detected_ads = []
            
            # Initialize ORB for frame
            orb = cv2.ORB_create(800)  # Reduced features for faster detection
            kp_frame, des_frame = orb.detectAndCompute(gray, None)
            
            current_state = detection_states[connection_id]
            
            # If we have an active ad that was recently detected, check if it's still visible first
            if (current_state["active_ad"] and 
                current_state["active_since"] and 
                time.time() - current_state["active_since"] < 5):  # Active for 5 seconds max
                
                ad_id = current_state["active_ad"]
                detector = orb_detectors.get(ad_id)
                
                if detector and detector["des"] is not None and des_frame is not None:
                    # Quick check for the active ad
                    matches = bf.match(detector["des"], des_frame)
                    matches = sorted(matches, key=lambda x: x.distance)
                    
                    # If we still have a good match, use the last known position
                    if len(matches) > 10 and matches[0].distance < 50:
                        detected_ads.append({
                            "id": ad_id,
                            "videoUrl": detector["video_url"],
                            "name": detector["name"],
                            "status": "active"  # Indicate this is an active tracking
                        })
                        await websocket.send_text(json.dumps(detected_ads))
                        continue
            
            # If no active ad or active ad not found, check all ads
            if des_frame is not None and len(kp_frame) > 15:
                best_match = None
                best_match_score = 0
                
                for ad_id, detector in orb_detectors.items():
                    if detector["des"] is not None and len(detector["kp"]) > 8:
                        try:
                            # Use BFMatcher for speed
                            matches = bf.match(detector["des"], des_frame)
                            matches = sorted(matches, key=lambda x: x.distance)
                            
                            # Simple threshold based on good matches
                            good_matches = [m for m in matches if m.distance < 50]
                            
                            if len(good_matches) > 12:
                                # Calculate match quality score
                                match_score = len(good_matches) / len(detector["kp"]) if len(detector["kp"]) > 0 else 0
                                
                                if match_score > best_match_score:
                                    best_match_score = match_score
                                    best_match = (ad_id, detector, good_matches, kp_frame)
                                    
                        except Exception as e:
                            print(f"Error matching features for ad {ad_id}: {e}")
                            continue
                
                # Process the best match
                if best_match and best_match_score > 0.15:
                    ad_id, detector, good_matches, kp_frame = best_match
                    
                    src_pts = np.float32([detector["kp"][m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
                    dst_pts = np.float32([kp_frame[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)
                    
                    try:
                        H, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
                        
                        if H is not None:
                            h, w = detector["shape"]
                            pts = np.float32([[0, 0], [w, 0], [w, h], [0, h]]).reshape(-1, 1, 2)
                            dst = cv2.perspectiveTransform(pts, H)
                            
                            # Calculate bounding box
                            x_coords = [point[0][0] for point in dst]
                            y_coords = [point[0][1] for point in dst]
                            
                            x_min, x_max = min(x_coords), max(x_coords)
                            y_min, y_max = min(y_coords), max(y_coords)
                            
                            # Normalize coordinates to percentage of frame size
                            frame_height, frame_width = frame.shape[:2]
                            
                            # Update detection state
                            current_state["active_ad"] = ad_id
                            current_state["active_since"] = time.time()
                            current_state["last_position"] = {
                                "x": float((x_min / frame_width) * 100),
                                "y": float((y_min / frame_height) * 100),
                                "width": float(((x_max - x_min) / frame_width) * 100),
                                "height": float(((y_max - y_min) / frame_height) * 100),
                            }
                            
                            detected_ads.append({
                                "id": ad_id,
                                "x": float((x_min / frame_width) * 100),
                                "y": float((y_min / frame_height) * 100),
                                "width": float(((x_max - x_min) / frame_width) * 100),
                                "height": float(((y_max - y_min) / frame_height) * 100),
                                "videoUrl": detector["video_url"],
                                "name": detector["name"],
                                "score": float(best_match_score),
                                "status": "new"  # Indicate this is a new detection
                            })
                    except Exception as e:
                        print(f"Error calculating homography: {e}")
            
            # If no ads detected but we have an active ad, continue tracking it
            elif current_state["active_ad"] and current_state["last_position"]:
                ad_id = current_state["active_ad"]
                detector = orb_detectors.get(ad_id)
                
                if detector:
                    detected_ads.append({
                        "id": ad_id,
                        **current_state["last_position"],
                        "videoUrl": detector["video_url"],
                        "name": detector["name"],
                        "status": "tracking"  # Indicate this is continued tracking
                    })
            
            # Send detected ads back to client
            await websocket.send_text(json.dumps(detected_ads))
            
    except WebSocketDisconnect:
        if connection_id in detection_states:
            del detection_states[connection_id]
        active_connections.remove(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        if connection_id in detection_states:
            del detection_states[connection_id]
        active_connections.remove(websocket)

@app.get("/")
def root():
    return {"message": "Add-to-Video backend running"}