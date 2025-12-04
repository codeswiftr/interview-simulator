import { useState, useEffect, useMemo, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, AlertCircle, Lightbulb } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { useOnboarding } from '../hooks/useOnboarding';
import { interviewsAPI, userAPI } from '../lib/api';
import StatsOverview from '../components/dashboard/StatsOverview';
import ProgressChart from '../components/dashboard/ProgressChart';
import CategoryBreakdown from '../components/dashboard/CategoryBreakdown';
import InterviewCard from '../components/interview/InterviewCard';
import NewInterviewModal from '../components/interview/NewInterviewModal';
import UpgradeModal from '../components/subscription/UpgradeModal';
import WelcomeModal from '../components/onboarding/WelcomeModal';
import type { InterviewSession, CreateInterviewFormData } from '../types';
import type { AxiosError } from 'axios';

interface UserStats {
  total_sessions: number;
  completed_sessions: number;
  average_score: number | null;
  total_practice_time_seconds: number;
}

interface UserProgress {
  score_trend: Array<{ date: string; score: number; content_score: number; audio_score: number }>;
  recommended_practice_areas: string[];
  average_audio_score: number | null;
  average_content_score: number | null;
}

interface ReadinessScore {
  readiness_score: number | null;
  sessions_used: number;
  improvement_trend: number | null;
  message?: string;
}

export default function DashboardPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { shouldShowWelcome, markWelcomeSeen } = useOnboarding();
  const [sessions, setSessions] = useState<InterviewSession[]>([]);
  const [userStats, setUserStats] = useState<UserStats | null>(null);
  const [userProgress, setUserProgress] = useState<UserProgress | null>(null);
  const [readinessScore, setReadinessScore] = useState<ReadinessScore | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [showUpgradeModal, setShowUpgradeModal] = useState(false);
  const [showWelcomeModal, setShowWelcomeModal] = useState(false);

  // Show welcome modal for new users after data loads
  useEffect(() => {
    if (!isLoading && shouldShowWelcome && sessions.length === 0) {
      setShowWelcomeModal(true);
    }
  }, [isLoading, shouldShowWelcome, sessions.length]);

  const handleWelcomeClose = () => {
    markWelcomeSeen();
    setShowWelcomeModal(false);
  };

  const handleWelcomeStartInterview = () => {
    markWelcomeSeen();
    setShowWelcomeModal(false);
    setIsModalOpen(true);
  };

  const loadInterviews = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await interviewsAPI.getAll();
      setSessions(response.data);
    } catch (err) {
      const axiosError = err as AxiosError<{ message?: string }>;
      setError(axiosError.response?.data?.message || 'Failed to load interviews');
    } finally {
      setIsLoading(false);
    }
  }, []);

  const loadData = useCallback(async () => {
    await Promise.all([loadInterviews(), loadStats(), loadProgress(), loadReadinessScore()]);
  }, [loadInterviews]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const loadStats = async () => {
    try {
      const response = await userAPI.getStats();
      setUserStats(response.data);
    } catch (err) {
      // Silently fail - stats are nice to have
      console.warn('Failed to load user stats:', err);
    }
  };

  const loadProgress = async () => {
    try {
      const response = await userAPI.getProgress();
      setUserProgress(response.data);
    } catch (err) {
      // Silently fail - progress is nice to have
      console.warn('Failed to load user progress:', err);
    }
  };

  const loadReadinessScore = async () => {
    try {
      const response = await userAPI.getReadinessScore();
      setReadinessScore(response.data);
    } catch (err) {
      // Silently fail - readiness score is nice to have
      console.warn('Failed to load readiness score:', err);
    }
  };

  const handleCreateInterview = async (data: CreateInterviewFormData) => {
    try {
      const response = await interviewsAPI.create(data);
      const newSession = response.data;

      // Navigate to the interview session
      navigate(`/interview/${newSession.id}`);
    } catch (err) {
      const axiosError = err as AxiosError<{ message?: string }>;
      if (axiosError.response?.status === 402) {
        // Quota exceeded - show upgrade modal
        setShowUpgradeModal(true);
        setError('Free tier limit reached. Upgrade to Pro for unlimited interviews.');
      } else {
        setError(axiosError.response?.data?.message || 'Failed to create interview');
      }
    }
  };

  const handleSessionClick = (session: InterviewSession) => {
    navigate(`/interview/${session.id}`);
  };

  // Use API stats if available, fallback to calculated
  const stats = {
    totalInterviews: userStats?.total_sessions ?? sessions.length,
    completedInterviews: userStats?.completed_sessions ?? sessions.filter((s) => s.status === 'completed' || s.status === 'analyzed').length,
    averageScore: userStats?.average_score ?? (sessions
      .filter((s) => s.overall_score !== null && s.overall_score !== undefined)
      .reduce((acc, s) => acc + (s.overall_score || 0), 0) /
      Math.max(1, sessions.filter((s) => s.overall_score !== null).length)),
    inProgress: sessions.filter((s) => s.status === 'in_progress').length,
  };

  // Calculate category breakdown from sessions
  const categoryBreakdown = useMemo(() => {
    const breakdown: Record<string, { count: number; scores: number[] }> = {};

    sessions.forEach((session) => {
      const category = session.interview_type || 'mixed';
      if (!breakdown[category]) {
        breakdown[category] = { count: 0, scores: [] };
      }
      breakdown[category].count++;
      if (session.overall_score !== null && session.overall_score !== undefined) {
        breakdown[category].scores.push(session.overall_score);
      }
    });

    return Object.entries(breakdown).map(([category, data]) => ({
      category,
      count: data.count,
      averageScore: data.scores.length > 0
        ? data.scores.reduce((a, b) => a + b, 0) / data.scores.length
        : undefined,
    }));
  }, [sessions]);

  return (
    <div className="min-h-screen bg-surface-primary">
      <div className="container mx-auto px-6 py-8 max-w-7xl">
        {/* Header Section */}
        <div className="mb-8">
          <h1 className="heading-page mb-2">Welcome back{user?.full_name ? `, ${user.full_name}` : ''}!</h1>
          <p className="text-text-secondary">Track your progress and continue practicing your interview skills.</p>
        </div>

        {/* Stats Overview */}
        <div className="mb-8">
          <StatsOverview
            totalSessions={stats.totalInterviews}
            completedSessions={stats.completedInterviews}
            averageScore={stats.averageScore && stats.averageScore > 0 ? stats.averageScore : null}
            totalPracticeTimeSeconds={userStats?.total_practice_time_seconds ?? 0}
            readinessScore={readinessScore}
          />
        </div>

        {/* Progress Charts - Only show when user has sessions */}
        {sessions.length > 0 && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            <ProgressChart
              data={userProgress?.score_trend || []}
              height={220}
            />
            <CategoryBreakdown data={categoryBreakdown} />
          </div>
        )}

        {/* Progress Section - Practice Recommendations */}
        {userProgress && userProgress.recommended_practice_areas.length > 0 && (
          <div className="card p-6 mb-8">
            <div className="flex items-center gap-3 mb-4">
              <Lightbulb className="w-6 h-6 text-electric-blue" />
              <h2 className="heading-section">Focus Areas</h2>
            </div>
            <p className="body-default text-text-secondary mb-4">
              Based on your recent interviews, here are areas to focus on:
            </p>
            <div className="flex flex-wrap gap-2">
              {userProgress.recommended_practice_areas.map((area, idx) => (
                <span key={idx} className="badge badge-in-progress">
                  {area}
                </span>
              ))}
            </div>
            {userProgress.average_audio_score !== null && userProgress.average_content_score !== null && (
              <div className="mt-4 pt-4 border-t border-border-light">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-text-tertiary">Avg Content Score: </span>
                    <span className="font-medium">{Math.round(userProgress.average_content_score)}/100</span>
                  </div>
                  <div>
                    <span className="text-text-tertiary">Avg Audio Score: </span>
                    <span className="font-medium">{Math.round(userProgress.average_audio_score)}/100</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Onboarding Panel - Show for new users */}
        {!isLoading && sessions.length === 0 && (
          <div className="card p-8 mb-8 border-2 border-electric-blue bg-electric-blue/5">
            <h2 className="heading-section mb-4">Get Started</h2>
            <p className="body-default text-text-secondary mb-6">
              Complete these steps to start improving your interview skills:
            </p>
            <div className="space-y-4">
              <div className="flex items-start gap-4">
                <div className="w-8 h-8 rounded-full bg-electric-blue text-white flex items-center justify-center font-semibold flex-shrink-0">
                  1
                </div>
                <div>
                  <h3 className="heading-card mb-1">Create your first interview</h3>
                  <p className="body-small text-text-secondary">
                    Choose from behavioral, technical, or system design questions
                  </p>
                </div>
              </div>
              <div className="flex items-start gap-4">
                <div className="w-8 h-8 rounded-full bg-border-light text-text-tertiary flex items-center justify-center font-semibold flex-shrink-0">
                  2
                </div>
                <div>
                  <h3 className="heading-card mb-1">Complete one session</h3>
                  <p className="body-small text-text-secondary">
                    Record your answers and submit them for analysis
                  </p>
                </div>
              </div>
              <div className="flex items-start gap-4">
                <div className="w-8 h-8 rounded-full bg-border-light text-text-tertiary flex items-center justify-center font-semibold flex-shrink-0">
                  3
                </div>
                <div>
                  <h3 className="heading-card mb-1">Review AI feedback</h3>
                  <p className="body-small text-text-secondary">
                    Get detailed insights on your performance and areas to improve
                  </p>
                </div>
              </div>
            </div>
            <div className="mt-6">
              <button
                onClick={() => setIsModalOpen(true)}
                className="btn-primary inline-flex items-center justify-center gap-2"
              >
                <Plus size={20} />
                Create Your First Interview
              </button>
            </div>
          </div>
        )}

        {/* Start New Interview CTA - Show when user has sessions */}
        {!isLoading && sessions.length > 0 && (
          <div className="mb-8">
            <button
              onClick={() => setIsModalOpen(true)}
              className="btn-primary w-full md:w-auto flex items-center justify-center gap-2"
            >
              <Plus size={20} />
              Start New Interview
            </button>
          </div>
        )}

        {/* Interview History */}
        <div className="mb-4">
          <h2 className="heading-section mb-4">Recent Interviews</h2>
        </div>

        {/* Loading State */}
        {isLoading && (
          <div className="card p-12 text-center">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-electric-blue border-t-transparent mb-4"></div>
            <p className="text-text-secondary">Loading your interviews...</p>
          </div>
        )}

        {/* Error State */}
        {error && !isLoading && (
          <div className="card p-8 border-status-error/20 bg-status-error/5">
            <div className="flex items-center gap-3 text-status-error">
              <AlertCircle size={24} />
              <div>
                <p className="font-semibold mb-1">Failed to load interviews</p>
                <p className="body-small">{error}</p>
              </div>
            </div>
            <button
              onClick={loadInterviews}
              className="btn-secondary mt-4"
            >
              Try Again
            </button>
          </div>
        )}

        {/* Empty State */}
        {!isLoading && !error && sessions.length === 0 && (
          <div className="card p-12 text-center">
            <div className="max-w-md mx-auto">
              <img
                src="/images/empty-state.png"
                alt="No interviews yet"
                className="w-48 h-48 mx-auto mb-6 opacity-80"
              />
              <h3 className="heading-card mb-2">No interviews yet</h3>
              <p className="text-text-secondary mb-6">
                Get started by creating your first interview session. Practice makes perfect!
              </p>
              <button
                onClick={() => setIsModalOpen(true)}
                className="btn-primary"
              >
                <Plus size={20} className="inline mr-2" />
                Start Your First Interview
              </button>
            </div>
          </div>
        )}

        {/* Interview List */}
        {!isLoading && !error && sessions.length > 0 && (
          <div className="grid gap-4">
            {sessions.map((session) => (
              <InterviewCard
                key={session.id}
                session={session}
                onClick={() => handleSessionClick(session)}
              />
            ))}
          </div>
        )}
      </div>

      {/* New Interview Modal */}
      <NewInterviewModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSubmit={handleCreateInterview}
      />

      {/* Upgrade Modal */}
      <UpgradeModal
        isOpen={showUpgradeModal}
        onClose={() => setShowUpgradeModal(false)}
        currentTier="free"
        onSuccess={() => {
          setShowUpgradeModal(false);
          setError(null);
        }}
      />

      {/* Welcome Modal for New Users */}
      <WelcomeModal
        isOpen={showWelcomeModal}
        onClose={handleWelcomeClose}
        onStartInterview={handleWelcomeStartInterview}
        userName={user?.full_name?.split(' ')[0]}
      />
    </div>
  );
}
