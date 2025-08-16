

from fastapi import APIRouter, Depends, HTTPException
from app.schemas import user as user_schema
from app.database.database import get_db
from app.models.user import User
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from passlib.context import CryptContext

# Khởi tạo router cho nhóm API user, prefix là /user, gắn tag "User" để phân loại trên docs
router = APIRouter(prefix="/user", tags=["User"])

# Khởi tạo context cho hash password
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Hàm hash password
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# Hàm verify password
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)



# API đăng ký tài khoản mới
@router.post("/register", response_model=user_schema.UserProfileResponse)
def register_user(request: user_schema.UserRegisterRequest, db: Session = Depends(get_db)):
    """
    Đăng ký tài khoản mới, kiểm tra trùng lặp username/email, lưu user vào DB.
    """
    # Kiểm tra username/email đã tồn tại chưa
    existing_user = db.query(User).filter((User.username == request.username) | (User.email == request.email)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username or email already exists")
    hashed_password = get_password_hash(request.password)
    user = User(
        username=request.username,
        password_hash=hashed_password,
        email=request.email,
        created_at=datetime.utcnow()
    )
    db.add(user)
    try:
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Username or email already exists")
    return user_schema.UserProfileResponse(
        user_id=user.user_id,
        username=user.username,
        email=user.email,
        created_at=user.created_at
    )

# API đăng nhập
@router.post("/login", response_model=user_schema.UserProfileResponse)
def login_user(request: user_schema.UserLoginRequest, db: Session = Depends(get_db)):
    """
    Đăng nhập: xác thực username và password, trả về thông tin user nếu thành công.
    """
    user = db.query(User).filter(User.username == request.username).first()
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return user_schema.UserProfileResponse(
        user_id=user.user_id,
        username=user.username,
        email=user.email,
        created_at=user.created_at
    )



# API lấy thông tin profile của user theo user_id
@router.get("/profile", response_model=user_schema.UserProfileResponse)
def get_profile(user_id: int, db: Session = Depends(get_db)):
    """
    Lấy thông tin profile của user theo user_id.
    """
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user_schema.UserProfileResponse(
        user_id=user.user_id,
        username=user.username,
        email=user.email,
        created_at=user.created_at
    )

# API đăng xuất (chỉ trả về message, không xử lý logic thực tế)
@router.post("/logout", response_model=user_schema.UserLogoutResponse)
def logout_user():
    """
    Đăng xuất: chỉ trả về message, không xử lý logic thực tế.
    """
    return user_schema.UserLogoutResponse(message="Logged out")
