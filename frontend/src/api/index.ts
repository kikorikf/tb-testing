import api from "./client";
import type {
  HistoryItem, Permit, PendingApproval, QuestionAdmin,
  SubmitResponse, TestStartResponse, TestStatus, User,
} from "./types";

export const getMe = () => api.get<User>("/me").then((r) => r.data);

export const getTestStatus = () => api.get<TestStatus>("/test/status").then((r) => r.data);
export const startTest = () => api.post<TestStartResponse>("/test/start").then((r) => r.data);
export const submitTest = (session_id: string, answers: Record<string, number>) =>
  api.post<SubmitResponse>("/test/submit", { session_id, answers }).then((r) => r.data);

export const getPendingApprovals = () =>
  api.get<PendingApproval[]>("/approvals/pending").then((r) => r.data);
export const approveAccess = (id: string) =>
  api.post(`/approvals/${id}/approve`).then((r) => r.data);
export const rejectAccess = (id: string, reason?: string) =>
  api.post(`/approvals/${id}/reject`, { reason }).then((r) => r.data);
export const getApprovalHistory = () =>
  api.get<HistoryItem[]>("/approvals/history").then((r) => r.data);

export const getMyPermits = () => api.get<Permit[]>("/permits/my").then((r) => r.data);
export const getPermit = (id: string) => api.get<Permit>(`/permits/my/${id}`).then((r) => r.data);

export const getQuestions = (is_active?: boolean) =>
  api
    .get<QuestionAdmin[]>("/questions", { params: is_active !== undefined ? { is_active } : {} })
    .then((r) => r.data);
export const createQuestion = (data: {
  text: string; options: string[]; correct: number; is_active: boolean;
}) => api.post<QuestionAdmin>("/questions", data).then((r) => r.data);
export const updateQuestion = (id: string, data: Partial<{
  text: string; options: string[]; correct: number; is_active: boolean;
}>) => api.patch<QuestionAdmin>(`/questions/${id}`, data).then((r) => r.data);
export const deactivateQuestion = (id: string) =>
  api.delete(`/questions/${id}`).then((r) => r.data);

export const getWfmShifts = (shift_date?: string) =>
  api.get("/wfm/shifts", { params: shift_date ? { shift_date } : {} }).then((r) => r.data);
