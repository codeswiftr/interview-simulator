import { lazy, Suspense } from 'react';
import { Routes, Route } from 'react-router-dom';
import Header from './components/layout/Header';
import Footer from './components/layout/Footer';
import { BottomNav } from './components/layout/BottomNav';
import ProtectedRoute from './components/layout/ProtectedRoute';
import { ErrorBoundary } from './components/ErrorBoundary';
import { ToastProvider } from './hooks/useToast';
import { ThemeProvider } from './contexts/ThemeContext';
import { usePageTracking } from './hooks/usePageTracking';
import { OfflineIndicator, InstallPrompt } from './components/pwa';
import { Loader2 } from 'lucide-react';

// Eager load lightweight pages (core auth, home)
import HomePage from './pages/HomePage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import ForgotPasswordPage from './pages/ForgotPasswordPage';
import ResetPasswordPage from './pages/ResetPasswordPage';
import AffiliatePage from './pages/AffiliatePage';
import VerifyEmailPage from './pages/VerifyEmailPage';
import PricingPage from './pages/PricingPage';
import ContentPage from './pages/ContentPage';
import FAQPage from './pages/FAQPage';
import ComparePage from './pages/ComparePage';
import PrivacyPage from './pages/PrivacyPage';
import TermsPage from './pages/TermsPage';

// Lazy load heavier pages for code splitting
const DashboardPage = lazy(() => import('./pages/DashboardPage'));
const QuestionsPage = lazy(() => import('./pages/QuestionsPage'));
const InterviewPage = lazy(() => import('./pages/InterviewPage'));
const FeedbackPage = lazy(() => import('./pages/FeedbackPage'));
const SettingsPage = lazy(() => import('./pages/SettingsPage'));
const PreparationPage = lazy(() => import('./pages/PreparationPage'));
const ProgressPage = lazy(() => import('./pages/ProgressPage'));
const AnalyticsDashboardPage = lazy(() => import('./pages/AnalyticsDashboardPage'));
const SharedInterviewPage = lazy(() => import('./pages/SharedInterviewPage'));
const BlogListPage = lazy(() => import('./pages/BlogListPage'));
const BlogPostPage = lazy(() => import('./pages/BlogPostPage'));
const TeamDashboardPage = lazy(() => import('./pages/TeamDashboardPage'));
const TeamSettingsPage = lazy(() => import('./pages/TeamSettingsPage'));
const AcceptInvitationPage = lazy(() => import('./pages/AcceptInvitationPage'));

// Dev-only preview page (lazy loaded, only in development)
const DevPreviewPage = lazy(() => import('./pages/DevPreviewPage'));

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
          <OfflineIndicator />
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
                  <Route path="/verify-email" element={<VerifyEmailPage />} />
                  <Route path="/pricing" element={<PricingPage />} />
                  <Route path="/faq" element={<FAQPage />} />
                  <Route path="/compare" element={<ComparePage />} />
                  <Route path="/affiliates" element={<AffiliatePage />} />
                  <Route path="/content" element={<ContentPage />} />
                  <Route path="/privacy" element={<PrivacyPage />} />
                  <Route path="/terms" element={<TermsPage />} />
                  <Route path="/blog" element={<BlogListPage />} />
                  <Route path="/blog/:slug" element={<BlogPostPage />} />
                  {/* Public shared interview view - no auth required */}
                  <Route path="/shared/:token" element={<SharedInterviewPage />} />
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
                    path="/analytics"
                    element={
                      <ProtectedRoute>
                        <AnalyticsDashboardPage />
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
                  {/* Public join invitation page */}
                  <Route path="/join/:token" element={<AcceptInvitationPage />} />
                  <Route
                    path="/team"
                    element={
                      <ProtectedRoute>
                        <TeamDashboardPage />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="/team/settings"
                    element={
                      <ProtectedRoute>
                        <TeamSettingsPage />
                      </ProtectedRoute>
                    }
                  />
                  {/* Dev-only preview route */}
                  {import.meta.env.DEV && (
                    <Route path="/dev-preview" element={<DevPreviewPage />} />
                  )}
                  {/* 404 catch-all */}
                  <Route path="*" element={
                    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4">
                      <h1 className="text-6xl font-bold text-electric-blue mb-4">404</h1>
                      <p className="text-xl text-text-secondary mb-6">Page not found</p>
                      <a href="/" className="px-6 py-3 bg-electric-blue text-white rounded-lg hover:opacity-90 transition-opacity">
                        Back to Home
                      </a>
                    </div>
                  } />
                </Routes>
              </Suspense>
            </main>
            <Footer />
            <BottomNav />
            <InstallPrompt />
          </div>
        </ToastProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;
