import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { deactivateQuestion, getQuestions } from "../../../api";
import type { QuestionAdmin } from "../../../api/types";

export default function QuestionBank() {
  const queryClient = useQueryClient();

  const { data: questions, isLoading } = useQuery({
    queryKey: ["questions"],
    queryFn: () => getQuestions(),
  });

  const deactivateMutation = useMutation({
    mutationFn: (id: string) => deactivateQuestion(id),
    onSuccess: (data: any) => {
      queryClient.invalidateQueries({ queryKey: ["questions"] });
      if (data.warning) alert(data.warning);
    },
  });

  const active = questions?.filter((q: QuestionAdmin) => q.is_active).length ?? 0;

  if (isLoading) return <div className="page">Загрузка...</div>;

  return (
    <div className="page">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700 }}>
          Банк вопросов
          <span className="badge badge-blue" style={{ marginLeft: 10, fontSize: 13 }}>
            {active} активных
          </span>
          {active < 5 && (
            <span className="badge badge-red" style={{ marginLeft: 8, fontSize: 13 }}>
              ⚠ Мало вопросов
            </span>
          )}
        </h1>
        <Link to="/questions/new">
          <button className="btn-primary">+ Добавить вопрос</button>
        </Link>
      </div>

      {!questions || questions.length === 0 ? (
        <div className="card" style={{ textAlign: "center", color: "#64748b" }}>
          Вопросов нет. Добавьте первый.
        </div>
      ) : (
        <div className="card" style={{ padding: 0, overflow: "hidden" }}>
          <table className="table">
            <thead>
              <tr>
                <th style={{ width: "50%" }}>Вопрос</th>
                <th>Вариантов</th>
                <th>Статус</th>
                <th>Изменён</th>
                <th>Действия</th>
              </tr>
            </thead>
            <tbody>
              {questions.map((q: QuestionAdmin) => (
                <tr key={q.id}>
                  <td style={{ maxWidth: 400 }}>
                    <div style={{ whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis", maxWidth: 380 }}>
                      {q.text}
                    </div>
                  </td>
                  <td>{q.options.length}</td>
                  <td>
                    <span className={`badge ${q.is_active ? "badge-green" : "badge-gray"}`}>
                      {q.is_active ? "Активен" : "Неактивен"}
                    </span>
                  </td>
                  <td style={{ fontSize: 12, color: "#94a3b8" }}>
                    {new Date(q.updated_at).toLocaleDateString("ru-RU")}
                  </td>
                  <td>
                    <div style={{ display: "flex", gap: 8 }}>
                      <Link to={`/questions/${q.id}/edit`}>
                        <button className="btn-outline" style={{ fontSize: 12, padding: "5px 12px" }}>
                          Изменить
                        </button>
                      </Link>
                      {q.is_active && (
                        <button
                          className="btn-danger"
                          style={{ fontSize: 12, padding: "5px 12px" }}
                          onClick={() => {
                            if (confirm(`Деактивировать вопрос?\n\n"${q.text}"`)) {
                              deactivateMutation.mutate(q.id);
                            }
                          }}
                          disabled={deactivateMutation.isPending}
                        >
                          Деакт.
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
