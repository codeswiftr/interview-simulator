import { Calendar, Building2 } from 'lucide-react';
import { Card, CardContent } from '../ui/Card';
import type { InterviewSession } from '../../types';

const companyLabels: Record<string, string> = {
  google: 'Google',
  amazon: 'Amazon',
  meta: 'Meta',
  microsoft: 'Microsoft',
  apple: 'Apple',
  netflix: 'Netflix',
  stripe: 'Stripe',
  uber: 'Uber',
  airbnb: 'Airbnb',
  linkedin: 'LinkedIn',
};

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
  analyzed: {
    label: 'Analyzed',
    className: 'badge-completed',
  },
  cancelled: {
    label: 'Cancelled',
    className: 'badge badge-scheduled opacity-50',
  },
};

const interviewTypeLabels = {
  behavioral: 'Behavioral',
  technical: 'Technical',
  system_design: 'System Design',
  mixed: 'Mixed',
};

export default function InterviewCard({ session, onClick }: InterviewCardProps) {
  const statusInfo = statusConfig[session.status] || statusConfig.scheduled;
  const typeLabel = interviewTypeLabels[session.interview_type as keyof typeof interviewTypeLabels] || session.interview_type;

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
    <Card
      variant="interactive"
      className={onClick ? 'cursor-pointer' : ''}
      onClick={onClick}
    >
      <CardContent className="p-6">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h3 className="heading-card mb-2">{typeLabel}</h3>
            <div className="flex items-center gap-2 text-sm text-text-secondary">
              <span>{session.question_count} questions</span>
              {session.duration_seconds && (
                <>
                  <span className="text-text-tertiary">•</span>
                  <span>{Math.floor(session.duration_seconds / 60)} min</span>
                </>
              )}
            </div>
          </div>
          <div className={`badge ${statusInfo.className}`}>
            {statusInfo.label}
          </div>
        </div>

        <div className="flex items-center gap-4 text-sm text-text-secondary flex-wrap">
          <div className="flex items-center gap-1.5">
            <Calendar size={16} />
            <span>{formatDate(session.created_at)}</span>
          </div>

          {session.target_company && (
            <div className="flex items-center gap-1.5 text-electric-blue">
              <Building2 size={16} />
              <span>{companyLabels[session.target_company] || session.target_company}</span>
            </div>
          )}

          {session.overall_score !== null && session.overall_score !== undefined && (
            <div className="flex items-center gap-1.5 text-electric-blue font-semibold">
              <span>Score: {Math.round(session.overall_score)}/100</span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
