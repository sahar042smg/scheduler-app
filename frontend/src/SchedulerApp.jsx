import { useState } from "react";
import TimetableGrid from "./components/TimetableGrid";
import UploadZone from "./components/UploadZone";
import ResultsTable from "./components/ResultsTable";
import WarningDialog from "./components/WarningDialog";
import OptionPicker from "./components/OptionPicker";
import AdminPanel from "./AdminPanel";
import { useAuth } from "./AuthContext";
import { uploadExcel, solveSchedule, downloadResultsUrl } from "./api";

// مراحل جریان کار: انتخاب فایل -> پارس/اعتبارسنجی -> حل مدل -> انتخاب گزینه -> نمایش نتیجه
const STAGE = {
  IDLE: "idle",
  PARSING: "parsing",
  PARSED: "parsed",
  SOLVING: "solving",
  CHOOSING: "choosing",
  DONE: "done",
  ERROR: "error",
};

export default function SchedulerApp() {
  const { user, logout } = useAuth();
  const [showAdminPanel, setShowAdminPanel] = useState(false);
  const [stage, setStage] = useState(STAGE.IDLE);
  const [parsedData, setParsedData] = useState(null);
  const [result, setResult] = useState(null);
  const [selectedOptionIndex, setSelectedOptionIndex] = useState(0);
  const [errorMessage, setErrorMessage] = useState("");
  const [pendingWarnings, setPendingWarnings] = useState([]);

  async function handleFileSelected(file) {
    setStage(STAGE.PARSING);
    setErrorMessage("");
    try {
      const uploadResult = await uploadExcel(file);
      setParsedData(uploadResult.data);
      if (uploadResult.warnings.length > 0) {
        setPendingWarnings(uploadResult.warnings);
      } else {
        setStage(STAGE.PARSED);
      }
    } catch (err) {
      setErrorMessage(err.message);
      setStage(STAGE.ERROR);
    }
  }

  function handleWarningContinue(warning) {
    // کاربر تایید کرد ادامه بده: استادهای این هشدار به‌عنوان «بدون هیچ
    // محدودیت زمانی» علامت می‌خورند تا solver بتواند آن‌ها را در هر
    // بازه‌ای قرار دهد.
    setParsedData((prev) => ({
      ...prev,
      professors_without_preference_constraint: [
        ...prev.professors_without_preference_constraint,
        ...warning.professor_codes,
      ],
    }));
    const remaining = pendingWarnings.slice(1);
    setPendingWarnings(remaining);
    if (remaining.length === 0) setStage(STAGE.PARSED);
  }

  function handleWarningStop() {
    setPendingWarnings([]);
    handleReset();
  }

  async function handleSolve() {
    setStage(STAGE.SOLVING);
    setErrorMessage("");
    try {
      const res = await solveSchedule(parsedData);
      setResult(res);
      setStage(STAGE.CHOOSING);
    } catch (err) {
      setErrorMessage(err.message);
      setStage(STAGE.ERROR);
    }
  }

  function handleSelectOption(index) {
    setSelectedOptionIndex(index);
    setStage(STAGE.DONE);
  }

  function handleReset() {
    setStage(STAGE.IDLE);
    setParsedData(null);
    setResult(null);
    setSelectedOptionIndex(0);
    setErrorMessage("");
    setPendingWarnings([]);
  }

  const gridState =
    stage === STAGE.PARSING || stage === STAGE.SOLVING
      ? "processing"
      : stage === STAGE.CHOOSING || stage === STAGE.DONE
      ? "done"
      : "idle";

  return (
    <div dir="rtl" className="min-h-screen bg-paper text-ink font-body">
      {pendingWarnings.length > 0 && (
        <WarningDialog
          warning={pendingWarnings[0]}
          onContinue={() => handleWarningContinue(pendingWarnings[0])}
          onStop={handleWarningStop}
        />
      )}
      <div className="mx-auto max-w-3xl px-6 py-16">
        {showAdminPanel && <AdminPanel onClose={() => setShowAdminPanel(false)} />}

        {/* نوار حساب کاربری */}
        <div className="mb-8 flex items-center justify-between text-sm text-ink/60">
          <span dir="ltr">{user?.email}</span>
          <div className="flex items-center gap-4">
            {user?.is_admin && (
              <button onClick={() => setShowAdminPanel(true)} className="hover:text-primary hover:underline">
                مدیریت کاربران
              </button>
            )}
            <button onClick={logout} className="hover:text-primary hover:underline">
              خروج
            </button>
          </div>
        </div>

        {/* هدر / hero */}
        <header className="mb-12 flex items-center justify-between gap-8">
          <div>
            <p className="mb-2 font-body text-xs font-medium text-brass">
              دانشکده مهندسی صنایع و سیستم‌ها
            </p>
            <h1 className="font-display text-3xl font-semibold leading-tight text-ink sm:text-4xl">
              زمان‌بندی خودکار دروس
            </h1>
            <p className="mt-3 max-w-md font-body text-ink/70">
              داده‌ها را آپلود کنید تا بهترین چینش کلاس‌ها و اساتید بر اساس
              زمان‌های در دسترسِ اساتید محاسبه شود.
            </p>
          </div>
          <TimetableGrid state={gridState} />
        </header>

        {/* بدنه‌ی اصلی بر اساس مرحله */}
        <main>
          {(stage === STAGE.IDLE || stage === STAGE.ERROR) && (
            <>
              <UploadZone onFileSelected={handleFileSelected} disabled={false} />
              {stage === STAGE.ERROR && (
                <div className="mt-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
                  {errorMessage}
                </div>
              )}
            </>
          )}

          {stage === STAGE.PARSING && (
            <div className="rounded-xl border border-line bg-white/40 p-10 text-center">
              <p className="font-display text-lg">در حال خواندن و بررسی فایل...</p>
            </div>
          )}

          {stage === STAGE.PARSED && parsedData && (
            <div className="rounded-xl border border-line bg-white/50 p-8">
              <p className="font-display text-lg text-ink">فایل با موفقیت خوانده شد.</p>
              <dl className="mt-4 grid grid-cols-2 gap-3 text-sm text-ink/70 sm:grid-cols-4">
                <div>
                  <dt className="font-body text-ink/50">اساتید</dt>
                  <dd className="font-mono text-lg text-primary">{parsedData.professors.length}</dd>
                </div>
                <div>
                  <dt className="font-body text-ink/50">دروس</dt>
                  <dd className="font-mono text-lg text-primary">{parsedData.courses.length}</dd>
                </div>
                <div>
                  <dt className="font-body text-ink/50">ارائه‌ها</dt>
                  <dd className="font-mono text-lg text-primary">{parsedData.offerings.length}</dd>
                </div>
                <div>
                  <dt className="font-body text-ink/50">کلاس‌ها</dt>
                  <dd className="font-mono text-lg text-primary">{parsedData.classrooms.length}</dd>
                </div>
              </dl>
              <div className="mt-6 flex gap-3">
                <button
                  onClick={handleSolve}
                  className="rounded-lg bg-primary px-5 py-2.5 font-body font-medium text-paper transition-colors hover:bg-primary-dark"
                >
                  اجرای زمان‌بندی
                </button>
                <button
                  onClick={handleReset}
                  className="rounded-lg border border-line px-5 py-2.5 font-body text-ink/70 transition-colors hover:bg-white"
                >
                  فایل دیگر
                </button>
              </div>
            </div>
          )}

          {stage === STAGE.SOLVING && (
            <div className="rounded-xl border border-line bg-white/40 p-10 text-center">
              <p className="font-display text-lg">در حال محاسبه‌ی بهترین چینش...</p>
            </div>
          )}

          {stage === STAGE.CHOOSING && result && (
            <div>
              {result.message && (
                <div className="mb-4 rounded-lg border border-brass/30 bg-brass/10 px-4 py-3 text-sm text-ink/80">
                  {result.message}
                </div>
              )}
              <OptionPicker options={result.options} onSelect={handleSelectOption} />
            </div>
          )}

          {stage === STAGE.DONE && result && (
            <div>
              <div className="mb-4 flex items-center justify-between">
                <p className="font-display text-lg">
                  {result.options[selectedOptionIndex].label} —{" "}
                  {result.options[selectedOptionIndex].assignments.length} جلسه زمان‌بندی شد.
                </p>
                <div className="flex gap-3">
                  <a
                    href={downloadResultsUrl(selectedOptionIndex)}
                    className="rounded-lg bg-brass px-5 py-2.5 font-body font-medium text-ink transition-colors hover:brightness-95"
                  >
                    دانلود اکسل نتایج
                  </a>
                  {result.options.length > 1 && (
                    <button
                      onClick={() => setStage(STAGE.CHOOSING)}
                      className="rounded-lg border border-line px-5 py-2.5 font-body text-ink/70 transition-colors hover:bg-white"
                    >
                      مقایسه با گزینه‌های دیگر
                    </button>
                  )}
                  <button
                    onClick={handleReset}
                    className="rounded-lg border border-line px-5 py-2.5 font-body text-ink/70 transition-colors hover:bg-white"
                  >
                    شروع دوباره
                  </button>
                </div>
              </div>
              <ResultsTable assignments={result.options[selectedOptionIndex].assignments} />
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
