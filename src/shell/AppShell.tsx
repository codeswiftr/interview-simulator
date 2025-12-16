import { Outlet, Route, Routes, Navigate } from "react-router-dom";
import { BottomNav } from "../components/navigation/BottomNav";
import { DashboardPage } from "../views/DashboardPage";
import { InterviewPage } from "../views/InterviewPage";
import { PreparationPage } from "../views/PreparationPage";
import { FeedbackPage } from "../views/FeedbackPage";
import { ProgressPage } from "../views/ProgressPage";
import { SettingsPage } from "../views/SettingsPage";
import { AuthPage } from "../views/AuthPage";

function ShellLayout() {
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
        <Route path="/auth" element={<AuthPage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/interview/:id" element={<InterviewPage />} />
        <Route path="/practice" element={<PreparationPage />} />
        <Route path="/progress" element={<ProgressPage />} />
        <Route path="/feedback/:id" element={<FeedbackPage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Route>
    </Routes>
  );
}
