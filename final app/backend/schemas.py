from pydantic import BaseModel
from pydantic import EmailStr

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