"""
تنظیمات مرکزی برنامه.

چرا این فایل جدا نگه داشته می‌شه:
وقتی قالب اکسل یا نام شیت‌ها تغییر کنه، فقط همینجا رو ویرایش می‌کنیم،
نه در چند فایل پراکنده.
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "برنامه زمان‌بندی دروس"

    # نام شیت‌های قالب اکسل ورودی — دقیقا مطابق فایلی که کاربر آپلود می‌کند
    sheet_professors: str = "اساتید"
    sheet_prerequisites: str = "پیش‌نیاز دروس"
    sheet_courses: str = "دروس"
    sheet_classrooms: str = "کلاس‌ها"
    sheet_timeslots: str = "بازه‌های زمانی"
    # این شیت اسمش «ارجحیت اساتید» مانده (چون نام واقعیِ شیت در تمپلیت
    # اکسل همین است)، اما از نظر مفهومی دیگر «ارجحیت» نیست: بازه‌هایی
    # که این‌جا برای هر استاد ثبت می‌شود یعنی «فقط در همین بازه‌ها در
    # دسترس است» — یک محدودیت سخت در solver (نگاه کنید به
    # app/solvers/cp_sat_solver.py).
    sheet_preferences: str = "ارجحیت اساتید"
    sheet_offerings: str = "ارائه دروس"
    sheet_student_groups: str = "گروه‌های دانشجویی"
    sheet_majors: str = "رشته‌ها"
    sheet_group_course_map: str = "نگاشت گروه به درس"

    # حداکثر حجم فایل آپلودی (بایت) — جلوگیری از آپلود فایل‌های خیلی بزرگ
    max_upload_size: int = 10 * 1024 * 1024  # 10MB

    # --- احراز هویت ---
    # در استقرار واقعی، این مقدار باید از طریق متغیر محیطی JWT_SECRET_KEY
    # ست شود (در Render به صورت خودکار یک مقدار تصادفی تولید می‌شود —
    # نگاه کنید به render.yaml).
    jwt_secret_key: str = "CHANGE-ME-in-.env-before-deploying"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # یک هفته

    database_url: str = "sqlite:///./scheduler.db"

    # دامنه‌(های) فرانت‌اند که اجازه‌ی دسترسی CORS دارند؛ با کاما جدا شوند.
    # در توسعه‌ی محلی، ویت روی 5173 اجرا می‌شود. در استقرار، این مقدار باید
    # از طریق متغیر محیطی CORS_ORIGINS به آدرس واقعی فرانت‌اند تغییر کند.
    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    class Config:
        env_file = ".env"


settings = Settings()
