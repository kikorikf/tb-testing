import { Navigate } from "react-router-dom";
import { useAuthStore } from "../store/authStore";

interface Props {
  role: "installer" | "engineer";
  children: React.ReactNode;
}

export default function ProtectedRoute({ role, children }: Props) {
  const user = useAuthStore((s) => s.user);
  if (!user) return null;
  if (user.role !== role) {
    return <Navigate to="/" replace />;
  }
  return <>{children}</>;
}
