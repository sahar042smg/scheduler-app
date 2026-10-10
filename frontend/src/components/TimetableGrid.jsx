import { useEffect, useState } from "react";

const DAYS = ["ش", "ی", "د", "س"];
const SLOTS = [0, 1, 2, 3, 4];

/**
 * عنصر شاخص برنامه: یک شبکه‌ی کوچک شبیه جدول زمان‌بندی واقعی.
 * در حالت idle فقط خطوط شبکه دیده می‌شود؛ در حالت processing خانه‌ها
 * به‌ترتیب (مثل پر شدن واقعیِ یک برنامه‌ی هفتگی) رنگ می‌گیرند.
 */
export default function TimetableGrid({ state = "idle" }) {
  const [filledCount, setFilledCount] = useState(0);
  const totalCells = DAYS.length * SLOTS.length;

  useEffect(() => {
    if (state !== "processing") {
      setFilledCount(state === "done" ? totalCells : 0);
      return;
    }
    setFilledCount(0);
    const interval = setInterval(() => {
      setFilledCount((c) => {
        if (c >= totalCells) {
          clearInterval(interval);
          return c;
        }
        return c + 1;
      });
    }, 90);
    return () => clearInterval(interval);
  }, [state, totalCells]);

  return (
    <div
      className="inline-grid gap-1.5 p-4 rounded-lg border border-line bg-white/60"
      style={{ gridTemplateColumns: `repeat(${DAYS.length}, 1.75rem)` }}
      aria-hidden="true"
    >
      {SLOTS.map((slotIdx) =>
        DAYS.map((_, dayIdx) => {
          const cellIndex = slotIdx * DAYS.length + dayIdx;
          const filled = cellIndex < filledCount;
          return (
            <div
              key={`${slotIdx}-${dayIdx}`}
              className={`h-7 w-7 rounded-sm transition-colors duration-300 ${
                filled ? "bg-primary" : "bg-line/50"
              }`}
              style={
                filled
                  ? { backgroundColor: dayIdx % 3 === 0 ? "#C8963E" : "#1F3A93" }
                  : undefined
              }
            />
          );
        })
      )}
    </div>
  );
}
