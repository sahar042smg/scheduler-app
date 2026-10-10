import { useState } from "react";
import { registerUser } from "./authApi";
import { useAuth } from "./AuthContext";

export default function AuthGate() {
  const { login } = useAuth();
  const [mode, setMode] = useState("login"); // "login" | "register"
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [error, setError] = useState("");
  const [pendingMessage, setPendingMessage] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setPendingMessage("");
    setSubmitting(true);
    try {
      if (mode === "login") {
        await login(email, password);
      } else {
        const res = await registerUser(email, password, fullName);
        setPendingMessage(res.message);
        setMode("login");
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div dir="rtl" className="flex min-h-screen items-center justify-center bg-paper px-4 font-body text-ink">
      <div className="w-full max-w-sm rounded-xl border border-line bg-white/60 p-8">
        <p className="mb-1 font-display text-2xl font-semibold text-ink">
          زمان‌بندی خودکار دروس
        </p>
        <p className="mb-6 text-sm text-ink/60">
          {mode === "login" ? "برای ادامه وارد حساب خود شوید." : "برای درخواست دسترسی ثبت‌نام کنید."}
        </p>

        {pendingMessage && (
          <div className="mb-4 rounded-lg border border-success/30 bg-success/10 px-4 py-3 text-sm text-success">
            {pendingMessage}
          </div>
        )}
        {error && (
          <div className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {mode === "register" && (
            <div>
              <label className="mb-1 block text-sm text-ink/70">نام و نام خانوادگی</label>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="w-full rounded-lg border border-line bg-white px-3 py-2 text-sm outline-none focus:border-primary"
              />
            </div>
          )}
          <div>
            <label className="mb-1 block text-sm text-ink/70">ایمیل</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-lg border border-line bg-white px-3 py-2 text-sm outline-none focus:border-primary"
              dir="ltr"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm text-ink/70">رمز عبور</label>
            <input
              type="password"
              required
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-lg border border-line bg-white px-3 py-2 text-sm outline-none focus:border-primary"
              dir="ltr"
            />
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded-lg bg-primary px-4 py-2.5 font-medium text-paper transition-colors hover:bg-primary-dark disabled:opacity-60"
          >
            {mode === "login" ? "ورود" : "ثبت‌نام"}
          </button>
        </form>

        <button
          onClick={() => {
            setMode(mode === "login" ? "register" : "login");
            setError("");
            setPendingMessage("");
          }}
          className="mt-4 w-full text-center text-sm text-primary hover:underline"
        >
          {mode === "login" ? "حساب ندارید؟ ثبت‌نام کنید" : "حساب دارید؟ وارد شوید"}
        </button>
      </div>
    </div>
  );
}
