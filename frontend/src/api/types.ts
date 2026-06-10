export interface User {
  id: string;
  keycloak_id: string;
  employee_id: number | null;
  full_name: string;
  role: "installer" | "engineer";
  created_at: string;
}

export interface Question {
  id: string;
  text: string;
  options: string[];
}

export interface QuestionAdmin {
  id: string;
  text: string;
  options: string[];
  correct: number;
  is_active: boolean;
  created_by: string | null;
  updated_by: string | null;
  created_at: string;
  updated_at: string;
}

export interface TestStartResponse {
  session_id: string;
  started_at: string;
  expires_at: string;
  questions: Question[];
}

export interface SubmitResponse {
  session_id: string;
  status: string;
  score_pct: number;
  correct_cnt: number;
  total_cnt: number;
  duration_sec: number;
  passed: boolean;
}

export interface TestStatus {
  date: string;
  status: "locked" | "in_progress" | "pending_approval" | "approved" | "rejected";
  session_id: string | null;
  score_pct: number | null;
  permit_id: string | null;
}

export interface InstallerInfo {
  id: string;
  employee_id: number | null;
  full_name: string;
}

export interface SessionInfo {
  id: string;
  score_pct: number;
  correct_cnt: number;
  total_cnt: number;
  duration_sec: number;
  submitted_at: string;
}

export interface PendingApproval {
  daily_access_id: string;
  installer: InstallerInfo;
  session: SessionInfo;
}

export interface HistoryItem {
  daily_access_id: string;
  installer_full_name: string;
  status: string;
  score_pct: number | null;
  decided_at: string | null;
  permit_id: string | null;
}

export interface Permit {
  permit_id: string;
  permit_date: string;
  valid_until: string;
  generated_at: string;
  payload: Record<string, unknown>;
}
