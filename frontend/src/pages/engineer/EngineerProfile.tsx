import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useAuthStore } from "../../store/authStore";
import { getMyPermits } from "../../api";
import type { Permit } from "../../api/types";

export default function EngineerProfile() {
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
            <div style={{ fontSize: 12, color: "#64748b" }}>Роль</div>
            <div style={{ fontWeight: 600 }}>Ведущий инженер</div>
          </div>
        </div>
      </div>

      <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 12 }}>Выданные наряды-допуска</h2>
      {isLoading ? (
        <p>Загрузка...</p>
      ) : !permits || permits.length === 0 ? (
        <div className="card" style={{ color: "#64748b", textAlign: "center" }}>Нарядов-допуска ещё нет.</div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {permits.map((p: Permit) => {
            const payload = p.payload as any;
            return (
              <div key={p.permit_id} className="card">
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div>
                    <div style={{ fontWeight: 700 }}>{p.permit_id}</div>
                    <div style={{ fontSize: 13, color: "#64748b" }}>
                      {payload?.installer?.full_name} · {p.permit_date}
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
            );
          })}
        </div>
      )}
    </div>
  );
}
