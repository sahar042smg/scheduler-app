"""
Dependencyهای احراز هویت.

get_current_user: توکن را می‌خواند، کاربر را از دیتابیس پیدا می‌کند.
get_current_active_user: علاوه بر بالا، چک می‌کند is_active باشد —
    این همان dependency ای است که مسیرهای اصلی برنامه (آپلود، حل مدل)
    باید ازش استفاده کنند تا کاربرهای تاییدنشده نتوانند از امکانات
    استفاده کنند.
get_current_admin_user: علاوه بر active بودن، چک می‌کند is_admin باشد —
    برای مسیرهای مدیریتی (فعال/غیرفعال کردن کاربران).
"""
from fastapi import Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User

# tokenUrl فقط برای مستندات Swagger استفاده می‌شود؛ خود لاگین در auth.py است.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def get_current_user(
    header_token: str | None = Depends(oauth2_scheme),
    query_token: str | None = Query(default=None, alias="token"),
    db: Session = Depends(get_db),
) -> User:
    """
    توکن معمولا از هدر Authorization خوانده می‌شود. برای مسیر دانلود که
    از طریق تگ <a href> باز می‌شود (و نمی‌توان هدر روی آن گذاشت)، توکن
    از query param به نام token هم پذیرفته می‌شود.
    """
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="ورود نامعتبر است. لطفا دوباره وارد شوید.",
    )
    token = header_token or query_token
    if not token:
        raise unauthorized

    email = decode_access_token(token)
    if email is None:
        raise unauthorized

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise unauthorized

    return user


def get_current_active_user(user: User = Depends(get_current_user)) -> User:
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="حساب شما هنوز توسط مدیر سیستم تایید نشده است.",
        )
    return user


def get_current_admin_user(user: User = Depends(get_current_active_user)) -> User:
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="این بخش فقط برای مدیر سیستم در دسترس است.",
        )
    return user
