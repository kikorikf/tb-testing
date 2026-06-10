import { useQuery } from "@tanstack/react-query";
import { getWfmShifts } from "../../api";

function formatTime(iso: string) {
  return new Date(iso).toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit" });
}

export default function WFMScreen() {
  const { data: shifts, isLoading, isError, error } = useQuery({
    queryKey: ["wfmShifts"],
    queryFn: () => getWfmShifts(),
  });

  if (isLoading) return <div className="page">Загрузка нарядов...</div>;

  if (isError) {
    const detail = (error as any)?.response?.data?.detail || "";
    if (detail.includes("approved") || (error as any)?.response?.status === 403) {
      return (
        <div className="page">
          <div className="card" style={{ maxWidth: 480, margin: "40px auto", textAlign: "center" }}>
            <div style={{ fontSize: 48, marginBottom: 12 }}>🔒</div>
            <h2 style={{ marginBottom: 8 }}>Доступ заблокирован</h2>
            <p style={{ color: "#64748b" }}>Пройдите тест по ТБ и получите апрув инженера.</p>
          </div>
        </div>
      );
    }
    return <div className="page"><p className="error-msg">Ошибка загрузки нарядов</p></div>;
  }

  return (
    <div className="page">
      <h1 className="page-title">Наряды ВФМ</h1>
      {!shifts || (shifts as any[]).length === 0 ? (
        <div className="card" style={{ textAlign: "center", color: "#64748b" }}>
          Нарядов на сегодня нет.
        </div>
      ) : (
        <div className="card" style={{ padding: 0, overflow: "hidden" }}>
          <table className="table">
            <thead>
              <tr>
                <th>Наряд</th>
                <th>Объект</th>
                <th>Тип</th>
                <th>Начало</th>
                <th>Конец</th>
              </tr>
            </thead>
            <tbody>
              {(shifts as any[]).map((s: any) => (
                <tr key={s.shiftId}>
                  <td>{s.shiftId}</td>
                  <td>{s.location}</td>
                  <td>{s.type}</td>
                  <td>{formatTime(s.startTime)}</td>
                  <td>{formatTime(s.endTime)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
