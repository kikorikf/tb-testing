import { Link, Outlet, useLocation } from "react-router-dom";
import { useAuthStore } from "../store/authStore";
import keycloak from "../keycloak";

export default function Layout() {
  const user = useAuthStore((s) => s.user);
  const location = useLocation();

  const installerNav = [
    { to: "/test", label: "Тест" },
    { to: "/wfm", label: "Наряды ВФМ" },
    { to: "/profile", label: "Профиль" },
  ];
  const engineerNav = [
    { to: "/approvals", label: "Апрувы" },
    { to: "/approvals/history", label: "История" },
    { to: "/questions", label: "Банк вопросов" },
    { to: "/eng-profile", label: "Профиль" },
  ];

  const nav = user?.role === "engineer" ? engineerNav : installerNav;

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      <header style={{
        background: "#1e3a8a",
        color: "#fff",
        padding: "0 24px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        height: 56,
        boxShadow: "0 2px 6px rgba(0,0,0,.2)",
      }}>
        <div style={{ fontWeight: 700, fontSize: 18 }}>ТБ-Допуск</div>
        <nav style={{ display: "flex", gap: 4 }}>
          {nav.map((item) => (
            <Link
              key={item.to}
              to={item.to}
              style={{
                color: location.pathname.startsWith(item.to) ? "#93c5fd" : "#fff",
                padding: "6px 14px",
                borderRadius: 6,
                fontWeight: location.pathname.startsWith(item.to) ? 700 : 400,
                fontSize: 14,
                background: location.pathname.startsWith(item.to) ? "rgba(255,255,255,.1)" : "transparent",
              }}
            >
              {item.label}
            </Link>
          ))}
        </nav>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <span style={{ fontSize: 13, opacity: 0.8 }}>{user?.full_name}</span>
          <button
            onClick={() => keycloak.logout()}
            style={{ background: "rgba(255,255,255,.15)", color: "#fff", fontSize: 13, padding: "5px 12px" }}
          >
            Выйти
          </button>
        </div>
      </header>
      <main style={{ flex: 1 }}>
        <Outlet />
      </main>
    </div>
  );
}
