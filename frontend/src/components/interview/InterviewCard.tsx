import { FileText, Calendar } from 'lucide-react';
import type { InterviewSession } from '../../types';

interface InterviewCardProps {
  session: InterviewSession;
  onClick?: () => void;
}

const statusConfig = {
  scheduled: {
    label: 'Scheduled',
    className: 'badge-scheduled',
  },
  in_progress: {
    label: 'In Progress',
    className: 'badge-in-progress',
  },
  completed: {
    label: 'Completed',
    className: 'badge-completed',
  },
  cancelled: {
    label: 'Cancelled',
    className: 'badge badge-scheduled opacity-50',
  },
};

const categoryLabels = {
  behavioral: 'Behavioral',
  technical: 'Technical',
  system_design: 'System Design',
};

const difficultyLabels = {
  easy: 'Easy',
  medium: 'Medium',
  hard: 'Hard',
};

export default function InterviewCard({ session, onClick }: InterviewCardProps) {
  const statusInfo = statusConfig[session.status] || statusConfig.scheduled;
  const categoryLabel = categoryLabels[session.category as keyof typeof categoryLabels] || session.category;
  const difficultyLabel = difficultyLabels[session.difficulty as keyof typeof difficultyLabels] || session.difficulty;

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
    }).format(date);
  };

  return (
    <div
      className={`card-interactive p-6 ${onClick ? 'cursor-pointer' : ''}`}
      onClick={onClick}
    >
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="heading-card mb-2">{categoryLabel}</h3>
          <div className="flex items-center gap-2 text-sm text-text-secondary">
            <span className="label">{difficultyLabel}</span>
            <span className="text-text-tertiary">•</span>
            <span>{session.total_questions} questions</span>
          </div>
        </div>
        <div className={`badge ${statusInfo.className}`}>
          {statusInfo.label}
        </div>
      </div>

      <div className="flex items-center gap-4 text-sm text-text-secondary">
        <div className="flex items-center gap-1.5">
          <Calendar size={16} />
          <span>{formatDate(session.created_at)}</span>
        </div>

        {session.completed_questions > 0 && (
          <div className="flex items-center gap-1.5">
            <FileText size={16} />
            <span>
              {session.completed_questions}/{session.total_questions} completed
            </span>
          </div>
        )}

        {session.overall_score !== null && session.overall_score !== undefined && (
          <div className="flex items-center gap-1.5 text-electric-blue font-semibold">
            <span>Score: {Math.round(session.overall_score)}/100</span>
          </div>
        )}
      </div>

      {session.status === 'in_progress' && (
        <div className="mt-4">
          <div className="progress-bar">
            <div
              className="progress-bar-fill"
              style={{
                width: `${(session.completed_questions / session.total_questions) * 100}%`,
              }}
            />
          </div>
        </div>
      )}
    </div>
  );
}
