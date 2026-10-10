"""
نقطه‌ی ورود برنامه.
اجرا با: uvicorn app.main:app --reload
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.admin import router as admin_router
from app.api.auth import router as auth_router
from app.api.schedule import router as schedule_router
from app.core.config import settings
from app.core.database import Base, SessionLocal, engine
from app.core.security import hash_password
from app.models.user import User

# ساخت جداول دیتابیس در صورت نبودشان — برای این پروژه، مهاجرت پیچیده
# (Alembic) لازم نیست؛ اگر بعدا مدل کاربر تغییر کرد، باید این خط دستی
# مدیریت مهاجرت شود.
Base.metadata.create_all(bind=engine)


def _ensure_initial_admin() -> None:
    """
    اگر هیچ مدیری در دیتابیس نباشد و متغیرهای محیطی
    INITIAL_ADMIN_EMAIL / INITIAL_ADMIN_PASSWORD ست شده باشند، یک حساب
    مدیر خودکار می‌سازد. این جایگزین اجرای دستی create_admin از طریق
    Shell است — چون پلن رایگان Render دسترسی Shell نمی‌دهد.
    """
    if not settings.initial_admin_email or not settings.initial_admin_password:
        return
    db = SessionLocal()
    try:
        if db.query(User).filter(User.is_admin.is_(True)).first():
            return  # قبلا یک مدیر ساخته شده؛ کاری لازم نیست
        existing = db.query(User).filter(User.email == settings.initial_admin_email).first()
        if existing:
            existing.is_admin = True
            existing.is_active = True
            existing.hashed_password = hash_password(settings.initial_admin_password)
        else:
            db.add(
                User(
                    email=settings.initial_admin_email,
                    hashed_password=hash_password(settings.initial_admin_password),
                    full_name="مدیر سیستم",
                    is_active=True,
                    is_admin=True,
                )
            )
        db.commit()
    finally:
        db.close()


_ensure_initial_admin()

app = FastAPI(title=settings.app_name)

# لیست دامنه‌های مجاز از متغیر محیطی CORS_ORIGINS خوانده می‌شود
# (پیش‌فرض برای توسعه‌ی محلی: پورت ویت). در Render این مقدار به‌طور
# خودکار به آدرس واقعی فرانت‌اند تنظیم می‌شود — نگاه کنید به render.yaml.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(schedule_router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
