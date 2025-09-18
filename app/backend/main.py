from fastapi import FastAPI, Depends, HTTPException, Body
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from passlib.context import CryptContext
import jwt
import datetime
from shapely.geometry import shape
from downloader.image_downloader import download_change_map_images, load_config
from database import get_db
from models import User, AOI, ChangeMap
from schemas import LoginRequest, RegisterRequest, ChangeMapCreate
from geoalchemy2.shape import from_shape
import asyncio
from water_analysis import run_water_analysis
from fastapi.responses import StreamingResponse
from io import BytesIO




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

@app.get("/activity")
def get_activity():
    return {"logs": ["Log 1", "Log 2", "Log 3"]}

@app.get("/notifications")
def get_notifications():
    return {"messages": ["Message 1", "Message 2"]}


@app.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == data.username).first()
    if not user or not pwd_context.verify(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    # Generate JWT token
    token_data = {
        "sub": user.username,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=2)
    }
    token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)

    return {"token": token}


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        user = db.query(User).filter(User.username == username).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


@app.post("/register")
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    # Check if username/email already exists
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email already exists")

    # Hash password
    hashed_password = pwd_context.hash(data.password)

    # Create user
    new_user = User(
        username=data.username,
        email=data.email,
        password_hash=hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User registered successfully", "user_id": new_user.id}

@app.post("/aoi")
def save_aoi(aoi: dict = Body(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        # Extract geometry from Feature or FeatureCollection
        if aoi.get("type") == "FeatureCollection":
            geom = aoi["features"][0]["geometry"]
        elif aoi.get("type") == "Feature":
            geom = aoi["geometry"]
        else:
            geom = aoi

        # Validate with shapely
        geom_shape = shape(geom)

        # Save both GeoJSON + PostGIS geometry
        new_aoi = AOI(
            user_id=current_user.id,
            name=aoi.get("properties", {}).get("shape", "AOI"),  # optional label
            geojson=aoi,  # keep full feature JSON
            geom=from_shape(geom_shape, srid=4326)  # proper PostGIS geometry
        )

        db.add(new_aoi)
        db.commit()
        db.refresh(new_aoi)

        return {"message": "AOI saved successfully", "aoi_id": new_aoi.id}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    
    
@app.post("/change_maps")
def save_change_map_selection(data: ChangeMapCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Validate AOI exists
    aoi = db.query(AOI).filter(AOI.id == data.aoi_id, AOI.user_id == current_user.id).first()
    if not aoi:
        raise HTTPException(status_code=404, detail="AOI not found")

    # Create change map record with images and map_path NULL
    new_map = ChangeMap(
        aoi_id=data.aoi_id,
        pre_image_id=None,
        post_image_id=None,
        map_data=b'\x01\x02\x03\x04\x05',
        from_date=datetime.datetime.strptime(data.from_date, "%Y-%m-%d").date(),
        to_date=datetime.datetime.strptime(data.to_date, "%Y-%m-%d").date(),
        created_at=datetime.datetime.utcnow()
    )
    db.add(new_map)
    db.commit()
    db.refresh(new_map)
    
    download_change_map_images(new_map.id)
    run_water_analysis(new_map.id)

    return {"message": "Change map selection saved", "change_map_id": new_map.id}


@app.get("/aois")
def get_user_aois(db: Session = Depends(get_db), current_user: "User" = Depends(get_current_user)):
    """
    Return AOIs belonging to the logged-in user with readable labels.
    """
    aois = db.query(AOI).filter(AOI.user_id == current_user.id).all()
    result = []

    for aoi in aois:
        # if aoi.name:
        #     label = aoi.name
        # el
        if aoi.geojson:
            geom = aoi.geojson.get("geometry") or (
                aoi.geojson.get("features")[0].get("geometry")
                if "features" in aoi.geojson else None
            )
            if geom and "coordinates" in geom:
                # Get first ring for polygon
                coords = geom["coordinates"][0]
                lats = [c[1] for c in coords]
                lons = [c[0] for c in coords]
                latCentroid = (min(lats) + max(lats)) / 2
                lonCentroid = (min(lons) + max(lons)) / 2
                label = f"AOI:{aoi.name} (Lat {latCentroid:.3f}, Lon {lonCentroid:.3f})"               
            else:
                label = f"AOI {aoi.name}"
                
                
        else:
            label = f"AOI #{aoi.name}"
            

        result.append({
            "id": aoi.id,
            "label": label
        })

    return result


@app.get("/change_maps/{change_map_id}/water_analysis_image")
def get_water_analysis_image(change_map_id: int, db: Session = Depends(get_db)):
    change_map = db.query(ChangeMap).filter(ChangeMap.id == change_map_id).first()
    if not change_map or not change_map.water_analysis_image:
        raise HTTPException(status_code=404, detail="Water analysis image not found")

    return StreamingResponse(
        BytesIO(change_map.water_analysis_image),
        media_type="image/tiff"
    )

@app.get("/change_maps/{change_map_id}/collage_image")
def get_collage_image(change_map_id: int, db: Session = Depends(get_db)):
    change_map = db.query(ChangeMap).filter(ChangeMap.id == change_map_id).first()
    if not change_map or not change_map.collage_image:
        raise HTTPException(status_code=404, detail="Collage image not found")

    return StreamingResponse(
        BytesIO(change_map.collage_image),
        media_type="image/tiff"
    )


@app.get("/dashboard")
def get_dashboard(db: Session = Depends(get_db)):
    total_aois = db.query(AOI).count()
    total_change_maps = db.query(ChangeMap).count()
    last_analysis = db.query(ChangeMap.created_at).order_by(ChangeMap.created_at.desc()).first()
    # pending_tasks = db.query(ChangeMap).filter(ChangeMap.status == "pending").count()
    

    return {
        "total_aois": total_aois,
        "total_change_maps": total_change_maps,
        "last_analysis_date": last_analysis[0].strftime("%B %d, %Y %I:%M:%S %p") if last_analysis else None,
        # "pending_tasks": pending_tasks,
    }