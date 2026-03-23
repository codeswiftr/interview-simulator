import { useState, useMemo, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, AlertCircle, Lightbulb, Sparkles, Activity, Target, Mic, BarChart2 } from 'lucide-react';
import { analytics, Events } from '../lib/analytics';
import { useAuth } from '../hooks/useAuth';
import { useDashboardModals } from '../hooks/useDashboardModals';
import { interviewsAPI, userAPI, preparationAPI } from '../lib/api';
import StatsOverview from '../components/dashboard/StatsOverview';
import ProgressChart from '../components/dashboard/ProgressChart';
import CategoryBreakdown from '../components/dashboard/CategoryBreakdown';
import ActivityHeatmap from '../components/dashboard/ActivityHeatmap';
import SkillsRadar from '../components/dashboard/SkillsRadar';
import ImprovementsByCriteria from '../components/dashboard/ImprovementsByCriteria';
import HeroStats from '../components/dashboard/HeroStats';
import RecentSessions from '../components/dashboard/RecentSessions';
import NextActions from '../components/dashboard/NextActions';
import WeeklyProgress from '../components/dashboard/WeeklyProgress';
import InterviewCard from '../components/interview/InterviewCard';
import NewInterviewModal from '../components/interview/NewInterviewModal';
import UpgradeModal from '../components/subscription/UpgradeModal';
import WelcomeModal from '../components/onboarding/WelcomeModal';
import FirstSessionPrompt from '../components/onboarding/FirstSessionPrompt';
import ContextualTooltip from '../components/common/ContextualTooltip';
import { Skeleton, SkeletonStatsOverview, SkeletonInterviewList } from '../components/ui/Skeleton';
import { Card } from '../components/ui/Card';
import { ErrorBoundary } from '../components/ErrorBoundary';
import type { InterviewSession, CreateInterviewFormData, ImprovementsByCriteriaResponse, SkillsGapResponse } from '../types';
import type { AxiosError } from 'axios';
import { useEffect } from 'react';

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
  const [improvements, setImprovements] = useState<ImprovementsByCriteriaResponse | null>(null);
  const [improvementsLoading, setImprovementsLoading] = useState(true);
  const [skillsGap, setSkillsGap] = useState<SkillsGapResponse | null>(null);
  const [skillsGapLoading, setSkillsGapLoading] = useState(true);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Centralized modal state management
  const {
    isNewInterviewOpen,
    isUpgradeOpen,
    isWelcomeOpen,
    isFirstSessionPromptOpen,
    openNewInterview,
    closeNewInterview,
    openUpgrade,
    closeUpgrade,
    closeWelcome,
    completeWelcome,
    createFirstSession,
    skipFirstSession,
  } = useDashboardModals({
    sessionsCount: sessions.length,
    isDataLoaded: !isLoading,
    userSubscriptionTier: user?.subscription_tier,
  });

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
    await Promise.all([loadInterviews(), loadStats(), loadProgress(), loadReadinessScore(), loadPreparations(), loadImprovements(), loadSkillsGap()]);
  }, [loadInterviews, loadPreparations]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Listen for header contextual action to open new interview modal
  useEffect(() => {
    const handleOpenNewInterview = () => openNewInterview();
    window.addEventListener('open-new-interview', handleOpenNewInterview);
    return () => window.removeEventListener('open-new-interview', handleOpenNewInterview);
  }, [openNewInterview]);

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

  const loadImprovements = async () => {
    try {
      setImprovementsLoading(true);
      const response = await userAPI.getImprovements();
      setImprovements(response.data);
    } catch (err) {
      console.warn('Failed to load improvements:', err);
    } finally {
      setImprovementsLoading(false);
    }
  };

  const loadSkillsGap = async () => {
    try {
      setSkillsGapLoading(true);
      const response = await userAPI.getSkillsGap();
      setSkillsGap(response.data);
    } catch (err) {
      console.warn('Failed to load skills gap:', err);
    } finally {
      setSkillsGapLoading(false);
    }
  };

  const handleCreateInterview = async (data: CreateInterviewFormData) => {
    try {
      const response = await interviewsAPI.create(data);
      const newSession = response.data;
      await loadInterviews();
      closeNewInterview();
      navigate(`/interview/${newSession.id}`);
    } catch (err) {
      const axiosError = err as AxiosError<{ message?: string }>;
      if (axiosError.response?.status === 402) {
        analytics.track(Events.LIMIT_REACHED, {
          limit_type: 'interview_sessions',
          trigger: 'create_interview',
        });
        openUpgrade();
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

  // Generate radar data from skills gap API
  const radarData = useMemo(() => {
    if (!skillsGap?.data_available || !skillsGap.dimensions?.length) {
      return undefined;
    }

    // Transform API response to SkillsRadar format
    return skillsGap.dimensions.map((dim) => ({
      subject: dim.name,
      current: Math.round(dim.current_score),
      target: dim.target_score,
    }));
  }, [skillsGap]);

  // Compute derived data for new premium components
  const heroStatsData = useMemo(() => {
    const completedSessions = sessions.filter(
      (s) => s.status === 'completed' || s.status === 'analyzed'
    );

    // Weekly change: sessions created in last 7 days
    const oneWeekAgo = Date.now() - 7 * 24 * 60 * 60 * 1000;
    const weeklyChange = sessions.filter(
      (s) => new Date(s.created_at).getTime() > oneWeekAgo
    ).length;

    // Average score
    const scoredSessions = completedSessions.filter(
      (s) => s.overall_score !== null && s.overall_score !== undefined
    );
    const avgScore =
      scoredSessions.length > 0
        ? Math.round(
            scoredSessions.reduce((acc, s) => acc + (s.overall_score || 0), 0) /
              scoredSessions.length
          )
        : 0;

    // Score change vs 5 sessions ago — compare last 5 vs previous 5
    const last5 = scoredSessions.slice(-5);
    const prev5 = scoredSessions.slice(-10, -5);
    const last5Avg =
      last5.length > 0
        ? last5.reduce((a, s) => a + (s.overall_score || 0), 0) / last5.length
        : 0;
    const prev5Avg =
      prev5.length > 0
        ? prev5.reduce((a, s) => a + (s.overall_score || 0), 0) / prev5.length
        : last5Avg;
    const scoreChange = Math.round(last5Avg - prev5Avg);

    // Streak: consecutive days with at least one session ending today
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const sessionDates = new Set(
      sessions.map((s) => {
        const d = new Date(s.created_at);
        d.setHours(0, 0, 0, 0);
        return d.getTime();
      })
    );
    let streakDays = 0;
    let checkDay = today.getTime();
    while (sessionDates.has(checkDay)) {
      streakDays++;
      checkDay -= 24 * 60 * 60 * 1000;
    }

    // Streak history: last 7 days bool array (index 0 = 6 days ago, index 6 = today)
    const streakHistory: boolean[] = Array.from({ length: 7 }, (_, i) => {
      const d = new Date(today);
      d.setDate(d.getDate() - (6 - i));
      return sessionDates.has(d.getTime());
    });

    return {
      totalInterviews: userStats?.total_sessions ?? sessions.length,
      weeklyChange,
      averageScore: avgScore,
      scoreChange,
      streakDays,
      streakHistory,
    };
  }, [sessions, userStats]);

  // Weekly bar chart data (Mon–Sun, current week)
  const weeklyProgressData = useMemo(() => {
    const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    const jsDay = new Date().getDay(); // 0=Sun
    const todayIndex = jsDay === 0 ? 6 : jsDay - 1;

    // Find start of current week (Monday)
    const now = new Date();
    const startOfWeek = new Date(now);
    startOfWeek.setDate(now.getDate() - todayIndex);
    startOfWeek.setHours(0, 0, 0, 0);

    return days.map((label, i) => {
      const dayStart = new Date(startOfWeek);
      dayStart.setDate(startOfWeek.getDate() + i);
      const dayEnd = new Date(dayStart);
      dayEnd.setDate(dayStart.getDate() + 1);

      const count = sessions.filter((s) => {
        const t = new Date(s.created_at).getTime();
        return t >= dayStart.getTime() && t < dayEnd.getTime();
      }).length;

      return { label, sessions: count, isToday: i === todayIndex };
    });
  }, [sessions]);

  // Map sessions to the new RecentSessions format
  const recentSessionsData = useMemo(() => {
    return sessions
      .slice()
      .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
      .slice(0, 8)
      .map((s) => ({
        id: s.id,
        type: s.interview_type ?? 'coding',
        title: s.interview_type
          ? `${s.interview_type.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())} Interview`
          : 'Practice Interview',
        score: s.overall_score ?? null,
        duration: s.duration_seconds ? Math.round(s.duration_seconds / 60) : 0,
        completedAt: s.created_at,
      }));
  }, [sessions]);

  const hasWeakAreas =
    userProgress?.recommended_practice_areas &&
    userProgress.recommended_practice_areas.length > 0;

  return (
    <ErrorBoundary fallback={
      <div className="min-h-screen bg-surface-primary flex items-center justify-center p-6">
        <div className="card p-8 max-w-md w-full text-center">
          <AlertCircle className="w-16 h-16 text-status-error mx-auto mb-4" />
          <h2 className="heading-section mb-4">Dashboard Error</h2>
          <p className="body-default text-text-secondary mb-6">
            We encountered an error loading your dashboard. Please refresh the page or contact support if the issue persists.
          </p>
          <button onClick={() => window.location.reload()} className="btn-primary">
            Refresh Page
          </button>
        </div>
      </div>
    }>
      <div className="min-h-screen bg-surface-primary pb-12">
        <div className="container mx-auto px-4 sm:px-6 py-8 max-w-7xl">
        {/* Header Section */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
          <div>
            <h1 className="heading-page mb-2">Welcome back{user?.full_name ? `, ${user.full_name}` : ''}!</h1>
            <p className="text-text-secondary">Track your progress and continue practicing your interview skills.</p>
          </div>

          {/* Usage indicator for free tier - PROMINENT CTA */}
          {user?.subscription_tier === 'free' && (() => {
            const used = user.interviews_this_month ?? 0;
            const remaining = Math.max(0, 3 - used);
            const isAtLimit = used >= 3;
            const isNearLimit = remaining === 1;
            return (
              <div className={`flex items-center gap-3 px-4 py-3 rounded-xl border ${
                isAtLimit
                  ? 'bg-gradient-to-r from-red-500/15 via-[#FF6B9D]/10 to-red-500/5 border-red-500/30'
                  : isNearLimit
                  ? 'bg-gradient-to-r from-amber-500/15 via-[#FF6B9D]/10 to-amber-500/5 border-amber-500/30'
                  : 'bg-gradient-to-r from-[#FF6B9D]/10 via-[#FF6B9D]/5 to-electric-blue/5 border-[#FF6B9D]/20'
              }`}>
                <div className="flex-1">
                  <p className="font-semibold text-text-primary">
                    {isAtLimit
                      ? '🚫 Monthly limit reached'
                      : isNearLimit
                      ? `⚠️ ${remaining} interview left this month`
                      : `${used} of 3 free interviews used`}
                  </p>
                  <p className="text-sm text-text-secondary">
                    {isAtLimit
                      ? 'Upgrade to Pro for unlimited interviews + advanced AI feedback'
                      : 'Unlock unlimited interviews + advanced AI feedback'}
                  </p>
                </div>
                <button
                  onClick={openUpgrade}
                  className={`px-4 py-2 rounded-lg text-white font-medium text-sm transition-colors shadow-md ${
                    isAtLimit
                      ? 'bg-red-500 hover:bg-red-600 shadow-red-500/20'
                      : isNearLimit
                      ? 'bg-amber-500 hover:bg-amber-600 shadow-amber-500/20'
                      : 'bg-[#FF6B9D] hover:bg-[#FF5588] shadow-[#FF6B9D]/20'
                  }`}
                >
                  Upgrade Now
                </button>
              </div>
            );
          })()}

          {!isLoading && sessions.length > 0 && (
            <button
              onClick={openNewInterview}
              className="btn-primary flex items-center justify-center gap-2 shadow-lg hover:shadow-electric-blue/25 w-full sm:w-auto"
            >
              <Plus size={20} />
              Start New Interview
            </button>
          )}
        </div>

        {/* Premium Hero Stats — new design */}
        {!isLoading && (
          <div className="mb-8">
            <HeroStats
              totalInterviews={heroStatsData.totalInterviews}
              weeklyChange={heroStatsData.weeklyChange}
              averageScore={heroStatsData.averageScore}
              scoreChange={heroStatsData.scoreChange}
              streakDays={heroStatsData.streakDays}
              streakHistory={heroStatsData.streakHistory}
            />
          </div>
        )}

        {/* Stats Overview (legacy — kept for practice time + readiness score) */}
        <div className="mb-8">
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
          <Card className="p-6 mb-8">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 rounded-lg bg-emerald-500/10">
                <Activity className="w-5 h-5 text-emerald-500" />
              </div>
              <h3 className="heading-card">Practice Activity</h3>
            </div>
            <ActivityHeatmap data={heatmapData} />
          </Card>
        )}

        {/* Skills & Progress Grid */}
        {sessions.length > 0 && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
            {/* Skills Radar */}
            <Card className="p-6 lg:col-span-1 relative">
              <div className="flex items-center gap-3 mb-6">
                <div className="p-2 rounded-lg bg-indigo-500/10">
                  <Target className="w-5 h-5 text-indigo-500" />
                </div>
                <h3 className="heading-card">Skills Gap Analysis</h3>
              </div>
              <SkillsRadar data={radarData} isLoading={skillsGapLoading} />
            </Card>

            {/* Progress Chart */}
            <Card className="p-6 lg:col-span-2">
              <h3 className="heading-card mb-6">Performance Trend</h3>
              <ProgressChart
                data={userProgress?.score_trend || []}
                height={260}
              />
            </Card>
          </div>
        )}

        {/* Improvements by Criteria */}
        {sessions.length > 0 && (
          <ImprovementsByCriteria data={improvements} isLoading={improvementsLoading} />
        )}

        {/* Premium: Weekly Progress + Recent Sessions + Next Actions */}
        {!isLoading && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
            {/* Left column: Weekly chart + Recent Sessions */}
            <div className="lg:col-span-2 flex flex-col gap-6">
              <WeeklyProgress data={weeklyProgressData} />
              <RecentSessions
                sessions={recentSessionsData}
                onReview={(id) => {
                  const session = sessions.find((s) => s.id === id);
                  if (session) handleSessionClick(session);
                }}
                onStartNew={openNewInterview}
                isLoading={isLoading}
              />
            </div>
            {/* Right column: Next Actions */}
            <div className="lg:col-span-1">
              <NextActions
                onStartNew={openNewInterview}
                hasWeakAreas={hasWeakAreas ?? false}
                totalSessions={sessions.length}
              />
            </div>
          </div>
        )}

        {/* Category Breakdown */}
        {sessions.length > 0 && (
          <div className="mb-8">
            <CategoryBreakdown data={categoryBreakdown} />
          </div>
        )}

        {/* Progress Section - Practice Recommendations */}
        {userProgress && userProgress.recommended_practice_areas && userProgress.recommended_practice_areas.length > 0 && (
          <Card className="p-6 mb-8 border-l-4 border-l-electric-blue">
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
                <span key={idx} className="badge badge-in-progress bg-[hsl(var(--card))] border border-electric-blue/20">
                  {area}
                </span>
              ))}
            </div>
          </Card>
        )}

        {/* Hero Banner - Show for new users with zero sessions */}
        {!isLoading && sessions.length === 0 && (
          <Card className="mb-8 overflow-hidden border-electric-blue/30">
            {/* Hero gradient strip */}
            <div className="bg-gradient-to-r from-electric-blue/20 via-indigo-500/10 to-electric-blue/5 px-8 py-10 text-center border-b border-electric-blue/20">
              <div className="w-16 h-16 rounded-2xl bg-electric-blue/15 border border-electric-blue/30 flex items-center justify-center mx-auto mb-5 shadow-lg shadow-electric-blue/10">
                <Sparkles className="w-8 h-8 text-electric-blue" />
              </div>
              <h2 className="text-2xl font-bold text-text-primary mb-2">Ready to ace your next interview?</h2>
              <p className="body-default text-text-secondary max-w-md mx-auto mb-6">
                Your first AI-powered practice session takes under 5 minutes. Get instant feedback on your answers.
              </p>
              <button
                onClick={openNewInterview}
                className="btn-primary inline-flex items-center justify-center gap-2 px-8 py-3.5 text-base font-semibold shadow-lg shadow-electric-blue/25 hover:shadow-electric-blue/40 transition-shadow"
                autoFocus
              >
                <Plus size={20} />
                Start My First Interview
              </button>
            </div>

            {/* Steps row */}
            <div className="grid md:grid-cols-3 gap-0 divide-y md:divide-y-0 md:divide-x divide-border-light p-0">
              <div className="flex items-start gap-4 p-5">
                <div className="w-9 h-9 rounded-lg bg-electric-blue/10 flex items-center justify-center shrink-0 mt-0.5">
                  <Target className="w-4 h-4 text-electric-blue" />
                </div>
                <div>
                  <h3 className="font-semibold text-text-primary mb-0.5 text-sm">1. Choose Topic</h3>
                  <p className="text-xs text-text-secondary">Behavioral, technical, or system design</p>
                </div>
              </div>
              <div className="flex items-start gap-4 p-5">
                <div className="w-9 h-9 rounded-lg bg-emerald-500/10 flex items-center justify-center shrink-0 mt-0.5">
                  <Mic className="w-4 h-4 text-emerald-500" />
                </div>
                <div>
                  <h3 className="font-semibold text-text-primary mb-0.5 text-sm">2. Record Answer</h3>
                  <p className="text-xs text-text-secondary">Speak naturally — we transcribe for you</p>
                </div>
              </div>
              <div className="flex items-start gap-4 p-5">
                <div className="w-9 h-9 rounded-lg bg-indigo-500/10 flex items-center justify-center shrink-0 mt-0.5">
                  <BarChart2 className="w-4 h-4 text-indigo-500" />
                </div>
                <div>
                  <h3 className="font-semibold text-text-primary mb-0.5 text-sm">3. Get Feedback</h3>
                  <p className="text-xs text-text-secondary">AI scores your content and delivery</p>
                </div>
              </div>
            </div>
          </Card>
        )}

        {/* Preparation Sessions (Pro/Team only) */}
        {!isLoading && preparations.length > 0 && (
          <div className="mb-8">
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
          <div>
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
        isOpen={isNewInterviewOpen}
        onClose={closeNewInterview}
        onSubmit={handleCreateInterview}
      />

      {/* Upgrade Modal */}
      <UpgradeModal
        isOpen={isUpgradeOpen}
        onClose={closeUpgrade}
        currentTier="free"
        onSuccess={() => {
          closeUpgrade();
          setError(null);
        }}
      />

      {/* Welcome Modal for New Users */}
      <WelcomeModal
        isOpen={isWelcomeOpen}
        onClose={closeWelcome}
        onStartInterview={completeWelcome}
        userName={user?.full_name?.split(' ')[0]}
      />

      {/* First Session Prompt */}
      <FirstSessionPrompt
        isOpen={isFirstSessionPromptOpen}
        onCreateSession={createFirstSession}
        onSkip={skipFirstSession}
      />

      {/* Mobile FAB - Start New Interview */}
      {!isLoading && sessions.length > 0 && (
        <button
          onClick={openNewInterview}
          className="fixed bottom-20 right-4 z-30 md:hidden w-14 h-14 rounded-full bg-electric-blue text-white shadow-lg shadow-electric-blue/30 flex items-center justify-center hover:bg-electric-blue/90 active:scale-95 transition-all focus:outline-none focus:ring-2 focus:ring-electric-blue focus:ring-offset-2"
          aria-label="Start new interview"
          title="Start new interview"
        >
          <Plus size={24} />
        </button>
      )}
      </div>
    </ErrorBoundary>
  );
}
