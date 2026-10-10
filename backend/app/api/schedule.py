"""
مسیرهای API مربوط به زمان‌بندی.

جریان کار:
  POST /api/schedule/upload   → فایل اکسل را می‌گیرد، اعتبارسنجی و پارس می‌کند
  POST /api/schedule/solve    → دیتای پارس‌شده را حل می‌کند؛ تا ۳ گزینه‌ی متفاوت برمی‌گرداند
  GET  /api/schedule/download → یکی از گزینه‌های آخرین حل (با ?option=N) را به‌صورت اکسل دانلود می‌دهد

این دو مرحله (آپلود/پارس، و حل) عمدا از هم جدا هستند: اگر داده نامعتبر
باشد، کاربر همان لحظه‌ی آپلود متوجه می‌شود، بدون اینکه منتظر اجرای مدل
(که ممکن است طول بکشد) بماند.
"""
from __future__ import annotations

import io

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse

from app.core.config import settings
from app.core.dependencies import get_current_active_user
from app.models.schemas import ParsedScheduleData, SolveResult, UploadResult
from app.services.excel_reader import ExcelValidationError, parse_excel
from app.solvers.cp_sat_solver import CpSatSolver

router = APIRouter(
    prefix="/api/schedule",
    tags=["schedule"],
    dependencies=[Depends(get_current_active_user)],  # همه‌ی مسیرهای این router نیاز به ورود دارند
)

# نگهداریِ ساده‌ی آخرین نتیجه در حافظه، فقط برای اینکه دانلود جدا از حل باشد.
# در نسخه‌ی نهایی (چند کاربره) این باید به یک session/DB واقعی منتقل شود.
_last_result: SolveResult | None = None


def get_solver():
    """
    نقطه‌ی تعویضِ solver.
    فعلا از یک مدل واقعیِ CP-SAT (app/solvers/cp_sat_solver.py) استفاده
    می‌شود که خودمان بر اساس محدودیت‌های مستندشده‌ی مدل اصلی نوشته‌ایم
    (چون کد اصلی از همکار دریافت نشد). اگر بعدا کد یا جزئیات دقیق‌تری
    از مدل واقعی رسید، فقط کافی‌ست همین خط عوض شود؛ هیچ‌جای دیگر برنامه
    نیازی به تغییر ندارد.
    """
    return CpSatSolver()


@router.post("/upload", response_model=UploadResult)
async def upload_excel(file: UploadFile):
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="فقط فایل اکسل (.xlsx) پذیرفته می‌شود.")

    contents = await file.read()
    if len(contents) > settings.max_upload_size:
        raise HTTPException(status_code=400, detail="حجم فایل بیش از حد مجاز است.")

    try:
        upload_result = parse_excel(contents)
    except ExcelValidationError as exc:
        # این‌ها خطاهای ساختاری‌اند (شیت گم‌شده، فایل غیرقابل‌خواندن) —
        # برخلاف «ارجحیت ثبت‌نشده»، قابل نادیده‌گرفتن توسط کاربر نیستند.
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return upload_result


@router.post("/solve", response_model=SolveResult)
async def solve_schedule(data: ParsedScheduleData):
    global _last_result
    solver = get_solver()
    result = solver.solve(data)
    _last_result = result

    if result.status in ("error", "infeasible"):
        raise HTTPException(status_code=422, detail=result.message)

    return result


@router.get("/download")
async def download_results(option: int = Query(default=0, ge=0, description="ایندکسِ گزینه (۰ = گزینه‌ی اول)")):
    if _last_result is None or not _last_result.options:
        raise HTTPException(status_code=404, detail="هنوز نتیجه‌ای برای دانلود وجود ندارد.")
    if option >= len(_last_result.options):
        raise HTTPException(status_code=404, detail="این گزینه وجود ندارد.")

    chosen = _last_result.options[option]
    df = pd.DataFrame([a.model_dump() for a in chosen.assignments])
    df = df.rename(
        columns={
            "course_name": "نام درس",
            "professor_last_name": "استاد",
            "classroom_name": "کلاس",
            "day": "روز",
            "start_time": "ساعت شروع",
            "end_time": "ساعت پایان",
        }
    )

    buffer = io.BytesIO()
    df.to_excel(buffer, index=False, engine="openpyxl")
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=schedule_results.xlsx"},
    )
