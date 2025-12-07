from pydantic import BaseModel
from pydantic import EmailStr
from typing import List


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
    
class PortSchema(BaseModel):
    id: int
    region: str
    port_name: str
    bbox: List[float]

    class Config:
        orm_mode = True