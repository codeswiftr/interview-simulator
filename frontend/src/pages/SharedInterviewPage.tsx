import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  ArrowLeft,
  BookOpen,
  MessageSquare,
  Smile,
  Calendar,
  User,
  AlertTriangle,
} from 'lucide-react';
import { Card } from '../components/ui/Card';
import ScoreRing from '../components/feedback/ScoreRing';
import MetricCard from '../components/feedback/MetricCard';
import ResponseAccordion from '../components/feedback/ResponseAccordion';
import { Skeleton, SkeletonScoreRing, SkeletonText } from '../components/ui/Skeleton';
import { interviewsAPI } from '../lib/api';

interface SharedInterview {
  interview_type: string;
  overall_score: number | null;
  audio_score: number | null;
  content_score: number | null;
  question_count: number;
  created_at: string;
  shared_by: string;
  responses: Array<{
    question: string;
    transcript: string | null;
    audio_url: string | null;
    overall_content_score: number | null;
    strengths: string[];
    improvements: string[];
    detailed_feedback: string | null;
  }>;
}

const interviewTypeLabels: Record<string, string> = {
  behavioral: 'Behavioral',
  technical: 'Technical',
  system_design: 'System Design',
  mixed: 'Mixed',
};

export default function SharedInterviewPage() {
  const { token } = useParams<{ token: string }>();
  const [interview, setInterview] = useState<SharedInterview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadSharedInterview = async () => {
      if (!token) {
        setError('Invalid share link');
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        const response = await interviewsAPI.getSharedInterview(token);
        setInterview(response.data);
      } catch (err) {
        console.error('Error loading shared interview:', err);
        const axiosError = err as { response?: { status?: number; data?: { detail?: string } } };
        const status = axiosError.response?.status;
        const detail = axiosError.response?.data?.detail;

        if (status === 404) {
          setError('This share link is invalid or has expired.');
        } else if (detail) {
          setError(detail);
        } else {
          setError('Failed to load shared interview. Please try again.');
        }
      } finally {
        setLoading(false);
      }
    };

    loadSharedInterview();
  }, [token]);

  const formatDate = (dateString: string) => {
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
      <div className="min-h-screen bg-surface-primary">
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
      </div>
    );
  }

  if (error || !interview) {
    return (
      <div className="min-h-screen bg-surface-primary flex items-center justify-center">
        <Card className="text-center p-8 border-status-error/20 bg-status-error/5 max-w-md mx-4">
          <AlertTriangle className="w-12 h-12 text-status-error mx-auto mb-4" />
          <h2 className="text-xl font-semibold mb-2 text-text-primary">Link Not Available</h2>
          <p className="text-text-secondary mb-6">{error}</p>
          <Link to="/" className="btn-primary inline-block">
            Go to Homepage
          </Link>
        </Card>
      </div>
    );
  }

  const hasScores = interview.overall_score !== null;

  return (
    <div className="min-h-screen bg-surface-primary dark:bg-surface-primary pb-12 transition-colors duration-300">
      {/* Background decoration */}
      <div className="fixed top-0 left-0 w-full h-full overflow-hidden pointer-events-none z-0">
        <div className="absolute top-[-10%] right-[-10%] w-[600px] h-[600px] rounded-full bg-electric-blue/5 dark:bg-electric-blue/10 blur-[100px]" />
        <div className="absolute bottom-[-10%] left-[-10%] w-[500px] h-[500px] rounded-full bg-indigo-500/5 dark:bg-indigo-500/10 blur-[100px]" />
      </div>

      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 relative z-10">
        {/* Header */}
        <div className="mb-8">
          <Link
            to="/"
            className="inline-flex items-center gap-2 text-text-secondary hover:text-electric-blue transition-colors mb-6 group"
          >
            <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
            <span className="body-default font-medium">Visit CodeSwiftr</span>
          </Link>

          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <h1 className="heading-page mb-2 text-[var(--fg-primary)]">Shared Interview Results</h1>
              <div className="flex items-center gap-4 text-text-secondary dark:text-text-tertiary">
                <div className="flex items-center gap-2">
                  <User className="w-4 h-4" />
                  <span className="body-small">Shared by {interview.shared_by}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Calendar className="w-4 h-4" />
                  <span className="body-small">{formatDate(interview.created_at)}</span>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <span className="badge bg-[hsl(var(--card))] border border-[hsl(var(--border))] text-text-secondary shadow-sm font-medium">
                {getTypeLabel(interview.interview_type)}
              </span>
              <span className="badge bg-[hsl(var(--card))] border border-[hsl(var(--border))] text-text-secondary shadow-sm font-medium">
                {interview.question_count} questions
              </span>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="space-y-8">
          {/* Overall Score (if available) */}
          {hasScores && (
            <>
              <Card className="p-8 sm:p-12 text-center relative overflow-hidden">
                <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-electric-blue to-indigo-500"></div>

                <h2 className="text-xl font-semibold mb-8 text-text-primary">Overall Performance</h2>

                <div className="flex justify-center mb-8 relative z-10">
                  <div className="bg-[hsl(var(--muted)/0.3)] rounded-full p-6 border border-[hsl(var(--border))]">
                    <ScoreRing score={interview.overall_score!} size="large" />
                  </div>
                </div>

                <p className="text-text-secondary">
                  Completed <span className="font-semibold text-text-primary">{interview.responses.length}</span> question{interview.responses.length !== 1 ? 's' : ''}
                </p>
              </Card>

              {/* Score Breakdown */}
              {interview.audio_score !== null && interview.content_score !== null && (
                <div>
                  <h2 className="text-lg font-semibold mb-6 text-text-primary">Score Breakdown</h2>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <MetricCard
                      title="Content Score"
                      score={interview.content_score}
                      description="Technical accuracy and completeness"
                      icon={BookOpen}
                    />
                    <MetricCard
                      title="Audio Score"
                      score={interview.audio_score}
                      description="Speech clarity and delivery quality"
                      icon={MessageSquare}
                    />
                    <MetricCard
                      title="Overall"
                      score={interview.overall_score!}
                      description="Combined performance"
                      icon={Smile}
                    />
                  </div>
                </div>
              )}
            </>
          )}

          {/* Questions & Responses */}
          {interview.responses.length > 0 && (
            <div>
              <h2 className="text-lg font-semibold mb-6 text-text-primary">
                Question-by-Question Analysis
              </h2>
              <div className="space-y-4">
                {interview.responses.map((response, idx) => (
                  <ResponseAccordion
                    key={idx}
                    questionNumber={idx + 1}
                    question={response.question}
                    transcript={response.transcript ?? undefined}
                    audioUrl={response.audio_url ?? undefined}
                    feedback={response.detailed_feedback ?? 'No feedback available'}
                    score={response.overall_content_score ?? undefined}
                    suggestions={response.improvements}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Call to Action */}
          <Card className="p-8 text-center bg-gradient-to-br from-electric-blue/5 to-indigo-500/5 border-electric-blue/20">
            <h2 className="text-xl font-semibold mb-4 text-text-primary">
              Want to practice your interview skills?
            </h2>
            <p className="text-text-secondary mb-6">
              Join CodeSwiftr to practice with AI-powered feedback and improve your performance
            </p>
            <Link
              to="/"
              className="btn-primary inline-flex items-center gap-2 shadow-lg hover:shadow-electric-blue/30 transition-all"
            >
              Get Started Free
            </Link>
          </Card>
        </div>
      </div>
    </div>
  );
}
