import { useCallback, useRef, useState } from "react";

export default function UploadZone({ onFileSelected, disabled }) {
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef(null);

  const handleDrop = useCallback(
    (e) => {
      e.preventDefault();
      setIsDragging(false);
      if (disabled) return;
      const file = e.dataTransfer.files?.[0];
      if (file) onFileSelected(file);
    },
    [onFileSelected, disabled]
  );

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        if (!disabled) setIsDragging(true);
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={handleDrop}
      onClick={() => !disabled && inputRef.current?.click()}
      className={`group cursor-pointer rounded-xl border-2 border-dashed p-10 text-center transition-colors
        ${isDragging ? "border-primary bg-primary/5" : "border-line bg-white/40 hover:border-primary/60"}
        ${disabled ? "cursor-not-allowed opacity-60" : ""}`}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".xlsx,.xls"
        className="hidden"
        disabled={disabled}
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) onFileSelected(file);
        }}
      />
      <p className="font-display text-lg text-ink">فایل اکسل داده‌ها را اینجا رها کنید</p>
      <p className="mt-1 font-body text-sm text-ink/60">یا برای انتخاب فایل کلیک کنید — فقط xlsx</p>

      <a
        href="/schedule-template.xlsx"
        download
        onClick={(e) => e.stopPropagation()}
        className="relative z-10 mt-4 inline-block text-sm text-primary underline decoration-primary/40 underline-offset-4 hover:text-primary-dark"
      >
        دانلود نمونه فایل اکسل (تمپلیت)
      </a>
    </div>
  );
}
