from fastapi import FastAPI, Depends, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pydantic import EmailStr
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
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

# Pydantic schema
class LoginRequest(BaseModel):
    username: str
    password: str
    
class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    
class AOI(Base):
    __tablename__ = "aois"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=True)  # optional label
    geojson = Column(JSON, nullable=False)  # optional: keep GeoJSON
    geom = Column(Geometry("POLYGON", srid=4326), nullable=True)  # PostGIS geometry 


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
def save_aoi(aoi: dict = Body(...), db: Session = Depends(get_db)):
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
