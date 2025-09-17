from fastapi import FastAPI, Depends, HTTPException, Body
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pydantic import EmailStr
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Date, Text, DateTime, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session,relationship
from passlib.context import CryptContext
import jwt
import datetime
from sqlalchemy import JSON
from geoalchemy2 import Geometry
from geoalchemy2.shape import from_shape
from shapely.geometry import shape



# Database setup
DATABASE_URL = "postgresql://postgres:12345@localhost/SatelliteDB"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT secret
SECRET_KEY = "supersecretkey"
ALGORITHM = "HS256"


# Models
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)

class AOI(Base):
    __tablename__ = "aois"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=True)  # optional label
    geojson = Column(JSON, nullable=False)  # optional: keep GeoJSON
    geom = Column(Geometry("POLYGON", srid=4326), nullable=True)  # PostGIS geometry 

class Image(Base):
    __tablename__ = "images"
    id = Column(Integer, primary_key=True, index=True)
    aoiId = Column(Integer)
    image_date = Column(Date)
    ndwi_data = Column(LargeBinary, nullable=True)  # Changed to LargeBinary for bytea
    rgb_data = Column(LargeBinary, nullable=True)  # Changed to LargeBinary for bytea
    meta_data = Column(LargeBinary, nullable=True)  # Changed to LargeBinary for bytea
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    
class ChangeMap(Base):
    __tablename__ = "change_maps"

    id = Column(Integer, primary_key=True, index=True)
    aoi_id = Column(Integer, ForeignKey("aois.id", ondelete="CASCADE"), nullable=False)
    pre_image_id = Column(Integer, ForeignKey("images.id", ondelete="CASCADE"), nullable=True)
    post_image_id = Column(Integer, ForeignKey("images.id", ondelete="CASCADE"), nullable=True)
    map_data = Column(LargeBinary, nullable=True)
    from_date = Column(Date, nullable=False)
    to_date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # relationships if needed
    aoi = relationship("AOI")
    pre_image = relationship("Image", foreign_keys=[pre_image_id])
    post_image = relationship("Image", foreign_keys=[post_image_id])
    

# Pydantic schema
class LoginRequest(BaseModel):
    username: str
    password: str
    
class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    
class ChangeMapCreate(BaseModel):
    aoi_id: int
    from_date: str
    to_date: str
    



app = FastAPI()

#Allow frontend to talk to backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        

      
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

    return {"message": "Change map selection saved", "change_map_id": new_map.id}


@app.get("/aois")
def get_user_aois(db: Session = Depends(get_db), current_user: "User" = Depends(get_current_user)):
    """
    Return AOIs belonging to the logged-in user with readable labels.
    """
    aois = db.query(AOI).filter(AOI.user_id == current_user.id).all()
    result = []

    for aoi in aois:
        if aoi.name:
            label = aoi.name
        elif aoi.geojson:
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
                label = f"AOI #{aoi.id} (Lat {latCentroid:.3f}, Lon {lonCentroid:.3f})"               
            else:
                label = f"AOI #{aoi.id}"
                
                
        else:
            label = f"AOI #{aoi.id}"
            

        result.append({
            "id": aoi.id,
            "label": label
        })

    return result


