export default function WarningDialog({ warning, onContinue, onStop }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink/40 px-4">
      <div className="w-full max-w-md rounded-xl border border-line bg-paper p-6 shadow-xl">
        <p className="font-display text-lg text-ink">نیاز به تایید شما</p>
        <p className="mt-3 font-body text-sm leading-relaxed text-ink/80">
          {warning.message}
        </p>
        <div className="mt-6 flex justify-end gap-3">
          <button
            onClick={onStop}
            className="rounded-lg border border-line px-4 py-2 font-body text-sm text-ink/70 transition-colors hover:bg-white"
          >
            متوقف کن، دیتا را کامل می‌کنم
          </button>
          <button
            onClick={onContinue}
            className="rounded-lg bg-primary px-4 py-2 font-body text-sm font-medium text-paper transition-colors hover:bg-primary-dark"
          >
            همینطور ادامه بده
          </button>
        </div>
      </div>
    </div>
  );
}
