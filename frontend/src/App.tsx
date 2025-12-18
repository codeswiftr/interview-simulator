import { lazy, Suspense } from 'react';
import { Routes, Route } from 'react-router-dom';
import Header from './components/layout/Header';
import { BottomNav } from './components/layout/BottomNav';
import ProtectedRoute from './components/layout/ProtectedRoute';
import { ErrorBoundary } from './components/ErrorBoundary';
import { ToastProvider } from './hooks/useToast';
import { ThemeProvider } from './contexts/ThemeContext';
import { usePageTracking } from './hooks/usePageTracking';
import { Loader2 } from 'lucide-react';

// Eager load lightweight pages (core auth, home)
import HomePage from './pages/HomePage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import ForgotPasswordPage from './pages/ForgotPasswordPage';
import ResetPasswordPage from './pages/ResetPasswordPage';

// Lazy load heavier pages for code splitting
const DashboardPage = lazy(() => import('./pages/DashboardPage'));
const QuestionsPage = lazy(() => import('./pages/QuestionsPage'));
const InterviewPage = lazy(() => import('./pages/InterviewPage'));
const FeedbackPage = lazy(() => import('./pages/FeedbackPage'));
const SettingsPage = lazy(() => import('./pages/SettingsPage'));
const PreparationPage = lazy(() => import('./pages/PreparationPage'));
const ProgressPage = lazy(() => import('./pages/ProgressPage'));

// Loading fallback component
const PageLoadingFallback = () => (
  <div className="flex items-center justify-center min-h-[60vh]">
    <div className="text-center">
      <Loader2 size={32} className="animate-spin text-electric-blue mx-auto mb-4" />
      <p className="text-text-secondary">Loading...</p>
    </div>
  </div>
);

function App() {
  // Track page views on route changes
  usePageTracking();

  return (
    <ErrorBoundary>
      <ThemeProvider>
        <ToastProvider>
          <div className="min-h-screen bg-surface-primary">
            <Header />
            <main id="main-content" className="pb-16 md:pb-0">
              <Suspense fallback={<PageLoadingFallback />}>
                <Routes>
                  <Route path="/" element={<HomePage />} />
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
                    path="/questions"
                    element={
                      <ProtectedRoute>
                        <QuestionsPage />
                      </ProtectedRoute>
                    }
                  />
                  {/* /practice route - same as /questions, for mobile nav consistency */}
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
                    path="/interview/:id"
                    element={
                      <ProtectedRoute>
                        <InterviewPage />
                      </ProtectedRoute>
                    }
                  />
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
                  <Route
                    path="/preparation/:id"
                    element={
                      <ProtectedRoute>
                        <PreparationPage />
                      </ProtectedRoute>
                    }
                  />
                </Routes>
              </Suspense>
            </main>
            <BottomNav />
          </div>
        </ToastProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;
