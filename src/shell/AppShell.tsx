import { Outlet, Route, Routes, Navigate } from "react-router-dom";
import { BottomNav } from "../components/navigation/BottomNav";
import ProtectedRoute from "../components/layout/ProtectedRoute";
import DashboardPage from "../views/DashboardPage";
import InterviewPage from "../views/InterviewPage";
import PreparationPage from "../views/PreparationPage";
import FeedbackPage from "../views/FeedbackPage";
import { ProgressPage } from "../views/ProgressPage";
import SettingsPage from "../views/SettingsPage";
import QuestionsPage from "../views/QuestionsPage";
import LoginPage from "../views/LoginPage";
import RegisterPage from "../views/RegisterPage";
import ForgotPasswordPage from "../views/ForgotPasswordPage";
import ResetPasswordPage from "../views/ResetPasswordPage";
import { usePageTracking } from "../hooks/usePageTracking";

function ShellLayout() {
  usePageTracking();
  
  return (
    <div className="flex min-h-screen flex-col bg-background">
      <header className="sticky top-0 z-30 border-b border-border bg-background/95 px-4 py-3 backdrop-blur">
        <div className="mx-auto flex max-w-4xl items-center justify-between">
          <span className="text-sm font-semibold tracking-tight">
            CareerSwiftr Interview Simulator
          </span>
        </div>
      </header>
      <main className="mx-auto flex w-full max-w-4xl flex-1 px-4 pb-16 pt-4">
        <Outlet />
      </main>
      <BottomNav />
    </div>
  );
}

export function AppShell() {
  return (
    <Routes>
      <Route element={<ShellLayout />}>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/forgot-password" element={<ForgotPasswordPage />} />
        <Route path="/reset-password" element={<ResetPasswordPage />} />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <DashboardPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/interview/:id"
          element={
            <ProtectedRoute>
              <InterviewPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/preparation/:id"
          element={
            <ProtectedRoute>
              <PreparationPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/practice"
          element={
            <ProtectedRoute>
              <QuestionsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/progress"
          element={
            <ProtectedRoute>
              <ProgressPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/feedback/:id"
          element={
            <ProtectedRoute>
              <FeedbackPage />
            </ProtectedRoute>
          }
        />
        {/* Alias route for backwards compatibility */}
        <Route
          path="/interview/:id/feedback"
          element={
            <ProtectedRoute>
              <FeedbackPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/settings"
          element={
            <ProtectedRoute>
              <SettingsPage />
            </ProtectedRoute>
          }
        />
      </Route>
    </Routes>
  );
}
