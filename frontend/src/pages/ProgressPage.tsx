import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { BarChart2, Clock, Target, TrendingUp, Calendar, ChevronRight, AlertCircle } from 'lucide-react';
import { userAPI, interviewsAPI } from '../lib/api';
import { Skeleton } from '../components/ui/Skeleton';
import { Card } from '../components/ui/Card';
import { formatRelativeTime, formatDuration, getScoreColor } from '../lib/utils';
import type { InterviewSession } from '../types';
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

export default function ProgressPage() {
  const navigate = useNavigate();
  const [stats, setStats] = useState<UserStats | null>(null);
  const [progress, setProgress] = useState<UserProgress | null>(null);
  const [sessions, setSessions] = useState<InterviewSession[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      const [statsRes, progressRes, sessionsRes] = await Promise.all([
        userAPI.getStats(),
        userAPI.getProgress(),
        interviewsAPI.getAll(),
      ]);

      setStats(statsRes.data);
      setProgress(progressRes.data);
      // Filter to only completed sessions and take the last 10
      const completedSessions = sessionsRes.data
        .filter((s: InterviewSession) => s.status === 'completed' || s.status === 'analyzed')
        .slice(0, 10);
      setSessions(completedSessions);
    } catch (err) {
      const axiosError = err as AxiosError<{ message?: string }>;
      setError(axiosError.response?.data?.message || 'Failed to load progress data');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const formatPracticeTime = (seconds: number): string => {
    if (seconds < 60) return `${seconds}s`;
    if (seconds < 3600) return `${Math.round(seconds / 60)}m`;
    const hours = Math.floor(seconds / 3600);
    const mins = Math.round((seconds % 3600) / 60);
    return `${hours}h ${mins}m`;
  };

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <Card variant="glass" className="p-6 text-center">
          <AlertCircle className="w-12 h-12 text-status-error mx-auto mb-4" />
          <h2 className="heading-card text-text-primary mb-2">Failed to Load Progress</h2>
          <p className="text-text-secondary mb-4">{error}</p>
          <button onClick={loadData} className="btn-primary">
            Try Again
          </button>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 pb-20 md:pb-8 max-w-4xl">
      {/* Page Header */}
      <section className="mb-8">
        <h1 className="heading-page text-text-primary">Your Progress</h1>
        <p className="text-text-secondary mt-1">
          Track your improvement over time
        </p>
      </section>

      {/* Stats Grid */}
      <section className="grid grid-cols-2 gap-4 mb-8">
        {isLoading ? (
          <>
            <Skeleton className="h-32 rounded-xl" />
            <Skeleton className="h-32 rounded-xl" />
            <Skeleton className="h-32 rounded-xl" />
            <Skeleton className="h-32 rounded-xl" />
          </>
        ) : (
          <>
            {/* Average Score */}
            <Card variant="glass" className="p-5">
              <div className="flex items-center gap-2 mb-3">
                <div className="p-2 rounded-lg bg-electric-blue/10">
                  <Target className="w-4 h-4 text-electric-blue" />
                </div>
                <span className="text-sm font-medium text-text-secondary">Avg Score</span>
              </div>
              <p className={`text-3xl font-bold ${stats?.average_score ? getScoreColor(stats.average_score) : 'text-text-tertiary'}`}>
                {stats?.average_score != null ? Math.round(stats.average_score) : '—'}
              </p>
              <p className="text-xs text-text-tertiary mt-1">
                {stats?.average_score != null ? 'out of 100' : 'Complete sessions to see'}
              </p>
            </Card>

            {/* Total Sessions */}
            <Card variant="glass" className="p-5">
              <div className="flex items-center gap-2 mb-3">
                <div className="p-2 rounded-lg bg-status-success/10">
                  <BarChart2 className="w-4 h-4 text-status-success" />
                </div>
                <span className="text-sm font-medium text-text-secondary">Sessions</span>
              </div>
              <p className="text-3xl font-bold text-text-primary">
                {stats?.completed_sessions ?? 0}
              </p>
              <p className="text-xs text-text-tertiary mt-1">
                completed
              </p>
            </Card>

            {/* Practice Time */}
            <Card variant="glass" className="p-5">
              <div className="flex items-center gap-2 mb-3">
                <div className="p-2 rounded-lg bg-status-warning/10">
                  <Clock className="w-4 h-4 text-status-warning" />
                </div>
                <span className="text-sm font-medium text-text-secondary">Practice Time</span>
              </div>
              <p className="text-3xl font-bold text-text-primary">
                {stats?.total_practice_time_seconds ? formatPracticeTime(stats.total_practice_time_seconds) : '0m'}
              </p>
              <p className="text-xs text-text-tertiary mt-1">
                total
              </p>
            </Card>

            {/* Score Trend */}
            <Card variant="glass" className="p-5">
              <div className="flex items-center gap-2 mb-3">
                <div className="p-2 rounded-lg bg-state-scheduled/10">
                  <TrendingUp className="w-4 h-4 text-state-scheduled" />
                </div>
                <span className="text-sm font-medium text-text-secondary">Trend</span>
              </div>
              {progress?.score_trend && progress.score_trend.length >= 2 ? (
                <>
                  {(() => {
                    const recent = progress.score_trend.slice(-5);
                    const firstScore = recent[0].score;
                    const lastScore = recent[recent.length - 1].score;
                    const trend = lastScore - firstScore;
                    const isPositive = trend >= 0;
                    return (
                      <>
                        <p className={`text-3xl font-bold ${isPositive ? 'text-status-success' : 'text-status-error'}`}>
                          {isPositive ? '+' : ''}{Math.round(trend)}
                        </p>
                        <p className="text-xs text-text-tertiary mt-1">
                          last {recent.length} sessions
                        </p>
                      </>
                    );
                  })()}
                </>
              ) : (
                <>
                  <p className="text-3xl font-bold text-text-tertiary">—</p>
                  <p className="text-xs text-text-tertiary mt-1">need 2+ sessions</p>
                </>
              )}
            </Card>
          </>
        )}
      </section>

      {/* Practice Areas */}
      {!isLoading && progress?.recommended_practice_areas && progress.recommended_practice_areas.length > 0 && (
        <section className="mb-8">
          <h2 className="text-sm font-medium text-text-tertiary uppercase tracking-wide mb-3">
            Recommended Focus Areas
          </h2>
          <Card variant="glass" className="p-4">
            <div className="flex flex-wrap gap-2">
              {progress.recommended_practice_areas.map((area, index) => (
                <span
                  key={index}
                  className="px-3 py-1.5 bg-electric-blue/10 text-electric-blue text-sm font-medium rounded-full"
                >
                  {area}
                </span>
              ))}
            </div>
          </Card>
        </section>
      )}

      {/* Session History */}
      <section>
        <h2 className="text-sm font-medium text-text-tertiary uppercase tracking-wide mb-3">
          Session History
        </h2>
        {isLoading ? (
          <div className="space-y-3">
            <Skeleton className="h-20 rounded-xl" />
            <Skeleton className="h-20 rounded-xl" />
            <Skeleton className="h-20 rounded-xl" />
          </div>
        ) : sessions.length === 0 ? (
          <Card variant="glass" className="p-8 text-center">
            <Calendar className="w-12 h-12 text-text-tertiary mx-auto mb-4" />
            <h3 className="heading-card text-text-primary mb-2">No Sessions Yet</h3>
            <p className="text-text-secondary mb-4">
              Complete your first interview to see your progress over time.
            </p>
            <button
              onClick={() => navigate('/questions')}
              className="btn-primary"
            >
              Start Practicing
            </button>
          </Card>
        ) : (
          <div className="space-y-3">
            {sessions.map((session) => (
              <Card
                key={session.id}
                variant="interactive"
                className="p-4 cursor-pointer"
                onClick={() => navigate(`/interview/${session.id}/feedback`)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className={`w-12 h-12 rounded-xl flex items-center justify-center font-bold text-lg ${
                      session.overall_score != null && session.overall_score >= 70
                        ? 'bg-status-success/10 text-status-success'
                        : session.overall_score != null
                        ? 'bg-status-warning/10 text-status-warning'
                        : 'bg-surface-tertiary text-text-tertiary'
                    }`}>
                      {session.overall_score != null ? Math.round(session.overall_score) : '—'}
                    </div>
                    <div>
                      <p className="font-medium text-text-primary capitalize">
                        {session.interview_type.replace('_', ' ')} Interview
                      </p>
                      <p className="text-sm text-text-tertiary">
                        {formatRelativeTime(session.created_at)} • {session.question_count} question{session.question_count !== 1 ? 's' : ''}
                        {session.duration_seconds && ` • ${formatDuration(session.duration_seconds)}`}
                      </p>
                    </div>
                  </div>
                  <ChevronRight className="w-5 h-5 text-text-tertiary" />
                </div>
              </Card>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
