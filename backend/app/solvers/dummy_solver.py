"""
Solver آزمایشی/موقت.

این solver هیچ بهینه‌سازیِ واقعی انجام نمی‌دهد — فقط هر ارائه‌ی درس را
به اولین کلاس و بازه‌ی زمانیِ آزاد نسبت می‌دهد (بدون رعایت هیچ محدودیتی).
هدف از وجود آن این است که بتوانیم مسیر «آپلود اکسل → حل → نمایش نتیجه»
را از همین حالا تست و دمو کنیم، بدون اینکه منتظر کد نهاییِ مدل بمانیم.

وقتی کد واقعیِ همکار رسید، فقط باید یک کلاس مثل RealMipSolver
(با ارث‌بری از BaseSolver) نوشته و در app/api/schedule.py جایگزین شود.
"""
from itertools import cycle

from app.models.schemas import ParsedScheduleData, ScheduleAssignment, ScheduleOption, SolveResult
from app.solvers.base import BaseSolver


class DummySolver(BaseSolver):
    def solve(self, data: ParsedScheduleData) -> SolveResult:
        if not data.offerings:
            return SolveResult(status="error", message="هیچ ارائه‌ی درسی برای زمان‌بندی وجود ندارد.")

        professors_by_code = {p.code: p for p in data.professors}
        courses_by_code = {c.code: c for c in data.courses}

        classrooms = cycle(data.classrooms) if data.classrooms else None
        timeslots = cycle(data.timeslots) if data.timeslots else None

        if classrooms is None or timeslots is None:
            return SolveResult(status="error", message="کلاس یا بازه‌ی زمانی‌ای در داده‌ها یافت نشد.")

        assignments: list[ScheduleAssignment] = []
        for offering in data.offerings:
            course = courses_by_code.get(offering.course_code)
            professor = professors_by_code.get(offering.professor_code)
            classroom = next(classrooms)
            slot = next(timeslots)

            assignments.append(
                ScheduleAssignment(
                    course_name=course.name if course else offering.course_code,
                    professor_last_name=professor.last_name if professor else offering.professor_code,
                    classroom_name=classroom.name,
                    day=slot.day,
                    start_time=slot.start_time,
                    end_time=slot.end_time,
                )
            )

        return SolveResult(
            status="feasible",
            options=[ScheduleOption(label="گزینه ۱", objective_value=0.0, assignments=assignments)],
        )
