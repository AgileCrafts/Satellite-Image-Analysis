from fastapi import FastAPI, Depends, HTTPException, Body
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from passlib.context import CryptContext
import jwt
import datetime
from shapely.geometry import shape
# from downloader.image_downloader import download_change_map_images, load_config
# from downloader.image_downloader2 import another_download_change_map_images
from database import get_db
from schemas import LoginRequest, RegisterRequest, ChangeMapCreate
from geoalchemy2.shape import from_shape
import asyncio
# from water_analysis import run_water_analysis
# from infrastructure_analysis import run_builtup_analysis
from fastapi.responses import StreamingResponse
from io import BytesIO
from inference_sdk import InferenceHTTPClient
import supervision as sv
import requests
from PIL import Image
import cv2
import numpy as np
from matplotlib import pyplot as plt
import json
from models import Port, Image
from schemas import PortSchema
from modified_downloader import download_images
from water_change import analyze_water_change



# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT secret
SECRET_KEY = "supersecretkey"
ALGORITHM = "HS256"




app = FastAPI()

#Allow frontend to talk to backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Builtup-Area-Stats", "X-Water-Area-Stats"],
)

        
# Simulating a long-running task
async def long_running_task():
    try:
        await asyncio.sleep(10)  # Simulate a long-running async task
    except asyncio.CancelledError:
        print("Long-running task was cancelled.")
        raise

@app.on_event("startup")
async def startup():
    print("Starting server...")
    # Start a long-running task in the background
    app.state.task = asyncio.create_task(long_running_task())

@app.on_event("shutdown")
async def shutdown():
    print("Shutting down gracefully...")
    # Cancel the long-running task
    app.state.task.cancel()
    try:
        # Wait for the task to finish or be cancelled
        await app.state.task
    except asyncio.CancelledError:
        print("Task cancelled successfully.")
    
    print("Server shutdown complete.")
      
@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI!"}

@app.get("/ping")
def ping():
    return {"status": "pong"}



# @app.post("/login")
# def login(data: LoginRequest, db: Session = Depends(get_db)):
#     user = db.query(User).filter(User.username == data.username).first()
#     if not user or not pwd_context.verify(data.password, user.password_hash):
#         raise HTTPException(status_code=401, detail="Invalid username or password")

#     # Generate JWT token
#     token_data = {
#         "sub": user.username,
#         "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)
#     }
#     token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)

#     return {"token": token}


# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

# def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         username = payload.get("sub")
#         if username is None:
#             raise HTTPException(status_code=401, detail="Invalid authentication credentials")
#         user = db.query(User).filter(User.username == username).first()
#         if not user:
#             raise HTTPException(status_code=401, detail="User not found")
#         return user
#     except jwt.ExpiredSignatureError:
#         raise HTTPException(status_code=401, detail="Token expired")
#     except jwt.PyJWTError:
#         raise HTTPException(status_code=401, detail="Invalid token")


# @app.post("/register")
# def register(data: RegisterRequest, db: Session = Depends(get_db)):
#     # Check if username/email already exists
#     if db.query(User).filter(User.username == data.username).first():
#         raise HTTPException(status_code=400, detail="Username already exists")
#     if db.query(User).filter(User.email == data.email).first():
#         raise HTTPException(status_code=400, detail="Email already exists")

#     # Hash password
#     hashed_password = pwd_context.hash(data.password)

#     # Create user
#     new_user = User(
#         username=data.username,
#         email=data.email,
#         password_hash=hashed_password
#     )
#     db.add(new_user)
#     db.commit()
#     db.refresh(new_user)

#     return {"message": "User registered successfully", "user_id": new_user.id}





################---------------------------------------------

@app.get("/ports/by-region/{region}")
def get_ports_by_region(region: str, db: Session = Depends(get_db)):
    ports = db.query(Port).filter(Port.region == region).all()
    return [ {"id": p.id, "region": p.region, "port_name": p.port_name, "bbox": p.bbox, "latitude":p.latitude, "longitude":p.longitude, "geojson":p.geojson} for p in ports ]


# ---------------- ANALYZE WATER CHANGE ----------------
@app.get("/analyze-water-change/{port_id}")
def analyze_water_change_for_port(port_id: int, pre_date: str, post_date: str, db: Session = Depends(get_db)):
    """
    Given a port ID, gets its bbox from DB, downloads pre/post images for the specified dates,
    then runs water change analysis and returns results.
    """
    port = db.query(Port).filter(Port.id == port_id).first()
    if not port:
        return {"error": f"Port {port_id} not found"}

    bbox = port.bbox  # expecting [minx, miny, maxx, maxy]
    if not bbox or len(bbox) != 4:
        return {"error": "Invalid bbox in port record"}


    # pre_date="2020-03-01"
    # post_date="2025-03-01"
    

    
    
    
    # # Download images as bytes (pre/post)
    # pre_bytes = download_images(pre_date, bbox, port_id)
    # post_bytes = download_images(post_date, bbox, port_id)

    # if not pre_bytes or not post_bytes:
    #     return {"error": "Failed to download pre/post images"}

    # Run water change analysis
    
     # ---- YOUR REAL LOGIC HERE ----
    pre_path = f"{port_id}_tiff_images/NDWI_5band_{pre_date}.tif"
    post_path = f"{port_id}_tiff_images/NDWI_5band_{post_date}.tif"
    
    print(pre_path)
    print(post_path)
    
    with open(pre_path, "rb") as f:
        pre_bytes = f.read()
    with open(post_path, "rb") as f:
        post_bytes = f.read()

    
    
    result = analyze_water_change(pre_bytes, post_bytes, output_dir="output" )

    # return {
    #     "port_name": port.port_name,
    #     "lost_area_ha": result["lost_area_ha"],
    #     "change_map_png_path": "output/change_map.png",
    #     "lost_water_tif_path": result["lost_water_tif"],
    #     "lost_water_geojson_path": result["lost_water_geojson"]
    # }
    return {
        "lost_water_geojson": result["geojson"],
        "lost_area_ha": result["lost_area_ha"]
    }