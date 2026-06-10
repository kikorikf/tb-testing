import { useEffect, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { startTest, submitTest } from "../../api";
import type { Question, TestStartResponse } from "../../api/types";

function formatTime(sec: number) {
  const m = Math.floor(sec / 60).toString().padStart(2, "0");
  const s = (sec % 60).toString().padStart(2, "0");
  return `${m}:${s}`;
}

export default function TestSession() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [sessionData, setSessionData] = useState<TestStartResponse | null>(null);
  const [current, setCurrent] = useState(0);
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [timeLeft, setTimeLeft] = useState(0);
  const [result, setResult] = useState<null | { passed: boolean; score_pct: number; correct_cnt: number; total_cnt: number }>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const startMutation = useMutation({
    mutationFn: startTest,
    onSuccess: (data) => {
      setSessionData(data);
      const expiresAt = new Date(data.expires_at).getTime();
      const now = Date.now();
      setTimeLeft(Math.max(0, Math.floor((expiresAt - now) / 1000)));
    },
  });

  const submitMutation = useMutation({
    mutationFn: ({ session_id, ans }: { session_id: string; ans: Record<string, number> }) =>
      submitTest(session_id, ans),
    onSuccess: (data) => {
      clearInterval(timerRef.current!);
      queryClient.invalidateQueries({ queryKey: ["testStatus"] });
      setResult({ passed: data.passed, score_pct: data.score_pct, correct_cnt: data.correct_cnt, total_cnt: data.total_cnt });
    },
  });

  useEffect(() => {
    startMutation.mutate();
  }, []);

  useEffect(() => {
    if (timeLeft <= 0 || !sessionData) return;
    timerRef.current = setInterval(() => {
      setTimeLeft((t) => {
        if (t <= 1) {
          clearInterval(timerRef.current!);
          submitMutation.mutate({ session_id: sessionData.session_id, ans: answers });
          return 0;
        }
        return t - 1;
      });
    }, 1000);
    return () => clearInterval(timerRef.current!);
  }, [sessionData]);

  if (startMutation.isPending) {
    return <div className="page" style={{ textAlign: "center", paddingTop: 80 }}>Загрузка теста...</div>;
  }

  if (startMutation.isError) {
    const detail = (startMutation.error as any)?.response?.data?.detail || "";
    return (
      <div className="page">
        <div className="card" style={{ maxWidth: 480, margin: "40px auto", textAlign: "center" }}>
          <p className="error-msg" style={{ fontSize: 16 }}>
            {detail.includes("approved") ? "Вы уже получили допуск сегодня." :
             detail.includes("pending") ? "Ваш результат уже отправлен инженеру." :
             detail.includes("questions") ? "Недостаточно активных вопросов. Обратитесь к инженеру." :
             "Ошибка запуска теста. " + detail}
          </p>
          <button className="btn-outline" style={{ marginTop: 20 }} onClick={() => navigate("/test")}>
            Назад
          </button>
        </div>
      </div>
    );
  }

  if (result) {
    return (
      <div className="page">
        <div className="card" style={{ maxWidth: 480, margin: "40px auto", textAlign: "center" }}>
          <div style={{ fontSize: 56, marginBottom: 12 }}>{result.passed ? "✅" : "❌"}</div>
          <h2 style={{ fontSize: 22, marginBottom: 8 }}>
            {result.passed ? "Тест пройден!" : "Тест не пройден"}
          </h2>
          <p style={{ fontSize: 32, fontWeight: 700, color: result.passed ? "#16a34a" : "#dc2626", marginBottom: 8 }}>
            {result.score_pct}%
          </p>
          <p style={{ color: "#64748b", marginBottom: 24 }}>
            Верных ответов: {result.correct_cnt} из {result.total_cnt}
          </p>
          {result.passed ? (
            <p style={{ color: "#2563eb" }}>Ваш результат отправлен инженеру. Ожидайте апрув.</p>
          ) : (
            <button className="btn-primary" onClick={() => navigate("/test")}>
              Пройти ещё раз
            </button>
          )}
        </div>
      </div>
    );
  }

  if (!sessionData) return null;

  const questions = sessionData.questions;
  const q: Question = questions[current];
  const progress = Math.round(((current + 1) / questions.length) * 100);
  const timerColor = timeLeft < 300 ? "#dc2626" : timeLeft < 600 ? "#f59e0b" : "#16a34a";

  return (
    <div className="page">
      <div className="card" style={{ maxWidth: 680, margin: "24px auto" }}>
        {/* Header */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
          <span style={{ color: "#64748b", fontSize: 14 }}>
            Вопрос {current + 1} из {questions.length}
          </span>
          <span style={{
            fontWeight: 700, fontSize: 20, color: timerColor,
            fontVariantNumeric: "tabular-nums",
          }}>
            ⏱ {formatTime(timeLeft)}
          </span>
        </div>

        {/* Progress bar */}
        <div style={{ height: 6, background: "#e2e8f0", borderRadius: 4, marginBottom: 24 }}>
          <div style={{ height: "100%", width: `${progress}%`, background: "#2563eb", borderRadius: 4, transition: "width .3s" }} />
        </div>

        {/* Question */}
        <p style={{ fontSize: 17, fontWeight: 600, marginBottom: 20, lineHeight: 1.5 }}>{q.text}</p>

        {/* Options */}
        <div style={{ display: "flex", flexDirection: "column", gap: 10, marginBottom: 28 }}>
          {q.options.map((opt, i) => {
            const selected = answers[q.id] === i;
            return (
              <button
                key={i}
                onClick={() => setAnswers((a) => ({ ...a, [q.id]: i }))}
                style={{
                  background: selected ? "#2563eb" : "#f8fafc",
                  color: selected ? "#fff" : "#1a1a2e",
                  border: `2px solid ${selected ? "#2563eb" : "#e2e8f0"}`,
                  borderRadius: 8,
                  padding: "12px 16px",
                  textAlign: "left",
                  fontWeight: selected ? 600 : 400,
                  fontSize: 15,
                }}
              >
                {opt}
              </button>
            );
          })}
        </div>

        {/* Navigation */}
        <div style={{ display: "flex", justifyContent: "space-between", gap: 12 }}>
          <button
            className="btn-outline"
            onClick={() => setCurrent((c) => c - 1)}
            disabled={current === 0}
          >
            ← Назад
          </button>

          {current < questions.length - 1 ? (
            <button
              className="btn-primary"
              onClick={() => setCurrent((c) => c + 1)}
            >
              Далее →
            </button>
          ) : (
            <button
              className="btn-success"
              onClick={() => submitMutation.mutate({ session_id: sessionData.session_id, ans: answers })}
              disabled={submitMutation.isPending}
            >
              {submitMutation.isPending ? "Отправка..." : "Сдать тест"}
            </button>
          )}
        </div>

        {/* Answered counter */}
        <p style={{ textAlign: "center", color: "#94a3b8", fontSize: 12, marginTop: 16 }}>
          Отвечено: {Object.keys(answers).length} / {questions.length}
        </p>
      </div>
    </div>
  );
}
