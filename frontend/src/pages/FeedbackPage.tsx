import { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  ArrowLeft,
  Share2,
  RefreshCw,
  BookOpen,
  MessageSquare,
  Smile,
  Calendar,
  Clock,
  Loader2,
  Sparkles,
} from 'lucide-react';
import { ErrorBoundary } from '../components/ErrorBoundary';
import ScoreRing from '../components/feedback/ScoreRing';
import MetricCard from '../components/feedback/MetricCard';
import ResponseAccordion from '../components/feedback/ResponseAccordion';
import ProcessingStatus from '../components/feedback/ProcessingStatus';
import { feedbackAPI, interviewsAPI, responsesAPI } from '../lib/api';
import type { InterviewSession, InterviewResponse, SessionFeedback, ContentFeedback } from '../types';

interface FeedbackState {
  session: InterviewSession | null;
  sessionFeedback: SessionFeedback | null;
  responses: InterviewResponse[];
  contentFeedbacks: ContentFeedback[];
}

const interviewTypeLabels: Record<string, string> = {
  behavioral: 'Behavioral',
  technical: 'Technical',
  system_design: 'System Design',
  mixed: 'Mixed',
};

export default function FeedbackPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [feedbackState, setFeedbackState] = useState<FeedbackState>({
    session: null,
    sessionFeedback: null,
    responses: [],
    contentFeedbacks: [],
  });

  const loadFeedback = async () => {
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

      setFeedbackState({
        session,
        sessionFeedback,
        responses,
        contentFeedbacks,
      });
    } catch (err) {
      setError('Failed to load interview data');
      console.error('Error loading feedback:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFeedback();
  }, [id]);

  const handleGenerateFeedback = async () => {
    if (!id) return;

    try {
      setGenerating(true);
      setError(null);

      await feedbackAPI.generateForSession(id);

      // Reload feedback data
      await loadFeedback();
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to generate feedback';
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
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-electric-blue border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="body-large text-text-secondary">Loading feedback...</p>
        </div>
      </div>
    );
  }

  if (error && !feedbackState.session) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="body-large text-status-error mb-4">{error}</p>
          <button onClick={() => navigate('/dashboard')} className="btn-primary">
            Return to Dashboard
          </button>
        </div>
      </div>
    );
  }

  const { session, sessionFeedback, responses, contentFeedbacks } = feedbackState;

  if (!session) {
    return (
      <div className="min-h-screen flex items-center justify-center">
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
      <div className="min-h-screen py-8">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <Link
            to="/dashboard"
            className="inline-flex items-center gap-2 text-electric-blue hover:text-electric-blue/80 transition-colors mb-4"
          >
            <ArrowLeft className="w-4 h-4" />
            <span className="body-default font-medium">Back to Dashboard</span>
          </Link>

          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <h1 className="heading-page mb-2">Interview Feedback</h1>
              <div className="flex items-center gap-4 text-text-secondary">
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
              <span className="badge badge-completed">
                {getTypeLabel(session.interview_type)}
              </span>
              <span className="badge badge-scheduled">
                {session.question_count} questions
              </span>
            </div>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="card p-4 mb-8 border-status-error bg-status-error/10">
            <p className="text-status-error">{error}</p>
          </div>
        )}

        {/* Processing Status - Show when session is completed but feedback not ready */}
        {session.status === 'completed' && !hasFeedback && id && (
          <ProcessingStatus
            sessionId={id}
            onComplete={() => {
              // Reload feedback when processing completes
              loadFeedback();
            }}
          />
        )}

        {/* No Feedback Yet - Show Generate Button */}
        {!hasFeedback && (
          <div className="card-glass p-8 sm:p-12 mb-8 text-center">
            <Sparkles className="w-16 h-16 text-electric-blue mx-auto mb-4" />
            <h2 className="heading-section mb-4">Generate AI Feedback</h2>
            <p className="body-large text-text-secondary mb-6 max-w-2xl mx-auto">
              Your interview responses are ready for analysis. Generate AI-powered feedback
              to get detailed insights on your performance.
            </p>
            <button
              onClick={handleGenerateFeedback}
              disabled={generating || responses.length === 0}
              className="btn-primary inline-flex items-center gap-2"
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
            {responses.length === 0 && (
              <p className="body-small text-text-tertiary mt-4">
                No responses found for this interview session.
              </p>
            )}
          </div>
        )}

        {/* Feedback Content */}
        {hasFeedback && (
          <>
            {/* Overall Score Hero */}
            <div className="card-glass p-8 sm:p-12 mb-8 text-center">
              <h2 className="heading-section mb-6">Overall Performance</h2>
              <ScoreRing score={sessionFeedback.overall_score} size="large" />
              <p className="body-large text-text-secondary mt-6 max-w-2xl mx-auto">
                You completed {responses.length} of {session.question_count} questions.
              </p>
            </div>

            {/* Score Breakdown */}
            <div className="mb-8">
              <h2 className="heading-section mb-6">Score Breakdown</h2>
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
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
              {sessionFeedback.top_strengths.length > 0 && (
                <div className="card p-6">
                  <h3 className="heading-card text-status-success mb-4">Top Strengths</h3>
                  <ul className="space-y-2">
                    {sessionFeedback.top_strengths.map((strength, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <span className="text-status-success">+</span>
                        <span className="body-default text-text-secondary">{strength}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {sessionFeedback.top_improvements.length > 0 && (
                <div className="card p-6">
                  <h3 className="heading-card text-status-warning mb-4">Areas for Improvement</h3>
                  <ul className="space-y-2">
                    {sessionFeedback.top_improvements.map((improvement, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <span className="text-status-warning">!</span>
                        <span className="body-default text-text-secondary">{improvement}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            {/* Recommended Practice Areas */}
            {sessionFeedback.recommended_practice_areas.length > 0 && (
              <div className="card p-6 mb-8">
                <h3 className="heading-card mb-4">Recommended Practice Areas</h3>
                <div className="flex flex-wrap gap-2">
                  {sessionFeedback.recommended_practice_areas.map((area, idx) => (
                    <span key={idx} className="badge badge-in-progress">
                      {area}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </>
        )}

        {/* Questions & Responses */}
        {responses.length > 0 && (
          <div className="mb-8">
            <h2 className="heading-section mb-6">Question-by-Question Analysis</h2>
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
                  />
                );
              })}
            </div>
          </div>
        )}

        {/* Action Section */}
        <div className="card p-8 text-center">
          <h2 className="heading-section mb-4">What's Next?</h2>
          <p className="body-default text-text-secondary mb-6">
            Continue improving your skills with more practice sessions
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button
              onClick={() => navigate('/dashboard')}
              className="btn-primary inline-flex items-center justify-center gap-2"
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
            <button className="btn-ghost inline-flex items-center justify-center gap-2" disabled>
              <Share2 className="w-5 h-5" />
              Share Results
              <span className="body-small text-text-tertiary">(Coming Soon)</span>
            </button>
          </div>
        </div>
      </div>
      </div>
    </ErrorBoundary>
  );
}
