export default function OptionPicker({ options, onSelect }) {
  return (
    <div>
      <p className="mb-1 font-display text-lg text-ink">
        {options.length > 1
          ? `${options.length} چینش متفاوت پیدا شد — یکی را برای مشاهده انتخاب کنید.`
          : "یک چینش پیدا شد."}
      </p>
      <p className="mb-5 font-body text-sm text-ink/60">
        گزینه‌ی اول بهترین حالتِ یافته‌شده است؛ بقیه چینش‌های متفاوتِ دیگری هستند.
      </p>
      <div className={`grid gap-4 ${options.length > 1 ? "sm:grid-cols-3" : "sm:grid-cols-1"}`}>
        {options.map((option, index) => (
          <button
            key={option.label}
            onClick={() => onSelect(index)}
            className="rounded-xl border border-line bg-white/60 p-5 text-right transition-colors hover:border-primary hover:bg-white"
          >
            <p className="font-display text-base text-ink">{option.label}</p>
            {index === 0 && options.length > 1 && (
              <span className="mt-1 inline-block rounded-full bg-primary/10 px-2 py-0.5 text-xs text-primary">
                بهترین گزینه
              </span>
            )}
            <p className="mt-3 font-mono text-sm text-ink/60">
              {option.assignments.length} جلسه
            </p>
          </button>
        ))}
      </div>
    </div>
  );
}
