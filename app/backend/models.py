from database import Base
import datetime
from sqlalchemy import JSON
from geoalchemy2 import Geometry
from geoalchemy2.shape import from_shape
from sqlalchemy.orm import sessionmaker, Session,relationship
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Date, Text, DateTime, LargeBinary
from sqlalchemy.dialects.postgresql import JSONB

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
    aoi_id = Column(Integer)
    image_date = Column(Date)
    ndwi_data = Column(LargeBinary, nullable=True)  # Changed to LargeBinary for bytea
    rgb_data = Column(LargeBinary, nullable=True)  # Changed to LargeBinary for bytea
    meta_data = Column(JSONB, nullable=True)  # Changed to LargeBinary for bytea
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
    collage_image = Column(LargeBinary, nullable=True)
    water_analysis_image = Column(LargeBinary, nullable=True)

    # relationships if needed
    # aoi = relationship("AOI")
    # pre_image = relationship("Image", foreign_keys=[pre_image_id])
    # post_image = relationship("Image", foreign_keys=[post_image_id])
    
    
class SavedImage(Base):
    __tablename__ = "saved_images"
    
    id = Column(Integer, primary_key=True, index=True)
    image = Column(String, nullable=False)  # You can store the image in binary here
    date = Column(Date, nullable=False)
