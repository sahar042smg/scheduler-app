"""
سرویس خواندن فایل اکسل.

مسئولیت این فایل فقط یک چیز است: تبدیل فایل اکسلِ آپلودشده (با قالب
ثابت) به شیء استاندارد ParsedScheduleData. اگر داده‌ی ورودی ناقص یا
نامعتبر باشد، به‌جای حدس‌زدن، خطای واضح برمی‌گردانیم — طبق تصمیمی که
قبلا گرفته شد (مثلا نبودِ ارجحیت یک استاد باید خطا بدهد، نه اینکه
فرض شود آن استاد هیچ محدودیتی ندارد).
"""
from __future__ import annotations

import pandas as pd

from app.core.config import settings
from app.models.schemas import (
    Classroom,
    Course,
    CourseOffering,
    GroupCourseLikelihood,
    ParsedScheduleData,
    Professor,
    ProfessorPreference,
    StudentGroup,
    TimeSlot,
    UploadResult,
    UploadWarning,
)

MISSING_PREFERENCE_WARNING_CODE = "professors_missing_preference"


class ExcelValidationError(Exception):
    """خطای مربوط به ناقص یا نامعتبر بودن داده‌ی ورودی — پیام آن مستقیما به کاربر نمایش داده می‌شود."""


def _read_sheet(sheets: dict[str, pd.DataFrame], sheet_name: str) -> pd.DataFrame:
    if sheet_name not in sheets:
        raise ExcelValidationError(f'شیت «{sheet_name}» در فایل آپلودشده یافت نشد.')
    return sheets[sheet_name]


def parse_excel(file_bytes: bytes) -> UploadResult:
    parsed, warnings = _parse_excel_internal(file_bytes)
    return UploadResult(data=parsed, warnings=warnings)


def _parse_excel_internal(file_bytes: bytes) -> tuple[ParsedScheduleData, list[UploadWarning]]:
    try:
        sheets = pd.read_excel(pd.io.common.BytesIO(file_bytes), sheet_name=None)
    except Exception as exc:  # noqa: BLE001 — هر خطای خواندن فایل باید پیام روشن بدهد
        raise ExcelValidationError(f"فایل اکسل قابل خواندن نیست: {exc}") from exc

    professors_df = _read_sheet(sheets, settings.sheet_professors)
    classrooms_df = _read_sheet(sheets, settings.sheet_classrooms)
    timeslots_df = _read_sheet(sheets, settings.sheet_timeslots)
    courses_df = _read_sheet(sheets, settings.sheet_courses)
    offerings_df = _read_sheet(sheets, settings.sheet_offerings)
    preferences_df = _read_sheet(sheets, settings.sheet_preferences)
    groups_df = _read_sheet(sheets, settings.sheet_student_groups)
    likelihood_df = _read_sheet(sheets, settings.sheet_group_course_map)

    professors = [
        Professor(code=str(row["کد استاد"]), last_name=str(row["نام خانوادگی"]))
        for _, row in professors_df.iterrows()
    ]

    classrooms = [
        Classroom(
            code=str(row["کد کلاس"]),
            name=str(row["نام کلاس"]),
            capacity=int(row["ظرفیت"]) if "ظرفیت" in row and not pd.isna(row["ظرفیت"]) else None,
        )
        for _, row in classrooms_df.iterrows()
    ]

    timeslots = [
        TimeSlot(
            code=str(row["کد بازه"]),
            day=str(row["روز"]),
            start_time=str(row["ساعت شروع"]),
            end_time=str(row["ساعت پایان"]),
            is_morning=bool(row.get("صبح", False)),
        )
        for _, row in timeslots_df.iterrows()
    ]

    courses = [
        Course(
            code=str(row["کد درس"]),
            name=str(row["نام درس"]),
            category=str(row["دسته‌بندی"]) if "دسته‌بندی" in row and not pd.isna(row["دسته‌بندی"]) else None,
        )
        for _, row in courses_df.iterrows()
    ]

    offerings = [
        CourseOffering(
            offering_id=str(row["کد ارائه"]),
            course_code=str(row["کد درس"]),
            professor_code=str(row["کد استاد"]),
            sessions_per_week=int(row["تعداد جلسات در هفته"]),
            group_count=int(row["تعداد گروه درسی"]),
        )
        for _, row in offerings_df.iterrows()
    ]

    preferences = [
        ProfessorPreference(professor_code=str(row["کد استاد"]), timeslot_code=str(row["کد بازه"]))
        for _, row in preferences_df.iterrows()
    ]

    student_groups = [
        StudentGroup(group_code=str(row["کد گروه"]), major_code=str(row["کد رشته"]))
        for _, row in groups_df.iterrows()
    ]

    group_course_likelihood = [
        GroupCourseLikelihood(
            group_code=str(row["کد گروه"]),
            course_code=str(row["کد درس"]),
            likelihood=str(row["احتمال اخذ"]),
        )
        for _, row in likelihood_df.iterrows()
    ]

    # قانونی که قبلا مشخص شد، با این تفاوت که دیگر جلوی کار را نمی‌گیرد:
    # اگر استادی هیچ ردیفی در شیت «بازه‌های در دسترس» نداشته باشد، به‌جای
    # توقف کامل، هشدار برمی‌گردانیم تا کاربر خودش تصمیم بگیرد ادامه بدهد یا نه.
    # توجه: این داده دیگر «ارجحیت» نیست، بلکه معنیِ در دسترس‌بودن
    # (availability) دارد و در solver به‌صورت محدودیت سخت اعمال می‌شود —
    # یعنی جلسات آن استاد فقط در همین بازه‌ها می‌توانند باشند. اگر کاربر
    # تایید کند که ادامه بدهد، آن استاد به‌عنوان «بدون هیچ محدودیتِ
    # زمانی» در نظر گرفته می‌شود (کد او را در
    # professors_without_preference_constraint می‌گذاریم تا solver
    # بداند اجازه دارد او را در هر بازه‌ای قرار دهد).
    warnings: list[UploadWarning] = []
    professor_codes_with_preferences = {p.professor_code for p in preferences}
    professors_missing_preferences = [
        p for p in professors if p.code not in professor_codes_with_preferences
    ]
    if professors_missing_preferences:
        names = "، ".join(p.last_name for p in professors_missing_preferences)
        warnings.append(
            UploadWarning(
                code=MISSING_PREFERENCE_WARNING_CODE,
                message=(
                    f"بازه‌های زمانیِ در دسترس برای این استادان ثبت نشده: {names}. "
                    "اگر ادامه دهید، این استادان بدون هیچ محدودیت زمانی در نظر گرفته "
                    "می‌شوند و ممکن است در هر بازه‌ای قرار بگیرند."
                ),
                professor_codes=[p.code for p in professors_missing_preferences],
            )
        )

    parsed = ParsedScheduleData(
        professors=professors,
        classrooms=classrooms,
        timeslots=timeslots,
        courses=courses,
        offerings=offerings,
        preferences=preferences,
        student_groups=student_groups,
        group_course_likelihood=group_course_likelihood,
    )
    return parsed, warnings
