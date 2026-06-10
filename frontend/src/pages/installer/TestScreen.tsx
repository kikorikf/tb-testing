import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { getTestStatus, startTest } from "../../api";

function statusBadge(status: string) {
  const map: Record<string, [string, string]> = {
    locked:           ["Заблокирован",         "badge-red"],
    in_progress:      ["Тест в процессе",       "badge-yellow"],
    pending_approval: ["Ожидает апрув",         "badge-blue"],
    approved:         ["Доступ открыт",         "badge-green"],
    rejected:         ["Отклонён",              "badge-red"],
  };
  const [label, cls] = map[status] || [status, "badge-gray"];
  return <span className={`badge ${cls}`}>{label}</span>;
}

export default function TestScreen() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data: status, isLoading } = useQuery({
    queryKey: ["testStatus"],
    queryFn: getTestStatus,
    refetchInterval: (q) =>
      q.state.data?.status === "pending_approval" ? 10000 : false,
  });

  const startMutation = useMutation({
    mutationFn: startTest,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["testStatus"] });
      navigate("/test/session");
    },
  });

  if (isLoading) return <div className="page">Загрузка...</div>;

  const s = status?.status;

  return (
    <div className="page">
      <div className="card" style={{ maxWidth: 560, margin: "40px auto", textAlign: "center" }}>
        <div style={{ fontSize: 48, marginBottom: 16 }}>🦺</div>
        <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 8 }}>
          Ежедневный допуск по ТБ
        </h1>
        <p style={{ color: "#64748b", marginBottom: 20, fontSize: 14 }}>
          Для получения нарядов ВФМ необходимо пройти тест по технике безопасности и получить апрув инженера.
        </p>

        <div style={{ marginBottom: 24 }}>
          {status && statusBadge(status.status)}
        </div>

        {s === "locked" || s === "rejected" ? (
          <button
            className="btn-primary"
            style={{ fontSize: 16, padding: "12px 36px" }}
            onClick={() => startMutation.mutate()}
            disabled={startMutation.isPending}
          >
            {startMutation.isPending ? "Запуск..." : "Начать тест"}
          </button>
        ) : s === "in_progress" ? (
          <button
            className="btn-primary"
            style={{ fontSize: 16, padding: "12px 36px" }}
            onClick={() => navigate("/test/session")}
          >
            Продолжить тест
          </button>
        ) : s === "pending_approval" ? (
          <div>
            {status?.score_pct !== null && (
              <p style={{ fontSize: 18, fontWeight: 700, color: "#2563eb", marginBottom: 8 }}>
                Результат: {status?.score_pct}%
              </p>
            )}
            <p style={{ color: "#64748b", fontSize: 14 }}>
              Ожидайте подтверждения инженера...
            </p>
          </div>
        ) : s === "approved" ? (
          <div>
            <p style={{ fontSize: 18, fontWeight: 700, color: "#16a34a", marginBottom: 16 }}>
              Доступ открыт! Результат: {status?.score_pct}%
            </p>
            <div style={{ display: "flex", gap: 12, justifyContent: "center" }}>
              <button className="btn-primary" onClick={() => navigate("/wfm")}>
                Открыть наряды ВФМ
              </button>
              <button className="btn-outline" onClick={() => navigate("/profile")}>
                Мои наряды-допуска
              </button>
            </div>
          </div>
        ) : null}

        {startMutation.isError && (
          <p className="error-msg" style={{ marginTop: 12 }}>
            {(startMutation.error as any)?.response?.data?.detail || "Ошибка запуска теста"}
          </p>
        )}
      </div>
    </div>
  );
}
