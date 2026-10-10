import { useAuth } from "./AuthContext";
import AuthGate from "./AuthGate";
import SchedulerApp from "./SchedulerApp";

export default function App() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-paper font-body text-ink/60">
        در حال بررسی ورود...
      </div>
    );
  }

  return user ? <SchedulerApp /> : <AuthGate />;
}
