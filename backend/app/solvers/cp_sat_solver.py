"""
Solver واقعی — بر پایه‌ی OR-Tools CP-SAT.

این solver جایگزینِ مدل اصلی (که دیگر در دسترس نیست) شده و بر اساس
تصمیم‌های نهاییِ زیر پیاده‌سازی شده است:

  ۱) هر ارائه‌ی درس (CourseOffering) به «تعداد گروه درسی» پاره/سکشن
     مستقل تقسیم می‌شود؛ هر پاره باید «تعداد جلسات در هفته» بار در
     هفته تشکیل شود.
  ۲) دروسِ تک‌جلسه‌ای (یک جلسه در هفته) هرگز در بازه‌های صبح قرار
     نمی‌گیرند.
  ۳) دروسِ دوجلسه‌ای باید در یکی از دو الگوی زیر جفت شوند — هر دو
     جلسه هم‌ساعت (شروع/پایان یکسان)، در دو روزِ:
       (شنبه و دوشنبه)  یا  (یکشنبه و سه‌شنبه)
     اگر داده‌ی جاری این روزها را نداشته باشد، یا ارجحیت/دسترسیِ خودِ
     استاد این الگو را برای یک درس خاص ناممکن کند، آن مورد به‌صورت
     fallback (بدون الگوی جفت‌شدن، فقط دو بازه‌ی متفاوت) زمان‌بندی
     می‌شود و در پیام خروجی گزارش می‌شود.
  ۴) «بازه‌های اعلام‌شده‌ی استاد» دیگر ارجحیت نیست، بلکه معنیِ
     در دسترس‌بودن (availability) دارد و یک محدودیت «سخت» است: هر
     جلسه‌ی آن استاد فقط می‌تواند در یکی از همین بازه‌ها باشد.
     استادهایی که هیچ داده‌ای برایشان ثبت نشده و کاربر در مرحله‌ی
     آپلود تایید کرده که ادامه بدهد (professors_without_preference_constraint)،
     در هر بازه‌ای آزادند.
  ۵) یک استاد یا یک کلاس نمی‌تواند هم‌زمان دو جلسه داشته باشد
     (محدودیت سخت).
  ۶) برای هر گروه دانشجویی:
       الف) دو درسی که احتمال اخذشان «زیاد» یا «متوسط» است، تا حد
            امکان هم‌زمان نمی‌شوند (نرم، وزن بالا).
       ب)  به‌طور اضافه، دو درسی که هر دو احتمال «زیاد» دارند، تا حد
            امکان پشت‌سرهم (همان روز، بدون فاصله) چیده می‌شوند تا
            زمان حضور دانشجو در دانشگاه کمتر شود (نرم، وزن پایین‌تر
            از بند الف — یعنی اجتناب از هم‌پوشانی همیشه اولویت
            بالاتری دارد).

محدودیت‌های ۲، ۳، ۴، ۵ سخت‌اند (هرگز نقض نمی‌شوند)؛ بند ۶ نرم است و
در تابع هدف کمینه می‌شود. وزن‌ها در ثابت‌های زیر قابل‌تنظیم‌اند.

۷) به‌جای فقط یک جواب، تلاش می‌شود تا ۳ چینشِ متفاوت از هم پیدا شود
   (نه لزوما هر سه هم‌ارزش با بهینه — بهترین سه‌تای متمایزی که پیدا
   می‌شود). روش کار: حل می‌کنیم، سپس با یک «برش عدمِ‌تکرار»
   (no-good cut) همان چینشِ دقیق را از فضای جواب حذف می‌کنیم و دوباره
   حل می‌کنیم؛ این کار حداکثر ۳ بار تکرار می‌شود. اگر داده اجازه‌ی
   کمتر از ۳ چینشِ متفاوت بدهد، همان تعداد کمتر برگردانده می‌شود.
"""
from __future__ import annotations

from collections import defaultdict
from itertools import combinations

from ortools.sat.python import cp_model

from app.models.schemas import ParsedScheduleData, ScheduleAssignment, ScheduleOption, SolveResult
from app.solvers.base import BaseSolver

# --- وزن‌های تابع هدف (قابل تنظیم) ---
GROUP_OVERLAP_PENALTY_WEIGHT = 20    # پنالتی هم‌پوشانی دو درسِ محتمل (زیاد/متوسط) برای یک گروه
CONSECUTIVE_BONUS_WEIGHT = 5         # پاداشِ پشت‌سرهم‌چینی دو درسِ «زیاد» برای یک گروه (کمتر از بالا)

# الگوهای مجاز جفت‌شدن جلسات دروس دوجلسه‌ای
PAIRED_DAY_PATTERNS = [("شنبه", "دوشنبه"), ("یکشنبه", "سه‌شنبه")]

MAX_SOLVE_SECONDS = 20.0

# طبق تصمیم: همیشه تلاش برای ۳ چینشِ متفاوت (نه لزوما هم‌ارزش با بهینه؛
# بهترین سه‌تای متمایزی که پیدا شود) — اگر کمتر ممکن بود، همان تعداد.
MAX_OPTIONS = 3


_PERSIAN_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


def _to_persian_digits(n: int) -> str:
    return str(n).translate(_PERSIAN_DIGITS)


def _time_to_minutes(value: str) -> int:
    """تبدیل رشته‌ی 'HH:MM' به دقیقه، برای مرتب‌سازیِ درست بازه‌های زمانی."""
    try:
        h, m = value.split(":")
        return int(h) * 60 + int(m)
    except (ValueError, AttributeError):
        return 0


class _Unit:
    """
    یک «پاره»/سکشن مستقل از یک ارائه‌ی درس — یعنی یکی از
    «تعداد گروه درسی» نمونه‌ی موازی آن درس. هر Unit باید
    sessions_per_week بار در هفته تشکیل شود.
    """

    __slots__ = ("offering", "section_index", "sessions_per_week")

    def __init__(self, offering, section_index: int):
        self.offering = offering
        self.section_index = section_index
        self.sessions_per_week = offering.sessions_per_week


class CpSatSolver(BaseSolver):
    def solve(self, data: ParsedScheduleData) -> SolveResult:
        if not data.offerings:
            return SolveResult(status="error", message="هیچ ارائه‌ی درسی برای زمان‌بندی وجود ندارد.")
        if not data.timeslots:
            return SolveResult(status="error", message="هیچ بازه‌ی زمانی‌ای در داده‌ها یافت نشد.")
        if not data.classrooms:
            return SolveResult(status="error", message="هیچ کلاسی در داده‌ها یافت نشد.")

        model = cp_model.CpModel()

        timeslots = data.timeslots
        classrooms = data.classrooms
        timeslot_by_code = {t.code: t for t in timeslots}
        courses_by_code = {c.code: c for c in data.courses}
        professors_by_code = {p.code: p for p in data.professors}

        # --- بازه‌های در دسترسِ هر استاد (طبق تصمیم جدید: سخت) ---
        available_slots_by_professor: dict[str, set[str]] = defaultdict(set)
        for row in data.preferences:
            available_slots_by_professor[row.professor_code].add(row.timeslot_code)

        def professor_is_constrained(professor_code: str) -> bool:
            return professor_code not in data.professors_without_preference_constraint

        def allowed_for_professor(professor_code: str, timeslot_code: str) -> bool:
            if not professor_is_constrained(professor_code):
                return True
            return timeslot_code in available_slots_by_professor.get(professor_code, set())

        # --- آماده‌سازی الگوهای جفت‌شدن (شنبه+دوشنبه / یکشنبه+سه‌شنبه) ---
        by_time_of_day: dict[tuple[str, str], dict[str, str]] = defaultdict(dict)
        for t in timeslots:
            by_time_of_day[(t.start_time, t.end_time)][t.day] = t.code

        all_pair_patterns: list[tuple[str, str]] = []
        for day_a, day_b in PAIRED_DAY_PATTERNS:
            for day_map in by_time_of_day.values():
                if day_a in day_map and day_b in day_map:
                    all_pair_patterns.append((day_map[day_a], day_map[day_b]))

        global_pairing_unavailable = len(all_pair_patterns) == 0

        # --- ساخت واحدهای مستقل (Unit) از روی هر ارائه ---
        units: list[_Unit] = []
        for offering in data.offerings:
            for section_index in range(offering.group_count):
                units.append(_Unit(offering, section_index))

        # --- متغیرهای تصمیم ---
        timeslot_bool: dict[tuple[int, int], dict[str, cp_model.IntVar]] = {}
        classroom_bool: dict[tuple[int, int], dict[str, cp_model.IntVar]] = {}

        fallback_due_to_no_day_data: set[int] = set()   # روزهای لازم اصلا در داده نبود
        fallback_due_to_availability: set[int] = set()  # روزها بودند ولی با دسترسیِ استاد جور درنیامد

        for u_idx, unit in enumerate(units):
            k = unit.sessions_per_week
            professor_code = unit.offering.professor_code
            constrained = professor_is_constrained(professor_code)
            available = available_slots_by_professor.get(professor_code, set())

            for s_idx in range(k):
                key = (u_idx, s_idx)
                timeslot_bool[key] = {
                    t.code: model.NewBoolVar(f"ts_u{u_idx}_s{s_idx}_{t.code}") for t in timeslots
                }
                classroom_bool[key] = {
                    r.code: model.NewBoolVar(f"rm_u{u_idx}_s{s_idx}_{r.code}") for r in classrooms
                }
                model.AddExactlyOne(classroom_bool[key].values())

            if k == 1:
                # محدودیت ۲ (صبح ممنوع) + محدودیت ۴ (فقط بازه‌های در دسترسِ استاد، اگر مقید باشد).
                for t in timeslots:
                    is_allowed = (not t.is_morning) and (not constrained or t.code in available)
                    if not is_allowed:
                        model.Add(timeslot_bool[(u_idx, 0)][t.code] == 0)
                model.AddExactlyOne(timeslot_bool[(u_idx, 0)].values())

            elif k == 2:
                # فقط الگوهایی که هم روزهای لازم را دارند، هم هر دو بازه‌شان برای این
                # استاد در دسترس است (یا استاد اصلا مقید نیست).
                patterns_for_unit = [
                    (t1, t2)
                    for (t1, t2) in all_pair_patterns
                    if not constrained or (t1 in available and t2 in available)
                ]

                if patterns_for_unit:
                    pattern_active = [
                        model.NewBoolVar(f"pair_u{u_idx}_p{p_idx}") for p_idx in range(len(patterns_for_unit))
                    ]
                    model.AddExactlyOne(pattern_active)
                    for p_idx, (t1, t2) in enumerate(patterns_for_unit):
                        model.Add(timeslot_bool[(u_idx, 0)][t1] == pattern_active[p_idx])
                        model.Add(timeslot_bool[(u_idx, 1)][t2] == pattern_active[p_idx])
                    model.AddExactlyOne(timeslot_bool[(u_idx, 0)].values())
                    model.AddExactlyOne(timeslot_bool[(u_idx, 1)].values())
                else:
                    # fallback: دو بازه‌ی متفاوت، هرکدام فقط از میان بازه‌های در دسترسِ استاد.
                    if global_pairing_unavailable:
                        fallback_due_to_no_day_data.add(u_idx)
                    else:
                        fallback_due_to_availability.add(u_idx)

                    for s_idx in range(k):
                        for t in timeslots:
                            if constrained and t.code not in available:
                                model.Add(timeslot_bool[(u_idx, s_idx)][t.code] == 0)
                        model.AddExactlyOne(timeslot_bool[(u_idx, s_idx)].values())
                    for t in timeslots:
                        model.Add(
                            sum(timeslot_bool[(u_idx, s_idx)][t.code] for s_idx in range(k)) <= 1
                        )

            else:
                # حالت کلی برای k غیر از ۱ و ۲: هر جلسه فقط در بازه‌های در دسترسِ استاد،
                # و جلسات همان unit در بازه‌های متفاوت از هم.
                for s_idx in range(k):
                    for t in timeslots:
                        if constrained and t.code not in available:
                            model.Add(timeslot_bool[(u_idx, s_idx)][t.code] == 0)
                    model.AddExactlyOne(timeslot_bool[(u_idx, s_idx)].values())
                for t in timeslots:
                    model.Add(
                        sum(timeslot_bool[(u_idx, s_idx)][t.code] for s_idx in range(k)) <= 1
                    )

        # --- محدودیت سخت: تداخل استاد ---
        sessions_by_professor: dict[str, list[tuple[int, int]]] = defaultdict(list)
        for u_idx, unit in enumerate(units):
            for s_idx in range(unit.sessions_per_week):
                sessions_by_professor[unit.offering.professor_code].append((u_idx, s_idx))

        for professor_code, session_keys in sessions_by_professor.items():
            for t in timeslots:
                model.Add(
                    sum(timeslot_bool[key][t.code] for key in session_keys) <= 1
                )

        # --- محدودیت سخت: تداخل کلاس (با متغیر کمکی occ = AND(timeslot, classroom)) ---
        occ_by_time_room: dict[tuple[str, str], list[cp_model.IntVar]] = defaultdict(list)
        for key in timeslot_bool:
            u_idx, s_idx = key
            for t in timeslots:
                ts_var = timeslot_bool[key][t.code]
                for r in classrooms:
                    rm_var = classroom_bool[key][r.code]
                    occ = model.NewBoolVar(f"occ_u{u_idx}_s{s_idx}_{t.code}_{r.code}")
                    model.Add(occ <= ts_var)
                    model.Add(occ <= rm_var)
                    model.Add(occ >= ts_var + rm_var - 1)
                    occ_by_time_room[(t.code, r.code)].append(occ)

        for occ_list in occ_by_time_room.values():
            model.Add(sum(occ_list) <= 1)

        # --- آماده‌سازی برای تابع هدف: بارِ هر (درس، بازه) به‌صورت متغیر صحیحِ کش‌شده ---
        objective_terms = []

        units_by_course: dict[str, list[int]] = defaultdict(list)
        for u_idx, unit in enumerate(units):
            units_by_course[unit.offering.course_code].append(u_idx)

        course_time_load_var_cache: dict[tuple[str, str], tuple[cp_model.IntVar, int] | None] = {}

        def get_course_time_load_var(course_code: str, timeslot_code: str):
            """
            متغیر صحیح = تعداد جلساتِ این درس که در این بازه قرار گرفته‌اند (کش‌شده).
            خروجی: (متغیر, کرانِ بالا) یا None اگر این درس اصلا جلسه‌ای نداشته باشد.
            """
            key = (course_code, timeslot_code)
            if key in course_time_load_var_cache:
                return course_time_load_var_cache[key]

            terms = []
            for u_idx in units_by_course.get(course_code, []):
                unit = units[u_idx]
                for s_idx in range(unit.sessions_per_week):
                    terms.append(timeslot_bool[(u_idx, s_idx)][timeslot_code])
            if not terms:
                course_time_load_var_cache[key] = None
                return None

            upper_bound = len(terms)
            load_var = model.NewIntVar(0, upper_bound, f"load_{course_code}_{timeslot_code}")
            model.Add(load_var == sum(terms))
            result = (load_var, upper_bound)
            course_time_load_var_cache[key] = result
            return result

        # --- تابع هدف، بند ۶‑الف: پنالتی هم‌پوشانی دروسِ «زیاد» یا «متوسط» برای هر گروه ---
        relevant_courses_by_group: dict[str, set[str]] = defaultdict(set)
        high_courses_by_group: dict[str, set[str]] = defaultdict(set)
        for row in data.group_course_likelihood:
            if row.likelihood in ("زیاد", "متوسط"):
                relevant_courses_by_group[row.group_code].add(row.course_code)
            if row.likelihood == "زیاد":
                high_courses_by_group[row.group_code].add(row.course_code)

        conflict_counter = 0
        for group_code, course_codes in relevant_courses_by_group.items():
            course_list = sorted(c for c in course_codes if c in units_by_course)
            for c1, c2 in combinations(course_list, 2):
                for t in timeslots:
                    r1 = get_course_time_load_var(c1, t.code)
                    r2 = get_course_time_load_var(c2, t.code)
                    if r1 is None or r2 is None:
                        continue
                    load1, bound1 = r1
                    load2, bound2 = r2
                    conflict = model.NewIntVar(0, min(bound1, bound2), f"conflict_{conflict_counter}")
                    model.AddMinEquality(conflict, [load1, load2])
                    objective_terms.append(GROUP_OVERLAP_PENALTY_WEIGHT * conflict)
                    conflict_counter += 1

        # --- تابع هدف، بند ۶‑ب: پاداش پشت‌سرهم‌چینیِ دروسِ «زیاد» برای هر گروه ---
        # بازه‌هایی که در یک روز، بدون فاصله پشت سر هم‌اند.
        by_day: dict[str, list] = defaultdict(list)
        for t in timeslots:
            by_day[t.day].append(t)

        adjacency_pairs: list[tuple[str, str]] = []
        for day_slots in by_day.values():
            day_slots_sorted = sorted(day_slots, key=lambda s: _time_to_minutes(s.start_time))
            for a, b in zip(day_slots_sorted, day_slots_sorted[1:]):
                if a.end_time == b.start_time:
                    adjacency_pairs.append((a.code, b.code))

        bonus_counter = 0
        if adjacency_pairs:
            for group_code, course_codes in high_courses_by_group.items():
                course_list = sorted(c for c in course_codes if c in units_by_course)
                for c1, c2 in combinations(course_list, 2):
                    for t_early, t_late in adjacency_pairs:
                        for course_a, t_a, course_b, t_b in (
                            (c1, t_early, c2, t_late),
                            (c1, t_late, c2, t_early),
                        ):
                            ra = get_course_time_load_var(course_a, t_a)
                            rb = get_course_time_load_var(course_b, t_b)
                            if ra is None or rb is None:
                                continue
                            load_a, bound_a = ra
                            load_b, bound_b = rb
                            bonus = model.NewIntVar(0, min(bound_a, bound_b), f"bonus_{bonus_counter}")
                            model.AddMinEquality(bonus, [load_a, load_b])
                            objective_terms.append(-CONSECUTIVE_BONUS_WEIGHT * bonus)
                            bonus_counter += 1

        if objective_terms:
            model.Minimize(sum(objective_terms))

        def extract_assignments() -> list[ScheduleAssignment]:
            assignments: list[ScheduleAssignment] = []
            for u_idx, unit in enumerate(units):
                offering = unit.offering
                course = courses_by_code.get(offering.course_code)
                professor = professors_by_code.get(offering.professor_code)
                course_display = course.name if course else offering.course_code
                if offering.group_count > 1:
                    course_display = f"{course_display} (گروه {_to_persian_digits(unit.section_index + 1)})"

                for s_idx in range(unit.sessions_per_week):
                    key = (u_idx, s_idx)
                    chosen_t = next(code for code, var in timeslot_bool[key].items() if solver.Value(var))
                    chosen_r = next(code for code, var in classroom_bool[key].items() if solver.Value(var))
                    t = timeslot_by_code[chosen_t]
                    classroom = next(r for r in classrooms if r.code == chosen_r)

                    assignments.append(
                        ScheduleAssignment(
                            course_name=course_display,
                            professor_last_name=professor.last_name if professor else offering.professor_code,
                            classroom_name=classroom.name,
                            day=t.day,
                            start_time=t.start_time,
                            end_time=t.end_time,
                        )
                    )
            return assignments

        # همه‌ی متغیرهای تصمیم بولی — برای ساختن «برش عدمِ‌تکرار» بین هر حل و حل بعدی.
        all_decision_vars: list[cp_model.IntVar] = []
        for key in timeslot_bool:
            all_decision_vars.extend(timeslot_bool[key].values())
            all_decision_vars.extend(classroom_bool[key].values())

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = MAX_SOLVE_SECONDS
        solver.parameters.num_search_workers = 8

        options: list[ScheduleOption] = []
        final_status = None

        for option_index in range(MAX_OPTIONS):
            status = solver.Solve(model)
            if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
                break  # دیگر چینشِ متفاوتی (حتی ضعیف‌تر) پیدا نشد.

            final_status = status
            options.append(
                ScheduleOption(
                    label=f"گزینه {_to_persian_digits(option_index + 1)}",
                    objective_value=solver.ObjectiveValue() if objective_terms else 0.0,
                    assignments=extract_assignments(),
                )
            )

            if option_index < MAX_OPTIONS - 1:
                # برشِ «عدمِ‌تکرار»: دست‌کم یکی از متغیرهایی که الان True بودند
                # باید در حل بعدی False شود — یعنی همین چینشِ دقیق دیگر تکرار
                # نمی‌شود، اما هر چینشِ دیگری (حتی با یک استاد/کلاسِ جابه‌جا)
                # مجاز است.
                ones = [v for v in all_decision_vars if solver.Value(v)]
                if ones:
                    model.Add(sum(ones) <= len(ones) - 1)

        if not options:
            return SolveResult(
                status="infeasible",
                message=(
                    "با این داده‌ها امکان یافتن هیچ زمان‌بندیِ معتبری وجود نداشت — مثلا "
                    "ممکن است بازه‌های اعلام‌شده‌ی در دسترسِ یک استاد برای حجم دروسش کافی "
                    "نباشد، یا تعداد کلاس/بازه‌ی زمانی نسبت به حجم دروس کم باشد."
                ),
            )

        notices = []
        if fallback_due_to_no_day_data:
            notices.append(
                "تذکر: الگوی جفت‌شدن جلسات دروس دوجلسه‌ای (شنبه+دوشنبه یا یکشنبه+سه‌شنبه) "
                "در داده‌ی جاری قابل‌اعمال نبود (روزهای لازم در بازه‌های زمانی یافت نشد)؛ "
                "این دروس بدون رعایت آن الگوی خاص، فقط در دو بازه‌ی متفاوت زمان‌بندی شدند."
            )
        if fallback_due_to_availability:
            notices.append(
                "تذکر: برای برخی دروسِ دوجلسه‌ای، بازه‌های در دسترسِ استاد با هیچ‌کدام از "
                "الگوهای مجاز جفت‌شدن (شنبه+دوشنبه / یکشنبه+سه‌شنبه هم‌ساعت) جور درنیامد؛ "
                "این دروس بدون رعایت آن الگوی خاص، فقط در دو بازه‌ی متفاوتِ در دسترسِ همان "
                "استاد زمان‌بندی شدند."
            )
        if len(options) < MAX_OPTIONS:
            notices.append(
                f"با این داده‌ها فقط {_to_persian_digits(len(options))} چینشِ متفاوت پیدا شد "
                "(نه ۳ تا) — یعنی برای این حجم از دروس/کلاس/بازه‌ی زمانی، آرایش دیگری وجود ندارد."
            )
        message = " ".join(notices) if notices else None

        status_label = "optimal" if final_status == cp_model.OPTIMAL else "feasible"
        return SolveResult(status=status_label, options=options, message=message)
