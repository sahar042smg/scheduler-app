import { useEffect, useState } from "react";
import { fetchUsers, setUserActive } from "./authApi";
import { useAuth } from "./AuthContext";

export default function AdminPanel({ onClose }) {
  const { token } = useAuth();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadUsers() {
    setLoading(true);
    try {
      setUsers(await fetchUsers(token));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadUsers();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function toggle(userId, active) {
    try {
      await setUserActive(token, userId, active);
      await loadUsers();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div dir="rtl" className="fixed inset-0 z-50 flex items-start justify-center overflow-auto bg-ink/40 p-6">
      <div className="w-full max-w-2xl rounded-xl border border-line bg-paper p-6">
        <div className="mb-4 flex items-center justify-between">
          <p className="font-display text-xl font-semibold">مدیریت دسترسی کاربران</p>
          <button onClick={onClose} className="text-sm text-ink/60 hover:text-ink">
            بستن
          </button>
        </div>

        {error && (
          <div className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
            {error}
          </div>
        )}

        {loading ? (
          <p className="text-sm text-ink/60">در حال بارگذاری...</p>
        ) : (
          <div className="overflow-hidden rounded-lg border border-line">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-ink text-paper">
                  <th className="px-4 py-2 text-right font-medium">ایمیل</th>
                  <th className="px-4 py-2 text-right font-medium">نام</th>
                  <th className="px-4 py-2 text-right font-medium">وضعیت</th>
                  <th className="px-4 py-2 text-right font-medium">عملیات</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u, i) => (
                  <tr key={u.id} className={i % 2 === 0 ? "bg-white/60" : "bg-paper"}>
                    <td className="px-4 py-2" dir="ltr">
                      {u.email}
                    </td>
                    <td className="px-4 py-2">{u.full_name || "—"}</td>
                    <td className="px-4 py-2">
                      {u.is_admin ? (
                        <span className="text-brass">مدیر</span>
                      ) : u.is_active ? (
                        <span className="text-success">فعال</span>
                      ) : (
                        <span className="text-ink/50">در انتظار تایید</span>
                      )}
                    </td>
                    <td className="px-4 py-2">
                      {!u.is_admin && (
                        <button
                          onClick={() => toggle(u.id, !u.is_active)}
                          className={`rounded-md px-3 py-1 text-xs font-medium ${
                            u.is_active
                              ? "bg-red-50 text-red-700 hover:bg-red-100"
                              : "bg-primary text-paper hover:bg-primary-dark"
                          }`}
                        >
                          {u.is_active ? "غیرفعال کن" : "فعال کن"}
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
