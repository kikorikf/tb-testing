import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { approveAccess, getPendingApprovals, rejectAccess } from "../../api";
import type { PendingApproval } from "../../api/types";

function formatDuration(sec: number) {
  const m = Math.floor(sec / 60);
  const s = sec % 60;
  return `${m}м ${s}с`;
}

export default function ApprovalQueue() {
  const queryClient = useQueryClient();

  const { data: items, isLoading } = useQuery({
    queryKey: ["pendingApprovals"],
    queryFn: getPendingApprovals,
    refetchInterval: 10000,
  });

  const approveMutation = useMutation({
    mutationFn: (id: string) => approveAccess(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["pendingApprovals"] }),
  });

  const rejectMutation = useMutation({
    mutationFn: (id: string) => rejectAccess(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["pendingApprovals"] }),
  });

  if (isLoading) return <div className="page">Загрузка...</div>;

  return (
    <div className="page">
      <h1 className="page-title">
        Очередь апрувов
        {items && items.length > 0 && (
          <span className="badge badge-blue" style={{ marginLeft: 12, fontSize: 14 }}>
            {items.length}
          </span>
        )}
      </h1>

      {!items || items.length === 0 ? (
        <div className="card" style={{ textAlign: "center", color: "#64748b", padding: 40 }}>
          <div style={{ fontSize: 40, marginBottom: 12 }}>✅</div>
          Нет ожидающих подтверждения
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          {items.map((item: PendingApproval) => (
            <div key={item.daily_access_id} className="card">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                <div>
                  <div style={{ fontWeight: 700, fontSize: 17 }}>{item.installer.full_name}</div>
                  <div style={{ color: "#64748b", fontSize: 13, marginTop: 2 }}>
                    Таб. №{item.installer.employee_id ?? "—"}
                  </div>
                </div>
                <div style={{ textAlign: "right" }}>
                  <div style={{ fontSize: 28, fontWeight: 800, color: item.session.score_pct >= 70 ? "#16a34a" : "#dc2626" }}>
                    {item.session.score_pct}%
                  </div>
                  <div style={{ fontSize: 12, color: "#64748b" }}>
                    {item.session.correct_cnt}/{item.session.total_cnt} · {formatDuration(item.session.duration_sec)}
                  </div>
                </div>
              </div>

              <div style={{ display: "flex", gap: 10, marginTop: 16 }}>
                <button
                  className="btn-success"
                  style={{ flex: 1 }}
                  onClick={() => approveMutation.mutate(item.daily_access_id)}
                  disabled={approveMutation.isPending || rejectMutation.isPending}
                >
                  ✓ Подтвердить
                </button>
                <button
                  className="btn-danger"
                  style={{ flex: 1 }}
                  onClick={() => rejectMutation.mutate(item.daily_access_id)}
                  disabled={approveMutation.isPending || rejectMutation.isPending}
                >
                  ✕ Отклонить
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
