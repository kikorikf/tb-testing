import { useQuery } from "@tanstack/react-query";
import { getApprovalHistory } from "../../api";
import type { HistoryItem } from "../../api/types";

export default function ApprovalHistory() {
  const { data: items, isLoading } = useQuery({
    queryKey: ["approvalHistory"],
    queryFn: getApprovalHistory,
  });

  if (isLoading) return <div className="page">Загрузка...</div>;

  return (
    <div className="page">
      <h1 className="page-title">История апрувов (сегодня)</h1>
      {!items || items.length === 0 ? (
        <div className="card" style={{ textAlign: "center", color: "#64748b" }}>Истории нет.</div>
      ) : (
        <div className="card" style={{ padding: 0, overflow: "hidden" }}>
          <table className="table">
            <thead>
              <tr>
                <th>ФИО инсталлятора</th>
                <th>Статус</th>
                <th>Результат</th>
                <th>Решено в</th>
                <th>Наряд №</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item: HistoryItem) => (
                <tr key={item.daily_access_id}>
                  <td>{item.installer_full_name}</td>
                  <td>
                    <span className={`badge ${item.status === "approved" ? "badge-green" : "badge-red"}`}>
                      {item.status === "approved" ? "Подтверждён" : "Отклонён"}
                    </span>
                  </td>
                  <td>{item.score_pct !== null ? `${item.score_pct}%` : "—"}</td>
                  <td>
                    {item.decided_at
                      ? new Date(item.decided_at).toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit" })
                      : "—"}
                  </td>
                  <td>{item.permit_id ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
