"""
اسکیمای استاندارد داده.

این فایل «قرارداد» بین دو بخش مستقل برنامه است:
  ۱) خواندن و اعتبارسنجی اکسل  (app/services/excel_reader.py)
  ۲) اجرای مدل بهینه‌سازی      (app/solvers/*)

هر کدام از این دو بخش، مستقل از دیگری قابل تغییر است — به شرطی که
همچنان همین کلاس‌ها را ورودی/خروجی بدهند. وقتی کد واقعی مدل رسید،
فقط کافی است یک کلاس تازه از Solver (در پوشه‌ی solvers) بسازیم؛
هیچ‌جای دیگر برنامه نیاز به تغییر ندارد.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class Professor(BaseModel):
    code: str
    last_name: str


class Classroom(BaseModel):
    code: str
    name: str
    capacity: int | None = None


class TimeSlot(BaseModel):
    code: str
    day: str
    start_time: str
    end_time: str
    is_morning: bool = False


class Course(BaseModel):
    code: str
    name: str
    category: str | None = None  # عمومی / تخصصی / ...


class CourseOffering(BaseModel):
    """یک ارائه‌ی مشخص از یک درس در ترم جاری."""
    offering_id: str
    course_code: str
    professor_code: str
    sessions_per_week: int
    group_count: int


class ProfessorPreference(BaseModel):
    professor_code: str
    timeslot_code: str


class StudentGroup(BaseModel):
    group_code: str
    major_code: str


class GroupCourseLikelihood(BaseModel):
    group_code: str
    course_code: str
    likelihood: str  # زیاد / متوسط / کم


class ParsedScheduleData(BaseModel):
    """
    خروجیِ استاندارد لایه‌ی خواندن اکسل، و ورودیِ استاندارد لایه‌ی حل مدل.
    هر Solver ای که ساخته شود، دقیقا همین شیء را دریافت می‌کند.
    """
    professors: list[Professor]
    classrooms: list[Classroom]
    timeslots: list[TimeSlot]
    courses: list[Course]
    offerings: list[CourseOffering]
    preferences: list[ProfessorPreference]
    student_groups: list[StudentGroup]
    group_course_likelihood: list[GroupCourseLikelihood]
    # کد استادهایی که در نهایت (بعد از تایید احتمالی کاربر) به‌عنوان
    # «بدون هیچ محدودیت زمانی» در نظر گرفته می‌شوند — یعنی solver باید
    # اجازه‌ی قرارگیری آن‌ها را در هر بازه‌ی زمانی بدهد. این لیست خالی
    # یعنی همه‌ی استادها ارجحیت مشخص دارند.
    professors_without_preference_constraint: list[str] = Field(default_factory=list)


class UploadWarning(BaseModel):
    """
    هشداری که مانع ادامه‌ی کار نمی‌شود، اما نیاز به تایید صریح کاربر دارد.
    code به فرانت‌اند اجازه می‌دهد رفتار مناسب (نمایش دیالوگ تایید) را
    بدون پارس‌کردن متن پیام تشخیص دهد.
    """
    code: str
    message: str
    professor_codes: list[str] = Field(default_factory=list)


class UploadResult(BaseModel):
    """پاسخ نهایی مسیر آپلود: داده‌ی پارس‌شده + هر هشداری که نیاز به تایید کاربر دارد."""
    data: ParsedScheduleData
    warnings: list[UploadWarning] = Field(default_factory=list)


class ScheduleAssignment(BaseModel):
    """یک سطر از نتیجه‌ی نهایی — قابل‌خواندن برای انسان، نه کدهای خام."""
    course_name: str
    professor_last_name: str
    classroom_name: str
    day: str
    start_time: str
    end_time: str


class ScheduleOption(BaseModel):
    """یکی از چند چینشِ ممکن (تا ۳ گزینه) که solver پیدا کرده — هرکدام کاملا مستقل و قابل‌دانلود."""
    label: str
    objective_value: float | None = None
    assignments: list[ScheduleAssignment] = Field(default_factory=list)


class SolveResult(BaseModel):
    status: str  # "optimal" | "feasible" | "infeasible" | "error"
    message: str | None = None
    # تا ۳ گزینه‌ی متفاوت (اگر کمتر شدنی بود، همون تعداد). گزینه‌ی اول
    # همیشه بهترین (کمترین پنالتی) است.
    options: list[ScheduleOption] = Field(default_factory=list)
