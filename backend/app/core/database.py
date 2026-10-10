"""
تنظیمات دیتابیس (SQLite، از طریق SQLAlchemy).

برای این پروژه یک دیتابیس ساده‌ی فایلی کافی است — نیازی به یک دیتابیس
جداگانه (Postgres و ...) نیست، مگر اینکه تعداد کاربران یا حجم داده در
آینده به‌طور جدی رشد کند.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
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
