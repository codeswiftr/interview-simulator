import { ChevronDown, ChevronUp, MessageSquare, BarChart2, Lightbulb, AlertCircle } from 'lucide-react';
import { useState } from 'react';
import AudioPlayer from './AudioPlayer';
import { cn } from '../../lib/utils';
import type { InterviewResponse, Question, ContentFeedback, Feedback } from '../../types';

interface ResponseReviewProps {
  response: InterviewResponse;
  question: Question;
  feedback?: ContentFeedback | Feedback | null;
  questionNumber: number;
  isExpanded?: boolean;
  onToggle?: () => void;
}

export default function ResponseReview({
  response,
  question,
  feedback,
  questionNumber,
  isExpanded = false,
  onToggle,
}: ResponseReviewProps) {
  const [showSampleAnswer, setShowSampleAnswer] = useState(false);

  // Normalize feedback structure (handle both ContentFeedback and Feedback types)
  const normalizedFeedback = feedback
    ? {
        overallScore: 'overall_content_score' in feedback
          ? feedback.overall_content_score
          : 'overall_score' in feedback
            ? feedback.overall_score
            : 0,
        strengths: 'strengths' in feedback ? feedback.strengths : [],
        improvements: 'improvements' in feedback
          ? feedback.improvements
          : 'weaknesses' in feedback
            ? feedback.weaknesses
            : [],
        detailedFeedback: 'detailed_feedback' in feedback
          ? feedback.detailed_feedback
          : 'detailed_analysis' in feedback
            ? feedback.detailed_analysis
            : '',
      }
    : null;

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-status-success';
    if (score >= 60) return 'text-yellow-500';
    return 'text-status-error';
  };

  return (
    <div className="card overflow-hidden">
      {/* Header - Clickable */}
      <button
        onClick={onToggle}
        className="w-full p-4 flex items-center justify-between hover:bg-surface-secondary transition-colors text-left"
      >
        <div className="flex items-center gap-4">
          <div className="w-8 h-8 rounded-full bg-electric-blue/10 text-electric-blue flex items-center justify-center font-semibold">
            {questionNumber}
          </div>
          <div className="flex-1">
            <h3 className="font-semibold text-text-primary line-clamp-1">
              {question.content}
            </h3>
            <div className="flex items-center gap-3 mt-1 text-sm text-text-secondary">
              <span className="badge badge-outline text-xs">
                {question.category.replace('_', ' ')}
              </span>
              {response.duration_seconds && (
                <span>{Math.floor(response.duration_seconds / 60)}:{(response.duration_seconds % 60).toString().padStart(2, '0')}</span>
              )}
              {normalizedFeedback && (
                <span className={cn('font-medium', getScoreColor(normalizedFeedback.overallScore))}>
                  {normalizedFeedback.overallScore.toFixed(0)}%
                </span>
              )}
            </div>
          </div>
        </div>
        {isExpanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
      </button>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="border-t border-border-light">
          {/* Audio Player */}
          {response.audio_url && (
            <div className="p-4 border-b border-border-light">
              <h4 className="text-sm font-medium text-text-secondary mb-3 flex items-center gap-2">
                <MessageSquare size={16} />
                Your Recording
              </h4>
              <AudioPlayer audioUrl={response.audio_url} />
            </div>
          )}

          {/* Transcript */}
          <div className="p-4 border-b border-border-light">
            <h4 className="text-sm font-medium text-text-secondary mb-3">Transcript</h4>
            {response.transcript ? (
              <div className="bg-surface-secondary rounded-lg p-4">
                <p className="text-text-primary whitespace-pre-wrap">{response.transcript}</p>
                {response.word_count && (
                  <p className="text-xs text-text-tertiary mt-2">
                    {response.word_count} words
                  </p>
                )}
              </div>
            ) : (
              <div className="bg-surface-secondary rounded-lg p-4 text-text-tertiary italic">
                Transcript not available
              </div>
            )}
          </div>

          {/* Sample Answer (if available) */}
          {question.sample_answer && (
            <div className="p-4 border-b border-border-light">
              <button
                onClick={() => setShowSampleAnswer(!showSampleAnswer)}
                className="text-sm font-medium text-electric-blue flex items-center gap-2 hover:underline"
              >
                <Lightbulb size={16} />
                {showSampleAnswer ? 'Hide' : 'Show'} Sample Answer
              </button>
              {showSampleAnswer && (
                <div className="mt-3 bg-electric-blue/5 border border-electric-blue/20 rounded-lg p-4">
                  <p className="text-text-primary whitespace-pre-wrap">{question.sample_answer}</p>
                </div>
              )}
            </div>
          )}

          {/* Feedback */}
          {normalizedFeedback && (
            <div className="p-4">
              <h4 className="text-sm font-medium text-text-secondary mb-3 flex items-center gap-2">
                <BarChart2 size={16} />
                AI Feedback
              </h4>

              {/* Score */}
              <div className="flex items-center gap-4 mb-4">
                <div className="text-center">
                  <div className={cn('text-3xl font-bold', getScoreColor(normalizedFeedback.overallScore))}>
                    {normalizedFeedback.overallScore.toFixed(0)}
                  </div>
                  <div className="text-xs text-text-tertiary">Score</div>
                </div>
              </div>

              {/* Strengths */}
              {normalizedFeedback.strengths.length > 0 && (
                <div className="mb-4">
                  <h5 className="text-sm font-medium text-status-success flex items-center gap-2 mb-2">
                    ✓ Strengths
                  </h5>
                  <ul className="space-y-1">
                    {normalizedFeedback.strengths.map((strength, idx) => (
                      <li key={idx} className="text-sm text-text-secondary pl-4 relative before:content-['•'] before:absolute before:left-0 before:text-status-success">
                        {strength}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Areas for Improvement */}
              {normalizedFeedback.improvements.length > 0 && (
                <div className="mb-4">
                  <h5 className="text-sm font-medium text-yellow-500 flex items-center gap-2 mb-2">
                    <AlertCircle size={14} />
                    Areas for Improvement
                  </h5>
                  <ul className="space-y-1">
                    {normalizedFeedback.improvements.map((improvement, idx) => (
                      <li key={idx} className="text-sm text-text-secondary pl-4 relative before:content-['•'] before:absolute before:left-0 before:text-yellow-500">
                        {improvement}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Detailed Feedback */}
              {normalizedFeedback.detailedFeedback && (
                <div className="bg-surface-secondary rounded-lg p-4">
                  <h5 className="text-sm font-medium text-text-secondary mb-2">Detailed Analysis</h5>
                  <p className="text-sm text-text-primary whitespace-pre-wrap">
                    {normalizedFeedback.detailedFeedback}
                  </p>
                </div>
              )}
            </div>
          )}

          {/* No Feedback Available */}
          {!normalizedFeedback && (
            <div className="p-4 text-center text-text-tertiary">
              <BarChart2 size={24} className="mx-auto mb-2 opacity-50" />
              <p className="text-sm">Feedback not yet available</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
