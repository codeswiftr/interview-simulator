import { useState, useEffect, useMemo, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, AlertCircle, Lightbulb, Sparkles, Activity, Target, TrendingUp, CheckCircle, XCircle } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { useOnboarding } from '../hooks/useOnboarding';
import { interviewsAPI, userAPI, preparationAPI } from '../lib/api';
import StatsOverview from '../components/dashboard/StatsOverview';
import ProgressChart from '../components/dashboard/ProgressChart';
import CategoryBreakdown from '../components/dashboard/CategoryBreakdown';
import ActivityHeatmap from '../components/dashboard/ActivityHeatmap';
import SkillsRadar from '../components/dashboard/SkillsRadar';
import InterviewCard from '../components/interview/InterviewCard';
import NewInterviewModal from '../components/interview/NewInterviewModal';
import UpgradeModal from '../components/subscription/UpgradeModal';
import WelcomeModal from '../components/onboarding/WelcomeModal';
import FirstSessionPrompt from '../components/onboarding/FirstSessionPrompt';
import ContextualTooltip from '../components/common/ContextualTooltip';
import ComingSoonBadge from '../components/ui/ComingSoonBadge';
import { Skeleton, SkeletonStatsOverview, SkeletonInterviewList } from '../components/ui/Skeleton';
import { Button } from '../components/ui/button';
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
  const {
    shouldShowWelcome,
    markWelcomeSeen,
    shouldShowFirstSessionPrompt,
    markFirstSessionCreated,
  } = useOnboarding();
  const [sessions, setSessions] = useState<InterviewSession[]>([]);
  const [preparations, setPreparations] = useState<Array<{
    id: string;
    question_id: string;
    question_content: string;
    stage: string;
    draft_answer: string | null;
    created_at: string;
    updated_at: string;
  }>>([]);
  const [userStats, setUserStats] = useState<UserStats | null>(null);
  const [userProgress, setUserProgress] = useState<UserProgress | null>(null);
  const [readinessScore, setReadinessScore] = useState<ReadinessScore | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [showUpgradeModal, setShowUpgradeModal] = useState(false);
  const [showWelcomeModal, setShowWelcomeModal] = useState(false);
  const [showFirstSessionPrompt, setShowFirstSessionPrompt] = useState(false);

  // If the user came from a pricing CTA (e.g. /register?plan=pro), open the upgrade modal on first login.
  useEffect(() => {
    const pendingPlan = sessionStorage.getItem('pending_plan');
    if (!pendingPlan) return;

    sessionStorage.removeItem('pending_plan');

    if (pendingPlan === 'pro' && user?.subscription_tier === 'free') {
      setShowUpgradeModal(true);
    }
  }, [user?.subscription_tier]);

  // Show welcome modal for new users after data loads
  useEffect(() => {
    if (!isLoading && !showUpgradeModal && shouldShowWelcome && sessions.length === 0) {
      setShowWelcomeModal(true);
    }
  }, [isLoading, shouldShowWelcome, sessions.length, showUpgradeModal]);

  // Show first session prompt after welcome is seen
  useEffect(() => {
    if (!isLoading && !showUpgradeModal && shouldShowFirstSessionPrompt && sessions.length === 0) {
      setShowFirstSessionPrompt(true);
    }
  }, [isLoading, shouldShowFirstSessionPrompt, sessions.length, showUpgradeModal]);

  const handleWelcomeClose = () => {
    markWelcomeSeen();
    setShowWelcomeModal(false);
  };

  const handleWelcomeComplete = () => {
    markWelcomeSeen();
    setShowWelcomeModal(false);
    // Show first session prompt after welcome
    setShowFirstSessionPrompt(true);
  };

  const handleFirstSessionCreate = () => {
    markFirstSessionCreated();
    setShowFirstSessionPrompt(false);
    setIsModalOpen(true);
  };

  const handleFirstSessionSkip = () => {
    markFirstSessionCreated();
    setShowFirstSessionPrompt(false);
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

  const loadPreparations = useCallback(async () => {
    try {
      // Only load if user has Pro/Team tier
      if (user?.subscription_tier === 'pro' || user?.subscription_tier === 'team') {
        const response = await preparationAPI.getAll();
        setPreparations(response.data.preparations);
      }
    } catch {
      // Silently fail - user might not have access
    }
  }, [user?.subscription_tier]);

  const loadData = useCallback(async () => {
    await Promise.all([loadInterviews(), loadStats(), loadProgress(), loadReadinessScore(), loadPreparations()]);
  }, [loadInterviews, loadPreparations]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const loadStats = async () => {
    try {
      const response = await userAPI.getStats();
      setUserStats(response.data);
    } catch (err) {
      console.warn('Failed to load user stats:', err);
    }
  };

  const loadProgress = async () => {
    try {
      const response = await userAPI.getProgress();
      setUserProgress(response.data);
    } catch (err) {
      console.warn('Failed to load user progress:', err);
    }
  };

  const loadReadinessScore = async () => {
    try {
      const response = await userAPI.getReadinessScore();
      setReadinessScore(response.data);
    } catch (err) {
      console.warn('Failed to load readiness score:', err);
    }
  };

  const handleCreateInterview = async (data: CreateInterviewFormData) => {
    try {
      const response = await interviewsAPI.create(data);
      const newSession = response.data;
      // Mark first session as created if this is the first one
      if (sessions.length === 0) {
        markFirstSessionCreated();
      }
      await loadInterviews();
      setIsModalOpen(false);
      navigate(`/interview/${newSession.id}`);
    } catch (err) {
      const axiosError = err as AxiosError<{ message?: string }>;
      if (axiosError.response?.status === 402) {
        setShowUpgradeModal(true);
        setError('Free tier limit reached. Upgrade to Pro for unlimited interviews.');
      } else {
        setError(axiosError.response?.data?.message || 'Failed to create interview');
      }
    }
  };

  const handleSessionClick = (session: InterviewSession) => {
    if (session.status === 'completed' || session.status === 'analyzed') {
      navigate(`/interview/${session.id}/feedback`);
    } else {
      navigate(`/interview/${session.id}`);
    }
  };

  const stats = {
    totalInterviews: userStats?.total_sessions ?? sessions.length,
    completedInterviews: userStats?.completed_sessions ?? sessions.filter((s) => s.status === 'completed' || s.status === 'analyzed').length,
    averageScore: userStats?.average_score ?? (sessions
      .filter((s) => s.overall_score !== null && s.overall_score !== undefined)
      .reduce((acc, s) => acc + (s.overall_score || 0), 0) /
      Math.max(1, sessions.filter((s) => s.overall_score !== null).length)),
    inProgress: sessions.filter((s) => s.status === 'in_progress').length,
  };

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

  // Generate heatmap data from sessions
  const heatmapData = useMemo(() => {
    const activityMap: Record<string, { count: number; totalScore: number; scoredSessions: number }> = {};

    sessions.forEach(session => {
      const date = new Date(session.created_at).toISOString().split('T')[0];
      if (!activityMap[date]) {
        activityMap[date] = { count: 0, totalScore: 0, scoredSessions: 0 };
      }
      activityMap[date].count++;
      if (session.overall_score) {
        activityMap[date].totalScore += session.overall_score;
        activityMap[date].scoredSessions++;
      }
    });

    return Object.entries(activityMap).map(([date, data]) => {
      const avgScore = data.scoredSessions > 0 ? Math.round(data.totalScore / data.scoredSessions) : undefined;
      // Mock trend logic for demo purposes
      let trend: 'improvement' | 'regression' | 'neutral' = 'neutral';
      if (avgScore) {
        if (avgScore >= 80) trend = 'improvement';
        else if (avgScore < 60) trend = 'regression';
      }

      return {
        date,
        count: data.count,
        score: avgScore,
        trend
      };
    });
  }, [sessions]);

  // Generate radar data from progress
  const radarData = useMemo(() => {
    if (!userProgress) return undefined;

    return [
      { subject: 'Content', current: Math.round(userProgress.average_content_score || 0), target: 90 },
      { subject: 'Delivery', current: Math.round(userProgress.average_audio_score || 0), target: 85 },
      // Mock other dimensions for now as they aren't in the API yet
      { subject: 'Behavioral', current: 75, target: 90 },
      { subject: 'Technical', current: 60, target: 85 },
      { subject: 'System Design', current: 40, target: 80 },
    ];
  }, [userProgress]);

  return (
    <div className="min-h-screen bg-surface-primary pb-12">
      {/* Background decoration */}
      <div className="fixed top-0 left-0 w-full h-full overflow-hidden pointer-events-none z-0">
        <div className="absolute top-[-10%] right-[-10%] w-[600px] h-[600px] rounded-full bg-electric-blue/5 blur-[100px]" />
        <div className="absolute bottom-[-10%] left-[-10%] w-[500px] h-[500px] rounded-full bg-indigo-500/5 blur-[100px]" />
      </div>

      <div className="container mx-auto px-6 py-8 max-w-7xl relative z-10">
        {/* Header Section */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
          <div className="min-w-0 flex-1">
            <h1 className="heading-page mb-2 truncate">Welcome back{user?.full_name ? `, ${user.full_name.split(' ')[0]}` : ''}!</h1>
            <p className="text-text-secondary text-sm sm:text-base">Track your progress and continue practicing your interview skills.</p>
          </div>

          {!isLoading && sessions.length > 0 && (
            <button
              onClick={() => setIsModalOpen(true)}
              className="btn-primary flex items-center justify-center gap-2 shadow-lg hover:shadow-electric-blue/25 whitespace-nowrap shrink-0"
            >
              <Plus size={20} />
              <span className="hidden sm:inline">Start New Interview</span>
              <span className="sm:hidden">New Session</span>
            </button>
          )}
        </div>

        {/* Stats Overview */}
        <div className="mb-8 animate-fade-in">
          <StatsOverview
            totalSessions={stats.totalInterviews}
            completedSessions={stats.completedInterviews}
            averageScore={stats.averageScore && stats.averageScore > 0 ? stats.averageScore : null}
            totalPracticeTimeSeconds={userStats?.total_practice_time_seconds ?? 0}
            readinessScore={readinessScore}
          />
        </div>

        {/* Activity Heatmap */}
        {sessions.length > 0 && (
          <div className="card-glass p-6 mb-8 animate-slide-up">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 rounded-lg bg-emerald-500/10">
                <Activity className="w-5 h-5 text-emerald-500" />
              </div>
              <h3 className="heading-card">Practice Activity</h3>
            </div>
            <ActivityHeatmap data={heatmapData} />
          </div>
        )}

        {/* Skills & Progress Grid */}
        {sessions.length > 0 && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8 animate-slide-up">
            {/* Skills Radar */}
            <div className="card-glass p-6 lg:col-span-1 relative">
              <ComingSoonBadge text="Preview" />
              <div className="flex items-center gap-3 mb-6">
                <div className="p-2 rounded-lg bg-indigo-500/10">
                  <Target className="w-5 h-5 text-indigo-500" />
                </div>
                <h3 className="heading-card">Skills Gap Analysis</h3>
              </div>
              <SkillsRadar data={radarData} />
            </div>

            {/* Progress Chart */}
            <div className="card-glass p-6 lg:col-span-2">
              <h3 className="heading-card mb-6">Performance Trend</h3>
              <ProgressChart
                data={userProgress?.score_trend || []}
                height={260}
              />
            </div>
          </div>
        )}

        {/* Improvements by Criteria (New Section) */}
        {sessions.length > 0 && (
          <div className="card-glass p-6 mb-8 animate-slide-up relative">
            <ComingSoonBadge text="Preview" />
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 rounded-lg bg-amber-500/10">
                <TrendingUp className="w-5 h-5 text-amber-500" />
              </div>
              <h3 className="heading-card">Improvements by Criteria</h3>
            </div>

            <div className="grid md:grid-cols-3 gap-6">
              {/* Delivery Improvements */}
              <div className="p-4 rounded-xl bg-surface-secondary/50 border border-border-light">
                <h4 className="font-semibold text-text-primary mb-3 flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-electric-blue"></span>
                  Delivery
                </h4>
                <ul className="space-y-2">
                  <li className="flex items-start gap-2 text-sm text-text-secondary">
                    <CheckCircle className="w-4 h-4 text-emerald-500 mt-0.5 shrink-0" />
                    <span>Pacing improved by 15%</span>
                  </li>
                  <li className="flex items-start gap-2 text-sm text-text-secondary">
                    <XCircle className="w-4 h-4 text-orange-500 mt-0.5 shrink-0" />
                    <span>Reduce filler words ("um", "like")</span>
                  </li>
                </ul>
              </div>

              {/* Behavioral Improvements */}
              <div className="p-4 rounded-xl bg-surface-secondary/50 border border-border-light">
                <h4 className="font-semibold text-text-primary mb-3 flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-purple-500"></span>
                  Behavioral
                </h4>
                <ul className="space-y-2">
                  <li className="flex items-start gap-2 text-sm text-text-secondary">
                    <CheckCircle className="w-4 h-4 text-emerald-500 mt-0.5 shrink-0" />
                    <span>STAR method usage detected</span>
                  </li>
                  <li className="flex items-start gap-2 text-sm text-text-secondary">
                    <XCircle className="w-4 h-4 text-orange-500 mt-0.5 shrink-0" />
                    <span>Elaborate more on "Results"</span>
                  </li>
                </ul>
              </div>

              {/* Technical Improvements */}
              <div className="p-4 rounded-xl bg-surface-secondary/50 border border-border-light">
                <h4 className="font-semibold text-text-primary mb-3 flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                  Technical
                </h4>
                <ul className="space-y-2">
                  <li className="flex items-start gap-2 text-sm text-text-secondary">
                    <CheckCircle className="w-4 h-4 text-emerald-500 mt-0.5 shrink-0" />
                    <span>Key terminology used correctly</span>
                  </li>
                  <li className="flex items-start gap-2 text-sm text-text-secondary">
                    <XCircle className="w-4 h-4 text-orange-500 mt-0.5 shrink-0" />
                    <span>Deepen system design explanations</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* Category Breakdown */}
        {sessions.length > 0 && (
          <div className="card-glass p-6 mb-8 animate-slide-up">
            <h3 className="heading-card mb-6">Category Breakdown</h3>
            <CategoryBreakdown data={categoryBreakdown} />
          </div>
        )}

        {/* Progress Section - Practice Recommendations */}
        {userProgress && userProgress.recommended_practice_areas.length > 0 && (
          <div className="card-glass p-6 mb-8 border-l-4 border-l-electric-blue animate-slide-up" style={{ animationDelay: '0.1s' }}>
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 rounded-lg bg-electric-blue/10">
                <Lightbulb className="w-5 h-5 text-electric-blue" />
              </div>
              <h2 className="heading-section">Focus Areas</h2>
            </div>
            <p className="body-default text-text-secondary mb-4">
              Based on your recent interviews, we recommend focusing on these areas:
            </p>
            <div className="flex flex-wrap gap-2">
              {userProgress.recommended_practice_areas.map((area, idx) => (
                <span key={idx} className="badge badge-in-progress bg-white border border-electric-blue/20">
                  {area}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Onboarding Panel - Show for new users */}
        {!isLoading && sessions.length === 0 && (
          <div className="card-glass p-8 mb-8 border-2 border-electric-blue/20 bg-gradient-to-br from-white to-electric-blue/5 dark:from-surface-dark dark:to-electric-blue/10 animate-scale-in">
            <div className="flex items-center gap-3 mb-4">
              <Sparkles className="w-6 h-6 text-electric-blue" />
              <h2 className="heading-section">Get Started</h2>
            </div>
            <p className="body-default text-text-secondary mb-8 max-w-2xl">
              Complete these steps to start improving your interview skills. Our AI coach will guide you through your first session.
            </p>

            <div className="grid md:grid-cols-3 gap-6 mb-8">
              <div className="relative p-6 rounded-xl bg-white dark:bg-surface-secondary border border-border-light dark:border-border-medium shadow-sm">
                <div className="absolute -top-3 -left-3 w-8 h-8 rounded-full bg-electric-blue text-white flex items-center justify-center font-bold shadow-lg">1</div>
                <h3 className="heading-card mb-2">Create Interview</h3>
                <p className="body-small text-text-secondary">Choose your topic and difficulty level to customize your practice.</p>
              </div>

              <div className="relative p-6 rounded-xl bg-white dark:bg-surface-secondary border border-border-light dark:border-border-medium shadow-sm">
                <div className="absolute -top-3 -left-3 w-8 h-8 rounded-full bg-surface-tertiary text-text-secondary flex items-center justify-center font-bold border border-border-medium">2</div>
                <h3 className="heading-card mb-2">Record Answers</h3>
                <p className="body-small text-text-secondary">Speak naturally. We'll record and transcribe your responses.</p>
              </div>

              <div className="relative p-6 rounded-xl bg-white dark:bg-surface-secondary border border-border-light dark:border-border-medium shadow-sm">
                <div className="absolute -top-3 -left-3 w-8 h-8 rounded-full bg-surface-tertiary text-text-secondary flex items-center justify-center font-bold border border-border-medium">3</div>
                <h3 className="heading-card mb-2">Get Feedback</h3>
                <p className="body-small text-text-secondary">Receive instant AI analysis on your content and delivery.</p>
              </div>
            </div>

            <Button
              onClick={() => setIsModalOpen(true)}
              size="lg"
              className="gap-2"
            >
              <Plus size={24} />
              Create Your First Interview
            </Button>
          </div>
        )}

        {/* Preparation Sessions (Pro/Team only) */}
        {!isLoading && preparations.length > 0 && (
          <div className="animate-slide-up mb-8" style={{ animationDelay: '0.15s' }}>
            <div className="flex items-center gap-2 mb-6">
              <h2 className="heading-section">Answer Preparations</h2>
              <ContextualTooltip
                content="Resume your answer preparation sessions. Click to continue where you left off - answer questions, review your draft, or practice your delivery."
                position="right"
                trigger="click"
                title="Preparation Mode"
              />
            </div>
            <div className="grid gap-4">
              {preparations.map((prep) => (
                <div
                  key={prep.id}
                  onClick={() => navigate(`/preparation/${prep.id}`)}
                  className="card p-6 hover:border-electric-blue cursor-pointer transition-colors"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <h3 className="heading-card mb-2 line-clamp-2">{prep.question_content}</h3>
                      <div className="flex items-center gap-4 text-sm text-text-secondary">
                        <span className="badge badge-outline">
                          {prep.stage === 'detective' ? 'Answering Questions' :
                            prep.stage === 'draft' ? 'Reviewing Draft' :
                              prep.stage === 'practice' ? 'Practicing' :
                                'Complete'}
                        </span>
                        <span className="text-text-tertiary">
                          Updated {new Date(prep.updated_at).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                    <Sparkles size={20} className="text-electric-blue shrink-0" />
                  </div>
                  {prep.draft_answer && (
                    <p className="text-sm text-text-secondary line-clamp-2 mt-2">
                      {prep.draft_answer.substring(0, 150)}...
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Interview History */}
        {!isLoading && sessions.length > 0 && (
          <div className="animate-slide-up" style={{ animationDelay: '0.2s' }}>
            <div className="flex items-center gap-2 mb-6">
              <h2 className="heading-section">Recent Interviews</h2>
              <ContextualTooltip
                content="View and continue your practice sessions. Click on any session to see feedback or resume recording. Completed sessions show your scores and detailed analysis."
                position="right"
                trigger="click"
                title="Interview Sessions"
              />
            </div>
            <div className="grid gap-4">
              {sessions.map((session) => (
                <InterviewCard
                  key={session.id}
                  session={session}
                  onClick={() => handleSessionClick(session)}
                />
              ))}
            </div>
          </div>
        )}

        {/* Loading State */}
        {isLoading && (
          <div className="space-y-8">
            <SkeletonStatsOverview />
            <div>
              <Skeleton variant="text" width={200} height={24} className="mb-6" />
              <SkeletonInterviewList count={3} />
            </div>
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
        onStartInterview={handleWelcomeComplete}
        userName={user?.full_name?.split(' ')[0]}
      />

      {/* First Session Prompt */}
      <FirstSessionPrompt
        isOpen={showFirstSessionPrompt}
        onCreateSession={handleFirstSessionCreate}
        onSkip={handleFirstSessionSkip}
      />
    </div>
  );
}
