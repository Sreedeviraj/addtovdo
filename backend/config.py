

import motor.motor_asyncio

# MongoDB Atlas connection
MONGO_DETAILS = "mongodb+srv://sreedeviraj:sree123@cluster0.oic5wy1.mongodb.net/parkease?retryWrites=true&w=majority&appName=Cluster0"

client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_DETAILS)
db = client["add2video"]   # expose db
ads_collection = db["ads"] 
