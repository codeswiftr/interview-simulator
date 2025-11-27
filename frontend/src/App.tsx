import { Routes, Route } from 'react-router-dom';
import Header from './components/layout/Header';
import ProtectedRoute from './components/layout/ProtectedRoute';
import HomePage from './pages/HomePage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import InterviewPage from './pages/InterviewPage';
import FeedbackPage from './pages/FeedbackPage';

function App() {
  return (
    <div className="min-h-screen bg-surface-primary">
      <Header />
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
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
          path="/interview/:id/feedback"
          element={
            <ProtectedRoute>
              <FeedbackPage />
            </ProtectedRoute>
          }
        />
      </Routes>
    </div>
  );
}

export default App;
