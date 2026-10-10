// در استقرار، آدرس بک‌اند واقعی از طریق متغیر محیطی VITE_API_URL
// (هنگام build) تزریق می‌شود. در توسعه‌ی محلی، به uvicorn روی 8000
// بازمی‌گردد.
const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

function authHeaders() {
  const token = localStorage.getItem("auth_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function handleResponse(res) {
  if (!res.ok) {
    let detail = "خطای نامشخص از سرور.";
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      // پاسخ JSON نبود؛ از پیام پیش‌فرض استفاده می‌شود.
    }
    throw new Error(detail);
  }
  return res.json();
}

export async function uploadExcel(file) {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${BASE_URL}/api/schedule/upload`, {
    method: "POST",
    headers: { ...authHeaders() },
    body: formData,
  });
  return handleResponse(res);
}

export async function solveSchedule(parsedData) {
  const res = await fetch(`${BASE_URL}/api/schedule/solve`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify(parsedData),
  });
  return handleResponse(res);
}

export function downloadResultsUrl(optionIndex = 0) {
  // چون این یک لینک مستقیم <a href> است (نه fetch)، توکن را به‌صورت
  // query param اضافه می‌کنیم تا بک‌اند بتواند هویت کاربر را تایید کند.
  const token = localStorage.getItem("auth_token");
  return `${BASE_URL}/api/schedule/download?option=${optionIndex}&token=${encodeURIComponent(token || "")}`;
}
