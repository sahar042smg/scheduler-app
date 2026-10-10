"""
مسیرهای مدیریتی — فقط برای کاربر مدیر (is_admin=True) در دسترس است.

از همین‌جا مدیر می‌تواند ببیند چه کسانی ثبت‌نام کرده‌اند و دسترسی
هرکدام را فعال یا غیرفعال کند.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_admin_user
from app.models.auth_schemas import UserOut
from app.models.user import User

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/users", response_model=list[UserOut])
async def list_users(
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin_user),
):
    return db.query(User).order_by(User.created_at.desc()).all()


@router.post("/users/{user_id}/activate", response_model=UserOut)
async def activate_user(
    user_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin_user),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="کاربر یافت نشد.")
    user.is_active = True
    db.commit()
    db.refresh(user)
    return user


@router.post("/users/{user_id}/deactivate", response_model=UserOut)
async def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin_user),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="کاربر یافت نشد.")
    if user.is_admin:
        raise HTTPException(status_code=400, detail="نمی‌توان دسترسی مدیر را غیرفعال کرد.")
    user.is_active = False
    db.commit()
    db.refresh(user)
    return user
