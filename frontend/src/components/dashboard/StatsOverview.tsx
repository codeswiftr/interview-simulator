import { Clock, Target, TrendingUp, Award } from 'lucide-react';
import { cn } from '../../lib/utils';

interface StatsOverviewProps {
  totalSessions: number;
  completedSessions: number;
  averageScore: number | null;
  totalPracticeTimeSeconds: number;
}

export default function StatsOverview({
  totalSessions,
  completedSessions,
  averageScore,
  totalPracticeTimeSeconds,
}: StatsOverviewProps) {
  // Format practice time
  const formatTime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);

    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    }
    return `${minutes}m`;
  };

  // Get score color
  const getScoreColor = (score: number | null) => {
    if (score === null) return 'text-text-tertiary';
    if (score >= 80) return 'text-status-success';
    if (score >= 60) return 'text-yellow-500';
    return 'text-status-error';
  };

  // Get score label
  const getScoreLabel = (score: number | null) => {
    if (score === null) return 'N/A';
    if (score >= 90) return 'Excellent';
    if (score >= 80) return 'Great';
    if (score >= 70) return 'Good';
    if (score >= 60) return 'Fair';
    return 'Needs Work';
  };

  const stats = [
    {
      label: 'Total Sessions',
      value: totalSessions,
      icon: Target,
      color: 'text-electric-blue bg-electric-blue/10',
      subtitle: `${completedSessions} completed`,
    },
    {
      label: 'Average Score',
      value: averageScore !== null ? `${averageScore.toFixed(0)}%` : '--',
      icon: Award,
      color: cn(
        'bg-opacity-10',
        averageScore !== null && averageScore >= 70
          ? 'text-status-success bg-status-success/10'
          : 'text-yellow-500 bg-yellow-500/10'
      ),
      subtitle: getScoreLabel(averageScore),
      valueColor: getScoreColor(averageScore),
    },
    {
      label: 'Practice Time',
      value: formatTime(totalPracticeTimeSeconds),
      icon: Clock,
      color: 'text-purple-500 bg-purple-500/10',
      subtitle: 'Total time invested',
    },
    {
      label: 'Completion Rate',
      value:
        totalSessions > 0
          ? `${((completedSessions / totalSessions) * 100).toFixed(0)}%`
          : '--',
      icon: TrendingUp,
      color: 'text-orange-500 bg-orange-500/10',
      subtitle: `${completedSessions} of ${totalSessions}`,
    },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {stats.map((stat) => {
        const Icon = stat.icon;
        return (
          <div key={stat.label} className="card p-4">
            <div className="flex items-start justify-between mb-3">
              <div className={cn('p-2 rounded-lg', stat.color)}>
                <Icon size={20} />
              </div>
            </div>
            <div className={cn('text-2xl font-bold mb-1', stat.valueColor || 'text-text-primary')}>
              {stat.value}
            </div>
            <div className="text-sm text-text-secondary">{stat.label}</div>
            {stat.subtitle && (
              <div className="text-xs text-text-tertiary mt-1">{stat.subtitle}</div>
            )}
          </div>
        );
      })}
    </div>
  );
}
