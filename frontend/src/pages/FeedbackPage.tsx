import { useEffect, useState, useCallback, useRef } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useScrollDirection } from '../hooks/useScrollDirection';
import {
  ArrowLeft,
  RefreshCw,
  BookOpen,
  MessageSquare,
  Smile,
  Calendar,
  Clock,
  Loader2,
  Sparkles,
  TrendingUp,
  TrendingDown,
  Minus,
  CheckCircle2,
  AlertTriangle,
  BarChart
} from 'lucide-react';
import { ErrorBoundary } from '../components/ErrorBoundary';
import ScoreRing from '../components/feedback/ScoreRing';
import MetricCard from '../components/feedback/MetricCard';
import ResponseAccordion from '../components/feedback/ResponseAccordion';
import ProcessingStatus from '../components/feedback/ProcessingStatus';
import { Skeleton, SkeletonScoreRing, SkeletonText } from '../components/ui/Skeleton';
import { Card } from '../components/ui/Card';
import { feedbackAPI, interviewsAPI, responsesAPI } from '../lib/api';
import { useAuth } from '../hooks/useAuth';
import { analytics, Events } from '../lib/analytics';
import type { InterviewSession, InterviewResponse, SessionFeedback, ContentFeedback } from '../types';

interface FeedbackState {
  session: InterviewSession | null;
  sessionFeedback: SessionFeedback | null;
  responses: InterviewResponse[];
  contentFeedbacks: ContentFeedback[];
}

interface ComparisonData {
  session_score: number;
  average_score: number | null;
  improvement_percent: number | null;
  sessions_compared: number;
}

const interviewTypeLabels: Record<string, string> = {
  behavioral: 'Behavioral',
  technical: 'Technical',
  system_design: 'System Design',
  mixed: 'Mixed',
};

const experienceLevelLabels: Record<string, string> = {
  junior: 'Junior Engineers',
  mid: 'Mid-Level Engineers',
  senior: 'Senior Engineers',
};

export default function FeedbackPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [feedbackState, setFeedbackState] = useState<FeedbackState>({
    session: null,
    sessionFeedback: null,
    responses: [],
    contentFeedbacks: [],
  });
  const [comparison, setComparison] = useState<ComparisonData | null>(null);
  const [processingComplete, setProcessingComplete] = useState(false);

  // Sticky CTA tracking
  const heroRef = useRef<HTMLDivElement>(null);
  const [showStickyBar, setShowStickyBar] = useState(false);
  const scrollDirection = useScrollDirection({ threshold: 10 });

  // Track when scrolled past hero section (throttled with rAF)
  useEffect(() => {
    let ticking = false;

    const handleScroll = () => {
      if (!ticking) {
        window.requestAnimationFrame(() => {
          if (heroRef.current) {
            const heroBottom = heroRef.current.getBoundingClientRect().bottom;
            setShowStickyBar(heroBottom < 0);
          }
          ticking = false;
        });
        ticking = true;
      }
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const loadFeedback = useCallback(async () => {
    if (!id) return;

    try {
      setLoading(true);
      setError(null);

      // Fetch session and responses
      const [sessionRes, responsesRes] = await Promise.all([
        interviewsAPI.getById(id),
        responsesAPI.getBySessionId(id),
      ]);

      const session = sessionRes.data;
      const responses = responsesRes.data;

      // Try to fetch session feedback
      let sessionFeedback: SessionFeedback | null = null;
      try {
        const feedbackRes = await feedbackAPI.getBySessionId(id);
        sessionFeedback = feedbackRes.data;
      } catch {
        // No feedback yet - that's okay
      }

      // Try to fetch content feedbacks for all responses
      let contentFeedbacks: ContentFeedback[] = [];
      try {
        const contentRes = await feedbackAPI.getAllBySessionId(id);
        contentFeedbacks = contentRes.data;
      } catch {
        // No content feedbacks yet
      }

      // Fetch comparison data if session feedback exists
      if (sessionFeedback) {
        try {
          const comparisonRes = await feedbackAPI.getComparison(id);
          setComparison(comparisonRes.data);
        } catch {
          // No comparison data available (e.g., first session)
          setComparison(null);
        }
      }

      setFeedbackState({
        session,
        sessionFeedback,
        responses,
        contentFeedbacks,
      });

      // Check if all responses have been transcribed (for page refresh case)
      const allTranscribed = responses.length > 0 && responses.every((r: InterviewResponse) => r.transcript);
      setProcessingComplete(allTranscribed);
    } catch (err) {
      // Extract error message from Axios error or use generic message
      const axiosError = err as { response?: { status?: number; data?: { message?: string; detail?: string } } };
      const status = axiosError.response?.status;
      const errorMessage = axiosError.response?.data?.message
        || axiosError.response?.data?.detail
        || (status === 404 ? 'Interview session not found' : 'Failed to load interview data');
      setError(errorMessage);
      console.error('Error loading feedback:', err);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    loadFeedback();
  }, [loadFeedback]);

  // Track feedback page view
  useEffect(() => {
    if (feedbackState.session && feedbackState.sessionFeedback) {
      const createdAt = feedbackState.sessionFeedback.created_at;
      const latencyMs = createdAt ? Date.now() - new Date(createdAt).getTime() : undefined;
      analytics.track(Events.FEEDBACK_VIEWED, {
        interview_id: feedbackState.session.id,
        overall_score: feedbackState.sessionFeedback.overall_score,
        has_responses: feedbackState.responses.length > 0,
        latency_ms: typeof latencyMs === 'number' && Number.isFinite(latencyMs) ? Math.max(0, Math.round(latencyMs)) : undefined,
      });
    }
  }, [feedbackState.session, feedbackState.sessionFeedback, feedbackState.responses.length]);

  const handleGenerateFeedback = async () => {
    if (!id) return;

    try {
      setGenerating(true);
      setError(null);

      await feedbackAPI.generateForSession(id);

      // Track feedback generated
      if (feedbackState.session) {
        analytics.track(Events.FEEDBACK_GENERATED, {
          interview_id: feedbackState.session.id,
        });
      }

      // Reload feedback data
      await loadFeedback();
    } catch (err: unknown) {
      // Extract error message from Axios error or generic error
      const axiosError = err as { response?: { data?: { message?: string; detail?: string } } };
      const errorMessage = axiosError.response?.data?.message
        || axiosError.response?.data?.detail
        || (err instanceof Error ? err.message : 'Failed to generate feedback');
      setError(errorMessage);
      console.error('Error generating feedback:', err);
    } finally {
      setGenerating(false);
    }
  };

  const formatDuration = (durationSeconds?: number) => {
    if (!durationSeconds) return 'N/A';
    const minutes = Math.floor(durationSeconds / 60);
    return `${minutes} min`;
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  const getTypeLabel = (type: string) => {
    return interviewTypeLabels[type] || type;
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        <div className="mb-8">
          <Skeleton variant="text" width={300} height={32} className="mb-4" />
          <SkeletonText lines={2} width="60%" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {Array.from({ length: 3 }).map((_, i) => (
            <SkeletonScoreRing key={i} />
          ))}
        </div>
        <div className="space-y-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <Card key={i} className="p-6">
              <Skeleton variant="text" width="70%" height={20} className="mb-4" />
              <SkeletonText lines={3} />
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (error && !feedbackState.session) {
    return (
      <div className="min-h-screen bg-surface-primary flex items-center justify-center">
        <Card className="text-center p-8 border-status-error/20 bg-status-error/5">
          <p className="text-lg text-status-error mb-4">{error}</p>
          <button onClick={() => navigate('/dashboard')} className="btn-primary">
            Return to Dashboard
          </button>
        </Card>
      </div>
    );
  }

  const { session, sessionFeedback, responses, contentFeedbacks } = feedbackState;

  if (!session) {
    return (
      <div className="min-h-screen bg-surface-primary flex items-center justify-center">
        <div className="text-center">
          <p className="body-large text-text-secondary mb-4">Interview session not found</p>
          <button onClick={() => navigate('/dashboard')} className="btn-primary">
            Return to Dashboard
          </button>
        </div>
      </div>
    );
  }

  const hasFeedback = sessionFeedback !== null;

  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-surface-primary dark:bg-surface-primary pb-12 transition-colors duration-300">
        {/* Background decoration - Matched to Dashboard */}
        <div className="fixed top-0 left-0 w-full h-full overflow-hidden pointer-events-none z-0">
          <div className="absolute top-[-10%] right-[-10%] w-[600px] h-[600px] rounded-full bg-electric-blue/5 dark:bg-electric-blue/10 blur-[100px]" />
          <div className="absolute bottom-[-10%] left-[-10%] w-[500px] h-[500px] rounded-full bg-indigo-500/5 dark:bg-indigo-500/10 blur-[100px]" />
        </div>

        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 relative z-10">
          {/* Header */}
          <div className="mb-8">
            <Link
              to="/dashboard"
              className="inline-flex items-center gap-2 text-text-secondary hover:text-electric-blue transition-colors mb-6 group"
            >
              <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
              <span className="body-default font-medium">Back to Dashboard</span>
            </Link>

            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div>
                <h1 className="heading-page mb-2 text-[var(--fg-primary)]">Interview Feedback</h1>
                <div className="flex items-center gap-4 text-text-secondary dark:text-text-tertiary">
                  <div className="flex items-center gap-2">
                    <Calendar className="w-4 h-4" />
                    <span className="body-small">{formatDate(session.created_at)}</span>
                  </div>
                  {session.duration_seconds && (
                    <div className="flex items-center gap-2">
                      <Clock className="w-4 h-4" />
                      <span className="body-small">{formatDuration(session.duration_seconds)}</span>
                    </div>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span className="badge bg-[hsl(var(--card))] border border-[hsl(var(--border))] text-text-secondary shadow-sm font-medium">
                  {getTypeLabel(session.interview_type)}
                </span>
                <span className="badge bg-[hsl(var(--card))] border border-[hsl(var(--border))] text-text-secondary shadow-sm font-medium">
                  {session.question_count} questions
                </span>
              </div>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="card p-4 mb-8 border-status-error bg-status-error/10 animate-fade-in">
              <p className="text-status-error font-medium flex items-center gap-2">
                <AlertTriangle className="w-5 h-5" />
                {error}
              </p>
            </div>
          )}

          {/* Processing Status */}
          {session.status === 'completed' && !hasFeedback && id && (
            <ProcessingStatus
              sessionId={id}
              onComplete={() => {
                setProcessingComplete(true);
                loadFeedback();
              }}
              onStuck={() => {
                // When stuck in generating_feedback state, show the generate button
                setProcessingComplete(true);
              }}
              checkFeedbackExists={async () => {
                // Directly check if feedback exists (bypassing status endpoint)
                try {
                  const feedbackRes = await feedbackAPI.getBySessionId(id);
                  return feedbackRes.data !== null;
                } catch {
                  return false;
                }
              }}
            />
          )}

          {/* No Responses State */}
          {!hasFeedback && responses.length === 0 && (
            <Card className="p-12 mb-8 text-center animate-scale-in">
              <div className="w-20 h-20 rounded-full bg-amber-500/10 flex items-center justify-center mx-auto mb-6">
                <MessageSquare className="w-10 h-10 text-amber-500" />
              </div>
              <h2 className="text-xl font-semibold mb-4 text-text-primary">No Responses Recorded</h2>
              <p className="text-text-secondary mb-8 max-w-2xl mx-auto">
                This interview session doesn't have any recorded answers yet.
                Complete the interview to get AI-powered feedback on your performance.
              </p>
              <Link
                to="/dashboard"
                className="btn-primary inline-flex items-center gap-2 px-8 py-3 shadow-lg hover:shadow-electric-blue/30 transition-all"
              >
                <ArrowLeft className="w-5 h-5" />
                Back to Dashboard
              </Link>
            </Card>
          )}

          {/* Generate Feedback Call-to-Action - only show when transcription is complete */}
          {!hasFeedback && responses.length > 0 && processingComplete && (
            <Card className="p-12 mb-8 text-center animate-scale-in">
              <div className="w-20 h-20 rounded-full bg-electric-blue/10 flex items-center justify-center mx-auto mb-6">
                <Sparkles className="w-10 h-10 text-electric-blue" />
              </div>
              <h2 className="text-xl font-semibold mb-4 text-text-primary">Ready for Analysis</h2>
              <p className="text-text-secondary mb-8 max-w-2xl mx-auto">
                Your interview responses have been recorded. Generate AI-powered feedback
                to get detailed insights on your performance, strengths, and areas for improvement.
              </p>
              <button
                onClick={handleGenerateFeedback}
                disabled={generating}
                className="btn-primary inline-flex items-center gap-2 px-8 py-3 shadow-lg hover:shadow-electric-blue/30 transition-all"
              >
                {generating ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Generating Feedback...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-5 h-5" />
                    Generate Feedback
                  </>
                )}
              </button>
            </Card>
          )}

          {/* Feedback Content */}
          {hasFeedback && (
            <div className="animate-slide-up space-y-8">
              {/* Overall Score Hero */}
              <Card ref={heroRef} className="p-8 sm:p-12 text-center relative overflow-hidden">
                <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-electric-blue to-indigo-500"></div>

                <h2 className="text-xl font-semibold mb-2 text-text-primary">Overall Performance</h2>
                {user?.experience_level && (
                  <p className="text-sm text-electric-blue font-medium mb-8 bg-electric-blue/10 inline-block px-4 py-1 rounded-full border border-electric-blue/20">
                    Feedback tailored for {experienceLevelLabels[user.experience_level] || 'Mid-Level Engineers'}
                  </p>
                )}

                <div className="flex justify-center mb-8 relative z-10">
                  <div className="bg-[hsl(var(--muted)/0.3)] rounded-full p-6 border border-[hsl(var(--border))]">
                    <ScoreRing score={sessionFeedback.overall_score} size="large" />
                  </div>
                </div>

                <p className="text-text-secondary max-w-2xl mx-auto">
                  You completed <span className="font-semibold text-text-primary">{responses.length}</span> question{responses.length !== 1 ? 's' : ''}.
                </p>

                {/* Improvement Banner */}
                {comparison && comparison.sessions_compared > 0 && comparison.improvement_percent !== null && (
                  <div className={`inline-flex items-center gap-2 mt-6 px-5 py-2.5 rounded-full border ${comparison.improvement_percent > 0
                      ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-600 dark:text-emerald-400'
                      : comparison.improvement_percent < 0
                        ? 'bg-rose-500/10 border-rose-500/20 text-rose-600 dark:text-rose-400'
                        : 'bg-slate-500/10 border-slate-500/20 text-slate-600 dark:text-slate-400'
                    }`}>
                    {comparison.improvement_percent > 0 ? (
                      <TrendingUp className="w-4 h-4" />
                    ) : comparison.improvement_percent < 0 ? (
                      <TrendingDown className="w-4 h-4" />
                    ) : (
                      <Minus className="w-4 h-4" />
                    )}
                    <span className="text-sm font-semibold">
                      {comparison.improvement_percent > 0 ? '+' : ''}
                      {comparison.improvement_percent}% vs your average ({comparison.average_score})
                    </span>
                  </div>
                )}
              </Card>

              {/* Score Breakdown */}
              <div>
                <h2 className="text-lg font-semibold mb-6 flex items-center gap-2 text-text-primary">
                  <BarChart className="w-5 h-5 text-electric-blue" />
                  Score Breakdown
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <MetricCard
                    title="Content Score"
                    score={sessionFeedback.content_score}
                    description="Technical accuracy and completeness of your responses"
                    icon={BookOpen}
                  />
                  <MetricCard
                    title="Audio Score"
                    score={sessionFeedback.audio_score}
                    description="Speech clarity, pacing, and delivery quality"
                    icon={MessageSquare}
                  />
                  <MetricCard
                    title="Overall"
                    score={sessionFeedback.overall_score}
                    description="Combined performance across all metrics"
                    icon={Smile}
                  />
                </div>
              </div>

              {/* Top Strengths & Improvements */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {sessionFeedback.top_strengths.length > 0 && (
                  <Card className="p-6 border-t-4 border-t-emerald-500">
                    <h3 className="font-semibold text-emerald-600 dark:text-emerald-400 mb-6 flex items-center gap-2">
                      <CheckCircle2 className="w-5 h-5" />
                      Top Strengths
                    </h3>
                    <ul className="space-y-3">
                      {sessionFeedback.top_strengths.map((strength, idx) => (
                        <li key={idx} className="flex items-start gap-3 p-3 rounded-lg bg-emerald-500/5 dark:bg-emerald-500/10 border border-emerald-500/10 dark:border-emerald-500/20">
                          <span className="text-emerald-500 mt-0.5">•</span>
                          <span className="text-sm text-text-secondary">{strength}</span>
                        </li>
                      ))}
                    </ul>
                  </Card>
                )}

                {sessionFeedback.top_improvements.length > 0 && (
                  <Card className="p-6 border-t-4 border-t-amber-500">
                    <h3 className="font-semibold text-amber-600 dark:text-amber-400 mb-6 flex items-center gap-2">
                      <TrendingUp className="w-5 h-5" />
                      Areas for Improvement
                    </h3>
                    <ul className="space-y-3">
                      {sessionFeedback.top_improvements.map((improvement, idx) => (
                        <li key={idx} className="flex items-start gap-3 p-3 rounded-lg bg-amber-500/5 dark:bg-amber-500/10 border border-amber-500/10 dark:border-amber-500/20">
                          <span className="text-amber-500 mt-0.5">•</span>
                          <span className="text-sm text-text-secondary">{improvement}</span>
                        </li>
                      ))}
                    </ul>
                  </Card>
                )}
              </div>

              {/* Recommended Practice Areas */}
              {sessionFeedback.recommended_practice_areas.length > 0 && (
                <Card className="p-6">
                  <h3 className="font-semibold mb-4 flex items-center gap-2 text-text-primary">
                    <Sparkles className="w-5 h-5 text-electric-blue" />
                    Recommended Practice Areas
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {sessionFeedback.recommended_practice_areas.map((area, idx) => (
                      <span key={idx} className="badge bg-[hsl(var(--muted)/0.5)] border border-electric-blue/20 px-4 py-2 text-sm text-text-secondary hover:border-electric-blue/50 transition-colors cursor-default">
                        {area}
                      </span>
                    ))}
                  </div>
                </Card>
              )}

              {/* Questions & Responses */}
              {responses.length > 0 && (
                <div>
                  <h2 className="text-lg font-semibold mb-6 text-text-primary">Question-by-Question Analysis</h2>
                  <div className="space-y-4">
                    {responses.map((response, idx) => {
                      const contentFeedback = contentFeedbacks[idx];
                      return (
                        <ResponseAccordion
                          key={response.id}
                          questionNumber={idx + 1}
                          question={response.question?.content || 'Question text unavailable'}
                          transcript={response.transcript}
                          audioUrl={response.audio_url}
                          feedback={contentFeedback?.detailed_feedback || 'Feedback analysis pending...'}
                          score={contentFeedback?.overall_content_score}
                          suggestions={contentFeedback?.improvements || []}
                          sampleAnswer={response.question?.sample_answer}
                        />
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Action Section */}
              <Card className="p-8 text-center">
                <h2 className="text-xl font-semibold mb-4 text-text-primary">What's Next?</h2>
                <p className="text-text-secondary mb-8">
                  Continue improving your skills with more practice sessions
                </p>
                <div className="flex flex-col sm:flex-row gap-4 justify-center">
                  <button
                    onClick={() => navigate('/dashboard')}
                    className="btn-primary inline-flex items-center justify-center gap-2 shadow-lg hover:shadow-electric-blue/25"
                  >
                    <RefreshCw className="w-5 h-5" />
                    Practice Again
                  </button>
                  <button
                    onClick={() => navigate('/dashboard')}
                    className="btn-secondary inline-flex items-center justify-center gap-2"
                  >
                    Try Different Type
                  </button>
                </div>
              </Card>
            </div>
          )}
        </div>
      </div>

      {/* Sticky Practice Again Bar - Mobile only */}
      {hasFeedback && (
        <div
          className={`fixed bottom-16 inset-x-0 z-30 md:hidden transition-transform duration-300 ease-out ${
            showStickyBar && scrollDirection !== 'down' ? 'translate-y-0' : 'translate-y-full'
          }`}
        >
          <div className="bg-surface-primary/95 backdrop-blur-sm border-t border-border-light px-4 py-3 safe-area-bottom">
            <button
              onClick={() => navigate('/dashboard')}
              className="w-full btn-primary flex items-center justify-center gap-2 py-3"
            >
              <RefreshCw className="w-4 h-4" />
              Practice Again
            </button>
          </div>
        </div>
      )}
    </ErrorBoundary>
  );
}
