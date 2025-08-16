from pydantic import BaseModel, EmailStr
from datetime import datetime

class UserRegisterRequest(BaseModel):
    username: str
    password: str
    email: EmailStr

class UserLoginRequest(BaseModel):
    username: str
    password: str

class UserProfileResponse(BaseModel):
    user_id: int
    username: str
    email: EmailStr
    created_at: datetime



class UserLogoutResponse(BaseModel):
    message: str
