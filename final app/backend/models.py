from database import Base
import datetime
from sqlalchemy import JSON
from geoalchemy2 import Geometry
from geoalchemy2.shape import from_shape
from sqlalchemy.orm import sessionmaker, Session,relationship
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Date, Text, DateTime, LargeBinary, Float
from sqlalchemy.dialects.postgresql import JSONB

# Models
# class User(Base):
#     __tablename__ = "users"
#     id = Column(Integer, primary_key=True, index=True)
#     username = Column(String, unique=True, index=True, nullable=False)
#     email = Column(String, unique=True, index=True, nullable=False)
#     password_hash = Column(String, nullable=False)

class Port(Base):
    __tablename__ = "ports"
    
    id = Column(Integer, primary_key=True, index=True)
    region = Column(String(50), nullable=False)
    port_name = Column(String(100), nullable=False)
    bbox = Column(JSON, nullable=True) 
    
    latitude = Column(Float, nullable=True)  # Latitude (in decimal degrees)
    longitude = Column(Float, nullable=True)
    geojson = Column(JSONB, nullable=True) 

class Image(Base):
    __tablename__ = "images"
    id = Column(Integer, primary_key=True, index=True)
    port_id = Column(Integer)
    image_date = Column(Date)
    ndwi_data = Column(LargeBinary, nullable=True)  # Changed to LargeBinary for bytea
    rgb_data = Column(LargeBinary, nullable=True)  # Changed to LargeBinary for bytea
    meta_data = Column(JSONB, nullable=True)  # Changed to LargeBinary for bytea
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    
    
# class SavedImage(Base):
#     __tablename__ = "saved_images"
    
#     id = Column(Integer, primary_key=True, index=True)
#     image = Column(String, nullable=False)  # You can store the image in binary here
#     date = Column(Date, nullable=False)
    
    

