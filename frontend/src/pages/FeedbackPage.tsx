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
} from 'lucide-react';
import ScoreRing from '../components/feedback/ScoreRing';
import MetricCard from '../components/feedback/MetricCard';
import ResponseAccordion from '../components/feedback/ResponseAccordion';
import { feedbackAPI, interviewsAPI, responsesAPI } from '../lib/api';
import type { InterviewSession, InterviewResponse, Feedback } from '../types';

interface FeedbackData {
  session: InterviewSession;
  responses: Array<InterviewResponse & { feedback?: Feedback }>;
  overallScore: number;
  contentScore: number;
  communicationScore: number;
  confidenceScore: number;
}

// Mock feedback data generator
const generateMockFeedback = (sessionId: string): FeedbackData => {
  const baseScore = 75 + Math.floor(Math.random() * 20); // 75-95

  return {
    session: {
      id: sessionId,
      user_id: 'mock-user',
      category: 'behavioral',
      difficulty: 'medium',
      status: 'completed',
      total_questions: 3,
      completed_questions: 3,
      overall_score: baseScore,
      started_at: new Date(Date.now() - 1800000).toISOString(),
      completed_at: new Date().toISOString(),
      created_at: new Date(Date.now() - 1800000).toISOString(),
      updated_at: new Date().toISOString(),
    },
    responses: [
      {
        id: '1',
        session_id: sessionId,
        question_id: '1',
        audio_url: '',
        transcription: 'In my previous role, I faced a challenging situation where...',
        submitted_at: new Date().toISOString(),
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        question: {
          id: '1',
          category: 'behavioral',
          difficulty: 'medium',
          question_text: 'Tell me about a time when you had to deal with a difficult stakeholder.',
          evaluation_criteria: ['Communication', 'Problem-solving', 'Emotional intelligence'],
          expected_duration_seconds: 300,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
        feedback: {
          id: 'f1',
          response_id: '1',
          overall_score: baseScore - 2,
          content_score: baseScore,
          delivery_score: baseScore - 5,
          structure_score: baseScore + 3,
          communication_clarity_score: baseScore - 1,
          strengths: ['Clear structure', 'Good example selection'],
          weaknesses: ['Could provide more specific metrics'],
          improvement_suggestions: [
            'Include quantifiable results from your actions',
            'Elaborate on the stakeholder\'s perspective',
          ],
          detailed_analysis: 'Strong response with clear STAR structure. Consider adding more specific outcomes.',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
      },
      {
        id: '2',
        session_id: sessionId,
        question_id: '2',
        audio_url: '',
        transcription: 'My approach to leadership involves...',
        submitted_at: new Date().toISOString(),
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        question: {
          id: '2',
          category: 'behavioral',
          difficulty: 'medium',
          question_text: 'Describe your leadership style and provide an example.',
          evaluation_criteria: ['Leadership', 'Self-awareness', 'Impact'],
          expected_duration_seconds: 300,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
        feedback: {
          id: 'f2',
          response_id: '2',
          overall_score: baseScore + 2,
          content_score: baseScore + 5,
          delivery_score: baseScore,
          structure_score: baseScore + 1,
          communication_clarity_score: baseScore + 3,
          strengths: ['Authentic leadership style', 'Concrete example'],
          weaknesses: ['Pacing could be improved'],
          improvement_suggestions: [
            'Practice varying your speaking pace',
            'Add more details about team impact',
          ],
          detailed_analysis: 'Excellent self-awareness and authentic presentation. Great concrete example.',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
      },
      {
        id: '3',
        session_id: sessionId,
        question_id: '3',
        audio_url: '',
        transcription: 'When faced with conflicting priorities, I...',
        submitted_at: new Date().toISOString(),
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        question: {
          id: '3',
          category: 'behavioral',
          difficulty: 'medium',
          question_text: 'How do you handle conflicting priorities?',
          evaluation_criteria: ['Time management', 'Decision making', 'Communication'],
          expected_duration_seconds: 300,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
        feedback: {
          id: 'f3',
          response_id: '3',
          overall_score: baseScore,
          content_score: baseScore - 3,
          delivery_score: baseScore + 2,
          structure_score: baseScore,
          communication_clarity_score: baseScore + 1,
          strengths: ['Clear decision-making framework', 'Good confidence'],
          weaknesses: ['Example could be more specific'],
          improvement_suggestions: [
            'Provide a more detailed real-world scenario',
            'Discuss how you communicated with stakeholders',
          ],
          detailed_analysis: 'Good framework explanation. Would benefit from a more detailed example.',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
      },
    ],
    overallScore: baseScore,
    contentScore: baseScore + 1,
    communicationScore: baseScore - 2,
    confidenceScore: baseScore + 3,
  };
};

export default function FeedbackPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [feedbackData, setFeedbackData] = useState<FeedbackData | null>(null);

  useEffect(() => {
    const loadFeedback = async () => {
      if (!id) return;

      try {
        setLoading(true);
        setError(null);

        // Try to fetch real data
        try {
          const [sessionRes, responsesRes] = await Promise.all([
            interviewsAPI.getById(id),
            responsesAPI.getBySessionId(id),
          ]);

          const session = sessionRes.data;
          const responses = responsesRes.data;

          // Try to fetch feedback for each response
          const responsesWithFeedback = await Promise.all(
            responses.map(async (response: InterviewResponse) => {
              try {
                const feedbackRes = await feedbackAPI.getByResponseId(response.id);
                return { ...response, feedback: feedbackRes.data };
              } catch {
                // If no feedback yet, return response without feedback
                return response;
              }
            })
          );

          // Calculate average scores if feedback exists
          const feedbackScores = responsesWithFeedback
            .filter((r) => r.feedback)
            .map((r) => r.feedback!);

          if (feedbackScores.length > 0) {
            const avgOverall =
              feedbackScores.reduce((sum, f) => sum + f.overall_score, 0) /
              feedbackScores.length;
            const avgContent =
              feedbackScores.reduce((sum, f) => sum + f.content_score, 0) /
              feedbackScores.length;
            const avgCommunication =
              feedbackScores.reduce((sum, f) => sum + f.communication_clarity_score, 0) /
              feedbackScores.length;

            setFeedbackData({
              session,
              responses: responsesWithFeedback,
              overallScore: Math.round(avgOverall),
              contentScore: Math.round(avgContent),
              communicationScore: Math.round(avgCommunication),
              confidenceScore: Math.round(avgOverall + 5), // Placeholder
            });
          } else {
            // No feedback yet, use mock data
            setFeedbackData(generateMockFeedback(id));
          }
        } catch (apiError) {
          // If API fails, use mock data
          console.warn('API fetch failed, using mock data:', apiError);
          setFeedbackData(generateMockFeedback(id));
        }
      } catch (err) {
        setError('Failed to load feedback data');
        console.error('Error loading feedback:', err);
      } finally {
        setLoading(false);
      }
    };

    loadFeedback();
  }, [id]);

  const formatDuration = (startedAt?: string, completedAt?: string) => {
    if (!startedAt || !completedAt) return 'N/A';
    const duration = new Date(completedAt).getTime() - new Date(startedAt).getTime();
    const minutes = Math.floor(duration / 60000);
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

  const getCategoryLabel = (category: string) => {
    return category
      .split('_')
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'easy':
        return 'badge-completed';
      case 'medium':
        return 'badge-in-progress';
      case 'hard':
        return 'badge-scheduled';
      default:
        return 'badge';
    }
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

  if (error || !feedbackData) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="body-large text-status-error mb-4">{error || 'No feedback data found'}</p>
          <button onClick={() => navigate('/dashboard')} className="btn-primary">
            Return to Dashboard
          </button>
        </div>
      </div>
    );
  }

  const { session, responses, overallScore, contentScore, communicationScore, confidenceScore } =
    feedbackData;

  return (
    <div className="min-h-screen bg-surface-primary py-8">
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
                  <span className="body-small">{formatDate(session.completed_at)}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Clock className="w-4 h-4" />
                  <span className="body-small">
                    {formatDuration(session.started_at, session.completed_at)}
                  </span>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <span className={`badge ${getDifficultyColor(session.difficulty)}`}>
                {getCategoryLabel(session.category)}
              </span>
              <span className="badge badge-completed">{session.difficulty}</span>
            </div>
          </div>
        </div>

        {/* Overall Score Hero */}
        <div className="card-glass p-8 sm:p-12 mb-8 text-center">
          <h2 className="heading-section mb-6">Overall Performance</h2>
          <ScoreRing score={overallScore} size="large" />
          <p className="body-large text-text-secondary mt-6 max-w-2xl mx-auto">
            You completed {session.completed_questions} of {session.total_questions} questions with
            strong performance across all areas.
          </p>
        </div>

        {/* Score Breakdown */}
        <div className="mb-8">
          <h2 className="heading-section mb-6">Score Breakdown</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <MetricCard
              title="Content Score"
              score={contentScore}
              description="Technical accuracy and completeness of your responses"
              icon={BookOpen}
            />
            <MetricCard
              title="Communication"
              score={communicationScore}
              description="Clarity, structure, and articulation of ideas"
              icon={MessageSquare}
            />
            <MetricCard
              title="Confidence"
              score={confidenceScore}
              description="Speaking pace and delivery (placeholder metric)"
              icon={Smile}
            />
          </div>
        </div>

        {/* Questions & Responses */}
        <div className="mb-8">
          <h2 className="heading-section mb-6">Question-by-Question Analysis</h2>
          <div className="space-y-4">
            {responses.map((response, idx) => (
              <ResponseAccordion
                key={response.id}
                questionNumber={idx + 1}
                question={response.question?.question_text || 'Question text unavailable'}
                transcript={response.transcription}
                feedback={
                  response.feedback?.detailed_analysis || 'Feedback analysis is being generated...'
                }
                score={response.feedback?.overall_score}
                suggestions={response.feedback?.improvement_suggestions || []}
              />
            ))}
          </div>
        </div>

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
  );
}
