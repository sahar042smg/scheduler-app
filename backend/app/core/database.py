"""
تنظیمات دیتابیس، از طریق SQLAlchemy.

در توسعه‌ی محلی از SQLite (یک فایل ساده) استفاده می‌شود. در استقرار
روی Render (پلن رایگان)، دیسک سرویس دائمی نیست، پس به‌جایش به یک
دیتابیس Postgres خارجی (مثلا Neon، رایگان و دائمی) وصل می‌شویم —
فقط با تغییر متغیر محیطی DATABASE_URL، بدون تغییر کد.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

_db_url = settings.sqlalchemy_database_url

engine = create_engine(
    _db_url,
    connect_args={"check_same_thread": False} if _db_url.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency برای تزریق session دیتابیس در مسیرهای API."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
