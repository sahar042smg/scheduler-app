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
from app.core.database import Base, engine

# ساخت جداول دیتابیس در صورت نبودشان — برای این پروژه، مهاجرت پیچیده
# (Alembic) لازم نیست؛ اگر بعدا مدل کاربر تغییر کرد، باید این خط دستی
# مدیریت مهاجرت شود.
Base.metadata.create_all(bind=engine)

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
