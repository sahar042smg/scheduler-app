"""
مسیرهای احراز هویت.

جریان کار:
  POST /api/auth/register  → کاربر ثبت‌نام می‌کند، اما is_active=False می‌ماند
  POST /api/auth/login     → فقط اگر is_active باشد، توکن صادر می‌شود
  GET  /api/auth/me        → اطلاعات کاربر لاگین‌شده (برای چک‌کردن وضعیت در فرانت‌اند)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.models.auth_schemas import (
    LoginRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
    UserOut,
)
from app.models.user import User

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=RegisterResponse)
async def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="این ایمیل قبلا ثبت‌نام کرده است.")

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        is_active=False,
        is_admin=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return RegisterResponse(
        message="ثبت‌نام شما با موفقیت انجام شد. تا زمانی که مدیر سیستم حساب شما را تایید کند، امکان ورود نخواهید داشت.",
        user=user,
    )


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: Session = Depends(get_db)):
    invalid = HTTPException(status_code=401, detail="ایمیل یا رمز عبور اشتباه است.")

    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise invalid

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="حساب شما هنوز توسط مدیر سیستم تایید نشده است.",
        )

    token = create_access_token(subject=user.email)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)):
    return current_user
