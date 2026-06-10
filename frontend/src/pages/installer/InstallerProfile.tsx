import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useAuthStore } from "../../store/authStore";
import { getMyPermits } from "../../api";
import type { Permit } from "../../api/types";

export default function InstallerProfile() {
  const user = useAuthStore((s) => s.user);
  const { data: permits, isLoading } = useQuery({ queryKey: ["myPermits"], queryFn: getMyPermits });
  const [expanded, setExpanded] = useState<string | null>(null);

  return (
    <div className="page">
      <h1 className="page-title">Мой профиль</h1>

      <div className="card" style={{ marginBottom: 20 }}>
        <div style={{ display: "flex", gap: 24 }}>
          <div>
            <div style={{ fontSize: 12, color: "#64748b" }}>ФИО</div>
            <div style={{ fontWeight: 600 }}>{user?.full_name}</div>
          </div>
          <div>
            <div style={{ fontSize: 12, color: "#64748b" }}>Табельный №</div>
            <div style={{ fontWeight: 600 }}>{user?.employee_id ?? "—"}</div>
          </div>
          <div>
            <div style={{ fontSize: 12, color: "#64748b" }}>Роль</div>
            <div style={{ fontWeight: 600 }}>Инсталлятор</div>
          </div>
        </div>
      </div>

      <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 12 }}>Наряды-допуска</h2>
      {isLoading ? (
        <p>Загрузка...</p>
      ) : !permits || permits.length === 0 ? (
        <div className="card" style={{ color: "#64748b", textAlign: "center" }}>Нарядов-допуска ещё нет.</div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {permits.map((p: Permit) => (
            <div key={p.permit_id} className="card">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div>
                  <div style={{ fontWeight: 700 }}>{p.permit_id}</div>
                  <div style={{ fontSize: 13, color: "#64748b" }}>
                    {p.permit_date} · действителен до {new Date(p.valid_until).toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit" })}
                  </div>
                </div>
                <button
                  className="btn-outline"
                  style={{ fontSize: 12, padding: "6px 14px" }}
                  onClick={() => setExpanded(expanded === p.permit_id ? null : p.permit_id)}
                >
                  {expanded === p.permit_id ? "Скрыть" : "JSON"}
                </button>
              </div>
              {expanded === p.permit_id && (
                <pre style={{
                  marginTop: 16, background: "#f1f5f9", borderRadius: 8,
                  padding: 16, fontSize: 12, overflowX: "auto",
                }}>
                  {JSON.stringify(p.payload, null, 2)}
                </pre>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
