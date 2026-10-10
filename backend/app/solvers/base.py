"""
رابط پایه‌ی Solver.

هدف: هر پیاده‌سازیِ حل مدل (چه نسخه‌ی فعلیِ آزمایشی، چه کد نهاییِ همکار)
باید از همین کلاس ارث‌بری کند و متد solve() را با همین امضا پیاده‌سازی کند.
بقیه‌ی برنامه (API، فرانت‌اند) فقط با این رابط کار می‌کند و از جزئیات
داخلیِ مدل (CBC، PuLP، محدودیت‌ها) کاملا بی‌خبر است.

نتیجه: وقتی کد واقعی مدل جایگزین شود، هیچ فایل دیگری در بک‌اند
نیاز به تغییر ندارد — فقط یک کلاس تازه اینجا اضافه و در core/config
یا app/api انتخاب می‌شود.
"""
from abc import ABC, abstractmethod

from app.models.schemas import ParsedScheduleData, SolveResult


class BaseSolver(ABC):
    @abstractmethod
    def solve(self, data: ParsedScheduleData) -> SolveResult:
        """
        دیتای پارس‌شده و اعتبارسنجی‌شده را می‌گیرد و نتیجه‌ی نهاییِ
        خوانا برای انسان را برمی‌گرداند. این متد هرگز نباید کد خام
        (course_code، professor_code، ...) را در خروجی برگرداند —
        تبدیل به نام خوانا وظیفه‌ی همین متد یا لایه‌ی صدازننده است.
        """
        raise NotImplementedError
