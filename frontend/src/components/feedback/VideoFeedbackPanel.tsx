import { Eye, Smile, AlertCircle, MoveHorizontal, Hand, Video } from 'lucide-react';
import ScoreRing from './ScoreRing';
import { Card } from '../ui/Card';
import { Skeleton } from '../ui/Skeleton';

export interface VideoFeedbackData {
  confidence_score: number;
  nervousness_score: number;
  engagement_score: number;
  eye_contact_percentage: number;
  looking_away_count: number;
  fidget_count: number | null;
  hand_gesture_frequency: number | null;
  processing_duration_ms: number;
  frame_count: number;
}

interface VideoFeedbackPanelProps {
  responseId: string;
  videoFeedback?: VideoFeedbackData | null;
  isLoading?: boolean;
}

/**
 * Get color based on score value
 */
const getScoreColor = (score: number): string => {
  if (score >= 60) return 'text-emerald-600 dark:text-emerald-400';
  if (score >= 40) return 'text-orange-600 dark:text-orange-400';
  return 'text-red-600 dark:text-red-400';
};

/**
 * Get progress bar color based on score (inverted for nervousness -> calmness)
 */
const getCalmnessColor = (calmnessScore: number): string => {
  if (calmnessScore >= 70) return 'bg-emerald-500';
  if (calmnessScore >= 40) return 'bg-orange-500';
  return 'bg-red-500';
};

/**
 * Get badge color for count-based metrics
 */
const getCountBadgeColor = (count: number, warningThreshold: number): string => {
  if (count < warningThreshold) return 'bg-slate-100 dark:bg-slate-700 text-text-secondary';
  return 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400';
};

/**
 * Get gesture frequency label
 */
const getGestureLabel = (frequency: number | null): string => {
  if (frequency === null) return 'N/A';
  if (frequency < 0.25) return 'Low';
  if (frequency < 0.5) return 'Moderate';
  if (frequency < 0.75) return 'High';
  return 'Very High';
};

/**
 * Get gesture color
 */
const getGestureColor = (frequency: number | null): string => {
  if (frequency === null) return 'text-text-tertiary';
  if (frequency < 0.5) return 'text-emerald-600 dark:text-emerald-400';
  if (frequency < 0.75) return 'text-orange-600 dark:text-orange-400';
  return 'text-red-600 dark:text-red-400';
};

/**
 * Loading skeleton for VideoFeedbackPanel
 */
function VideoFeedbackPanelSkeleton() {
  return (
    <Card className="p-6">
      <div className="flex items-center gap-3 mb-6">
        <Skeleton variant="circular" width={32} height={32} />
        <Skeleton variant="text" width={180} height={24} />
      </div>

      {/* Score Rings Skeleton */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        {[1, 2, 3].map((i) => (
          <div key={i} className="flex flex-col items-center">
            <Skeleton variant="circular" width={100} height={100} className="mb-3" />
            <Skeleton variant="text" width={60} height={14} />
          </div>
        ))}
      </div>

      {/* Calmness Bar Skeleton */}
      <div className="mb-6">
        <Skeleton variant="text" width={100} height={16} className="mb-2" />
        <Skeleton variant="rectangular" width="100%" height={24} className="rounded-full" />
      </div>

      {/* Detail Stats Skeleton */}
      <div className="grid grid-cols-3 gap-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="text-center p-4 bg-surface-secondary rounded-lg">
            <Skeleton variant="text" width={40} height={32} className="mx-auto mb-2" />
            <Skeleton variant="text" width={60} height={14} />
          </div>
        ))}
      </div>
    </Card>
  );
}

/**
 * Empty state for VideoFeedbackPanel
 */
function VideoFeedbackPanelEmpty() {
  return (
    <Card className="p-8 text-center">
      <div className="w-16 h-16 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center mx-auto mb-4">
        <Video className="w-8 h-8 text-text-tertiary" />
      </div>
      <h3 className="text-lg font-semibold text-text-primary mb-2">
        No Video Analysis Available
      </h3>
      <p className="text-sm text-text-secondary max-w-sm mx-auto">
        Video analysis results will appear here once your response has been processed.
      </p>
    </Card>
  );
}

/**
 * VideoFeedbackPanel displays video analysis metrics from the backend API
 */
export default function VideoFeedbackPanel({
  videoFeedback,
  isLoading = false,
}: VideoFeedbackPanelProps) {
  // Loading state
  if (isLoading) {
    return <VideoFeedbackPanelSkeleton />;
  }

  // Empty state
  if (!videoFeedback) {
    return <VideoFeedbackPanelEmpty />;
  }

  // Convert scores to percentages (0-1 scale to 0-100)
  const confidencePercent = Math.round(videoFeedback.confidence_score * 100);
  const engagementPercent = Math.round(videoFeedback.engagement_score * 100);
  const eyeContactPercent = Math.round(videoFeedback.eye_contact_percentage * 100);

  // Invert nervousness to show "Calmness" (higher is better)
  const calmnessPercent = Math.round((1 - videoFeedback.nervousness_score) * 100);

  return (
    <Card className="p-6">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 rounded-lg bg-electric-blue/10">
          <Video className="w-5 h-5 text-electric-blue" />
        </div>
        <h3 className="text-lg font-semibold text-text-primary">
          Video Analysis
        </h3>
      </div>

      {/* Main Score Rings - Desktop Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 mb-6">
        {/* Confidence */}
        <div className="flex flex-col items-center">
          <ScoreRing score={confidencePercent} size="medium" />
          <span className="mt-2 text-sm font-medium text-text-secondary">Confidence</span>
        </div>

        {/* Engagement */}
        <div className="flex flex-col items-center">
          <ScoreRing score={engagementPercent} size="medium" />
          <span className="mt-2 text-sm font-medium text-text-secondary">Engagement</span>
        </div>

        {/* Eye Contact */}
        <div className="flex flex-col items-center">
          <ScoreRing score={eyeContactPercent} size="medium" />
          <span className="mt-2 text-sm font-medium text-text-secondary">Eye Contact</span>
        </div>
      </div>

      {/* Calmness Progress Bar */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-text-secondary flex items-center gap-2">
            <Smile className="w-4 h-4" />
            Calmness
          </span>
          <span className={`text-sm font-semibold ${getScoreColor(calmnessPercent)}`}>
            {calmnessPercent}%
          </span>
        </div>
        <div className="w-full h-3 bg-surface-secondary dark:bg-slate-700 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ${getCalmnessColor(calmnessPercent)}`}
            style={{ width: `${calmnessPercent}%` }}
          />
        </div>
        {videoFeedback.nervousness_score > 0.6 && (
          <p className="mt-2 text-xs text-amber-600 dark:text-amber-400 flex items-center gap-1">
            <AlertCircle className="w-3 h-3" />
            High nervousness detected - try to stay calm and relaxed
          </p>
        )}
      </div>

      {/* Detail Stats */}
      <div className="grid grid-cols-3 gap-3">
        {/* Looking Away Count */}
        <div className="text-center p-3 bg-surface-secondary dark:bg-slate-800/50 rounded-lg">
          <div className="flex items-center justify-center gap-1.5 mb-1">
            <Eye className="w-4 h-4 text-text-tertiary" />
            <span className="text-xs text-text-tertiary">Looked Away</span>
          </div>
          <span className={`text-2xl font-bold ${getCountBadgeColor(videoFeedback.looking_away_count, 10)} px-3 py-1 rounded-full inline-block`}>
            {videoFeedback.looking_away_count}
          </span>
        </div>

        {/* Fidget Count */}
        <div className="text-center p-3 bg-surface-secondary dark:bg-slate-800/50 rounded-lg">
          <div className="flex items-center justify-center gap-1.5 mb-1">
            <MoveHorizontal className="w-4 h-4 text-text-tertiary" />
            <span className="text-xs text-text-tertiary">Fidgets</span>
          </div>
          <span className={`text-2xl font-bold ${getCountBadgeColor(videoFeedback.fidget_count ?? 0, 10)} px-3 py-1 rounded-full inline-block`}>
            {videoFeedback.fidget_count ?? 'N/A'}
          </span>
        </div>

        {/* Hand Gesture Frequency */}
        <div className="text-center p-3 bg-surface-secondary dark:bg-slate-800/50 rounded-lg">
          <div className="flex items-center justify-center gap-1.5 mb-1">
            <Hand className="w-4 h-4 text-text-tertiary" />
            <span className="text-xs text-text-tertiary">Gestures</span>
          </div>
          <span className={`text-lg font-bold ${getGestureColor(videoFeedback.hand_gesture_frequency)}`}>
            {getGestureLabel(videoFeedback.hand_gesture_frequency)}
          </span>
        </div>
      </div>

      {/* Processing Info */}
      {videoFeedback.processing_duration_ms && (
        <p className="mt-4 text-xs text-text-tertiary text-center">
          Analyzed {videoFeedback.frame_count} frames in {videoFeedback.processing_duration_ms}ms
        </p>
      )}
    </Card>
  );
}
