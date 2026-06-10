import { useEffect } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getMe } from "./api";
import { useAuthStore } from "./store/authStore";
import Layout from "./components/Layout";
import ProtectedRoute from "./components/ProtectedRoute";

import TestScreen from "./pages/installer/TestScreen";
import TestSession from "./pages/installer/TestSession";
import WFMScreen from "./pages/installer/WFMScreen";
import InstallerProfile from "./pages/installer/InstallerProfile";

import ApprovalQueue from "./pages/engineer/ApprovalQueue";
import ApprovalHistory from "./pages/engineer/ApprovalHistory";
import EngineerProfile from "./pages/engineer/EngineerProfile";
import QuestionBank from "./pages/engineer/questions/QuestionBank";
import QuestionForm from "./pages/engineer/questions/QuestionForm";

export default function App() {
  const setUser = useAuthStore((s) => s.setUser);
  const user = useAuthStore((s) => s.user);

  const { data } = useQuery({ queryKey: ["me"], queryFn: getMe });
  useEffect(() => { if (data) setUser(data); }, [data, setUser]);

  if (!user) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100vh" }}>
        Загрузка профиля...
      </div>
    );
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={
            user.role === "installer"
              ? <Navigate to="/test" replace />
              : <Navigate to="/approvals" replace />
          } />

          {/* Installer routes */}
          <Route path="/test" element={<ProtectedRoute role="installer"><TestScreen /></ProtectedRoute>} />
          <Route path="/test/session" element={<ProtectedRoute role="installer"><TestSession /></ProtectedRoute>} />
          <Route path="/wfm" element={<ProtectedRoute role="installer"><WFMScreen /></ProtectedRoute>} />
          <Route path="/profile" element={<ProtectedRoute role="installer"><InstallerProfile /></ProtectedRoute>} />

          {/* Engineer routes */}
          <Route path="/approvals" element={<ProtectedRoute role="engineer"><ApprovalQueue /></ProtectedRoute>} />
          <Route path="/approvals/history" element={<ProtectedRoute role="engineer"><ApprovalHistory /></ProtectedRoute>} />
          <Route path="/questions" element={<ProtectedRoute role="engineer"><QuestionBank /></ProtectedRoute>} />
          <Route path="/questions/new" element={<ProtectedRoute role="engineer"><QuestionForm /></ProtectedRoute>} />
          <Route path="/questions/:id/edit" element={<ProtectedRoute role="engineer"><QuestionForm /></ProtectedRoute>} />
          <Route path="/eng-profile" element={<ProtectedRoute role="engineer"><EngineerProfile /></ProtectedRoute>} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
