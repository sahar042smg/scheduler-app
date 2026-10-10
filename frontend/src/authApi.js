// در استقرار، آدرس بک‌اند واقعی از طریق متغیر محیطی VITE_API_URL
// (هنگام build) تزریق می‌شود. در توسعه‌ی محلی، به uvicorn روی 8000
// بازمی‌گردد.
const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function handleResponse(res) {
  if (!res.ok) {
    let detail = "خطای نامشخص از سرور.";
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      // نادیده گرفته می‌شود
    }
    throw new Error(detail);
  }
  return res.json();
}

export async function registerUser(email, password, fullName) {
  const res = await fetch(`${BASE_URL}/api/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, full_name: fullName }),
  });
  return handleResponse(res);
}

export async function loginUser(email, password) {
  const res = await fetch(`${BASE_URL}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  return handleResponse(res);
}

export async function fetchMe(token) {
  const res = await fetch(`${BASE_URL}/api/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return handleResponse(res);
}

export async function fetchUsers(token) {
  const res = await fetch(`${BASE_URL}/api/admin/users`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return handleResponse(res);
}

export async function setUserActive(token, userId, active) {
  const action = active ? "activate" : "deactivate";
  const res = await fetch(`${BASE_URL}/api/admin/users/${userId}/${action}`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  return handleResponse(res);
}
