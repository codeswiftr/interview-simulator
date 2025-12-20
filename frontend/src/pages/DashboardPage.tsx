import { useState, useMemo, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, AlertCircle, Lightbulb, Sparkles, Activity, Target, Mic, BarChart2 } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { useDashboardModals } from '../hooks/useDashboardModals';
import { interviewsAPI, userAPI, preparationAPI } from '../lib/api';
import StatsOverview from '../components/dashboard/StatsOverview';
import ProgressChart from '../components/dashboard/ProgressChart';
import CategoryBreakdown from '../components/dashboard/CategoryBreakdown';
import ActivityHeatmap from '../components/dashboard/ActivityHeatmap';
import SkillsRadar from '../components/dashboard/SkillsRadar';
import ImprovementsByCriteria from '../components/dashboard/ImprovementsByCriteria';
import InterviewCard from '../components/interview/InterviewCard';
import NewInterviewModal from '../components/interview/NewInterviewModal';
import UpgradeModal from '../components/subscription/UpgradeModal';
import WelcomeModal from '../components/onboarding/WelcomeModal';
import FirstSessionPrompt from '../components/onboarding/FirstSessionPrompt';
import ContextualTooltip from '../components/common/ContextualTooltip';
import { Skeleton, SkeletonStatsOverview, SkeletonInterviewList } from '../components/ui/Skeleton';
import { Card } from '../components/ui/Card';
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

  return (
    <div className="min-h-screen bg-surface-primary pb-12">
      <div className="container mx-auto px-6 py-8 max-w-7xl">
        {/* Header Section */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
          <div>
            <h1 className="heading-page mb-2">Welcome back{user?.full_name ? `, ${user.full_name}` : ''}!</h1>
            <p className="text-text-secondary">Track your progress and continue practicing your interview skills.</p>
          </div>

          {!isLoading && sessions.length > 0 && (
            <button
              onClick={openNewInterview}
              className="btn-primary flex items-center justify-center gap-2 shadow-lg hover:shadow-electric-blue/25"
            >
              <Plus size={20} />
              Start New Interview
            </button>
          )}
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

        {/* Onboarding Panel - Show for new users */}
        {!isLoading && sessions.length === 0 && (
          <Card className="p-8 mb-8">
            <div className="text-center mb-8">
              <div className="w-14 h-14 rounded-full bg-electric-blue/10 flex items-center justify-center mx-auto mb-4">
                <Sparkles className="w-7 h-7 text-electric-blue" />
              </div>
              <h2 className="heading-section mb-2">Welcome to Interview Simulator</h2>
              <p className="body-default text-text-secondary max-w-lg mx-auto">
                Practice your interview skills with AI-powered feedback. Get started in 3 simple steps.
              </p>
            </div>

            <div className="grid md:grid-cols-3 gap-4 mb-8">
              <div className="flex items-start gap-4 p-4 rounded-lg bg-surface-secondary/50">
                <div className="w-10 h-10 rounded-lg bg-electric-blue/10 flex items-center justify-center shrink-0">
                  <Target className="w-5 h-5 text-electric-blue" />
                </div>
                <div>
                  <h3 className="font-semibold text-text-primary mb-1">Choose Topic</h3>
                  <p className="text-sm text-text-secondary">Select behavioral, technical, or system design</p>
                </div>
              </div>

              <div className="flex items-start gap-4 p-4 rounded-lg bg-surface-secondary/50">
                <div className="w-10 h-10 rounded-lg bg-emerald-500/10 flex items-center justify-center shrink-0">
                  <Mic className="w-5 h-5 text-emerald-500" />
                </div>
                <div>
                  <h3 className="font-semibold text-text-primary mb-1">Record Answer</h3>
                  <p className="text-sm text-text-secondary">Speak naturally, we transcribe for you</p>
                </div>
              </div>

              <div className="flex items-start gap-4 p-4 rounded-lg bg-surface-secondary/50">
                <div className="w-10 h-10 rounded-lg bg-indigo-500/10 flex items-center justify-center shrink-0">
                  <BarChart2 className="w-5 h-5 text-indigo-500" />
                </div>
                <div>
                  <h3 className="font-semibold text-text-primary mb-1">Get Feedback</h3>
                  <p className="text-sm text-text-secondary">AI analysis of content and delivery</p>
                </div>
              </div>
            </div>

            <div className="text-center">
              <button
                onClick={openNewInterview}
                className="btn-primary inline-flex items-center justify-center gap-2 px-6 py-3"
              >
                <Plus size={20} />
                Start Your First Interview
              </button>
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
    </div>
  );
}
