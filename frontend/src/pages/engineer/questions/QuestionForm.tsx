import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate, useParams } from "react-router-dom";
import { createQuestion, updateQuestion, getQuestions } from "../../../api";

interface FormState {
  text: string;
  options: string[];
  correct: number;
  is_active: boolean;
}

export default function QuestionForm() {
  const { id } = useParams<{ id?: string }>();
  const isEdit = Boolean(id);
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [form, setForm] = useState<FormState>({
    text: "",
    options: ["", "", "", ""],
    correct: 0,
    is_active: true,
  });
  const [error, setError] = useState("");

  const { data: allQuestions } = useQuery({
    queryKey: ["questions"],
    queryFn: () => getQuestions(),
    enabled: isEdit,
  });

  useEffect(() => {
    if (isEdit && allQuestions) {
      const q = allQuestions.find((q: any) => q.id === id);
      if (q) {
        setForm({ text: q.text, options: [...q.options], correct: q.correct, is_active: q.is_active });
      }
    }
  }, [allQuestions, id, isEdit]);

  const createMutation = useMutation({
    mutationFn: (data: FormState) => createQuestion(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["questions"] });
      navigate("/questions");
    },
    onError: (e: any) => setError(e?.response?.data?.detail || "Ошибка сохранения"),
  });

  const updateMutation = useMutation({
    mutationFn: (data: Partial<FormState>) => updateQuestion(id!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["questions"] });
      navigate("/questions");
    },
    onError: (e: any) => setError(e?.response?.data?.detail || "Ошибка сохранения"),
  });

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    const filtered = form.options.filter((o) => o.trim());
    if (filtered.length < 2) { setError("Минимум 2 варианта ответа"); return; }
    if (form.correct >= filtered.length) { setError("Выберите правильный вариант"); return; }
    const payload = { ...form, options: filtered };
    if (isEdit) updateMutation.mutate(payload);
    else createMutation.mutate(payload);
  }

  const isPending = createMutation.isPending || updateMutation.isPending;

  return (
    <div className="page">
      <h1 className="page-title">{isEdit ? "Редактировать вопрос" : "Новый вопрос"}</h1>
      <div className="card" style={{ maxWidth: 640 }}>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Текст вопроса *</label>
            <textarea
              rows={3}
              value={form.text}
              onChange={(e) => setForm((f) => ({ ...f, text: e.target.value }))}
              placeholder="Введите текст вопроса..."
              required
            />
          </div>

          <div className="form-group">
            <label>Варианты ответов (2–6) *</label>
            {form.options.map((opt, i) => (
              <div key={i} style={{ display: "flex", gap: 8, marginBottom: 8, alignItems: "center" }}>
                <input
                  type="radio"
                  name="correct"
                  checked={form.correct === i}
                  onChange={() => setForm((f) => ({ ...f, correct: i }))}
                  title="Правильный ответ"
                  style={{ width: "auto", flexShrink: 0 }}
                />
                <input
                  value={opt}
                  onChange={(e) => {
                    const opts = [...form.options];
                    opts[i] = e.target.value;
                    setForm((f) => ({ ...f, options: opts }));
                  }}
                  placeholder={`Вариант ${i + 1}`}
                />
                {form.options.length > 2 && (
                  <button
                    type="button"
                    className="btn-danger"
                    style={{ flexShrink: 0, padding: "6px 10px" }}
                    onClick={() => {
                      const opts = form.options.filter((_, idx) => idx !== i);
                      const newCorrect = form.correct >= opts.length ? opts.length - 1 : form.correct;
                      setForm((f) => ({ ...f, options: opts, correct: newCorrect }));
                    }}
                  >
                    ✕
                  </button>
                )}
              </div>
            ))}
            <p style={{ fontSize: 12, color: "#94a3b8", marginBottom: 8 }}>
              ○ — отметьте правильный вариант
            </p>
            {form.options.length < 6 && (
              <button
                type="button"
                className="btn-outline"
                style={{ fontSize: 13, padding: "6px 14px" }}
                onClick={() => setForm((f) => ({ ...f, options: [...f.options, ""] }))}
              >
                + Добавить вариант
              </button>
            )}
          </div>

          <div className="form-group" style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <input
              type="checkbox"
              id="is_active"
              checked={form.is_active}
              onChange={(e) => setForm((f) => ({ ...f, is_active: e.target.checked }))}
              style={{ width: "auto" }}
            />
            <label htmlFor="is_active" style={{ margin: 0 }}>Активен (включён в тест)</label>
          </div>

          {error && <p className="error-msg" style={{ marginBottom: 12 }}>{error}</p>}

          <div style={{ display: "flex", gap: 12 }}>
            <button type="submit" className="btn-primary" disabled={isPending}>
              {isPending ? "Сохранение..." : isEdit ? "Сохранить" : "Создать"}
            </button>
            <button type="button" className="btn-outline" onClick={() => navigate("/questions")}>
              Отмена
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
