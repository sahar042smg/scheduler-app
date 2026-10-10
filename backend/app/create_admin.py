"""
ساخت اولین حساب مدیر.

اجرا: python -m app.create_admin

بدون این اسکریپت، هیچ‌کس نمی‌تواند وارد پنل مدیریت بشود (چون فقط مدیر
می‌تواند کاربر دیگری را فعال کند). این اسکریپت را فقط یک‌بار، موقع
راه‌اندازی اولیه‌ی برنامه اجرا کنید.
"""
import getpass

from app.core.database import Base, SessionLocal, engine
from app.core.security import hash_password
from app.models.user import User


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    print("=== ساخت حساب مدیر ===")
    email = input("ایمیل مدیر: ").strip()
    password = getpass.getpass("رمز عبور (حداقل ۸ کاراکتر): ")

    existing = db.query(User).filter(User.email == email).first()
    if existing:
        existing.is_admin = True
        existing.is_active = True
        existing.hashed_password = hash_password(password)
        db.commit()
        print(f"کاربر موجود «{email}» به مدیر ارتقا یافت.")
        return

    admin = User(
        email=email,
        hashed_password=hash_password(password),
        full_name="مدیر سیستم",
        is_active=True,
        is_admin=True,
    )
    db.add(admin)
    db.commit()
    print(f"حساب مدیر «{email}» با موفقیت ساخته شد.")


if __name__ == "__main__":
    main()
