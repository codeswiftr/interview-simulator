import { useEffect, useState } from 'react';
import { videoAPI, type VideoFeedbackRead } from '../../lib/api';
import { Skeleton } from '../ui/Skeleton';

interface VideoFeedbackCardProps {
  responseId: string;
  className?: string;
}

// Derive a color class from a 0–1 score for the progress bar fill
function getEngagementColor(score: number): string {
  if (score >= 0.9) return 'bg-emerald-500';
  if (score >= 0.8) return 'bg-green-500';
  if (score >= 0.7) return 'bg-yellow-500';
  if (score >= 0.6) return 'bg-orange-500';
  return 'bg-red-500';
}

// Derive the SVG stroke color for the circular eye-contact indicator
function getEyeContactColor(pct: number): string {
  if (pct >= 80) return '#059669'; // emerald-600
  if (pct >= 65) return '#16a34a'; // green-600
  if (pct >= 50) return '#ca8a04'; // yellow-600
  if (pct >= 35) return '#ea580c'; // orange-600
  return '#dc2626';                 // red-600
}

function EyeContactRing({ percentage }: { percentage: number }) {
  const size = 80;
  const strokeWidth = 7;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (percentage / 100) * circumference;
  const color = getEyeContactColor(percentage);

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="transform -rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth={strokeWidth}
          className="text-surface-secondary"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          style={{ transition: 'stroke-dashoffset 0.6s ease-out' }}
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="text-xs font-bold tabular-nums" style={{ color }}>
          {Math.round(percentage)}%
        </span>
      </div>
    </div>
  );
}

function VideoFeedbackCardSkeleton({ className = '' }: { className?: string }) {
  return (
    <div
      className={`card p-5 dark:bg-surface-secondary/40 dark:border-white/5 ${className}`}
      aria-busy="true"
      aria-label="Loading video feedback"
    >
      <Skeleton variant="text" width="40%" height={16} className="mb-4" />
      <div className="flex gap-6 items-center">
        <div className="flex-1">
          <Skeleton variant="text" width="30%" height={12} className="mb-2" />
          <Skeleton variant="rectangular" height={10} className="rounded-full mb-1" />
          <Skeleton variant="text" width="20%" height={12} />
        </div>
        <div className="flex flex-col items-center gap-1 shrink-0">
          <Skeleton variant="circular" width={80} height={80} />
          <Skeleton variant="text" width={60} height={12} className="mt-1" />
        </div>
      </div>
    </div>
  );
}

export default function VideoFeedbackCard({ responseId, className = '' }: VideoFeedbackCardProps) {
  const [feedback, setFeedback] = useState<VideoFeedbackRead | null | undefined>(undefined);

  useEffect(() => {
    let cancelled = false;

    videoAPI.getVideoFeedback(responseId).then((data) => {
      if (!cancelled) setFeedback(data);
    }).catch(() => {
      if (!cancelled) setFeedback(null);
    });

    return () => { cancelled = true; };
  }, [responseId]);

  // Loading state
  if (feedback === undefined) {
    return <VideoFeedbackCardSkeleton className={className} />;
  }

  // Feature flag off (404) or error — render nothing
  if (feedback === null) {
    return null;
  }

  const engagementPct = Math.round(feedback.engagement_score * 100);
  const engagementColor = getEngagementColor(feedback.engagement_score);

  return (
    <div
      className={`card p-5 dark:bg-surface-secondary/40 dark:border-white/5 ${className}`}
      aria-label="Video feedback"
    >
      <h3 className="heading-card mb-4 text-text-primary dark:text-white">Video Analysis</h3>

      <div className="flex gap-6 items-center">
        {/* Engagement score — horizontal progress bar */}
        <div className="flex-1">
          <div className="flex items-center justify-between mb-1">
            <span className="body-small text-text-secondary">Engagement</span>
            <span className="body-small font-semibold text-text-primary dark:text-white tabular-nums">
              {engagementPct}%
            </span>
          </div>
          <div
            className="w-full h-2.5 bg-surface-secondary rounded-full overflow-hidden"
            role="progressbar"
            aria-label="Engagement score"
            aria-valuenow={engagementPct}
            aria-valuemin={0}
            aria-valuemax={100}
          >
            <div
              className={`h-full rounded-full transition-all duration-700 ${engagementColor}`}
              style={{ width: `${engagementPct}%` }}
            />
          </div>
        </div>

        {/* Eye contact — circular indicator */}
        <div className="flex flex-col items-center gap-1 shrink-0">
          <EyeContactRing percentage={feedback.eye_contact_percentage} />
          <span className="body-small text-text-secondary text-center whitespace-nowrap">
            Eye Contact
          </span>
        </div>
      </div>
    </div>
  );
}
