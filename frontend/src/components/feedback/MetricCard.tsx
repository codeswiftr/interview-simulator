import type { LucideIcon } from 'lucide-react';
import { Card } from '../ui/Card';

interface MetricCardProps {
  title: string;
  score: number;
  description: string;
  icon: LucideIcon;
  trend?: 'up' | 'down' | 'neutral';
}

const getScoreColor = (score: number): string => {
  if (score >= 90) return 'text-emerald-600 dark:text-emerald-400';
  if (score >= 80) return 'text-green-600 dark:text-green-400';
  if (score >= 70) return 'text-yellow-600 dark:text-yellow-400';
  if (score >= 60) return 'text-orange-600 dark:text-orange-400';
  return 'text-red-600 dark:text-red-400';
};

const getScoreBgColor = (score: number): string => {
  if (score >= 90) return 'bg-emerald-100 dark:bg-emerald-500/10';
  if (score >= 80) return 'bg-green-100 dark:bg-green-500/10';
  if (score >= 70) return 'bg-yellow-100 dark:bg-yellow-500/10';
  if (score >= 60) return 'bg-orange-100 dark:bg-orange-500/10';
  return 'bg-red-100 dark:bg-red-500/10';
};

const getTrendIcon = (trend?: 'up' | 'down' | 'neutral') => {
  if (!trend || trend === 'neutral') return null;

  return (
    <span className={trend === 'up' ? 'text-status-success' : 'text-status-error'}>
      {trend === 'up' ? '↑' : '↓'}
    </span>
  );
};

export default function MetricCard({
  title,
  score,
  description,
  icon: Icon,
  trend,
}: MetricCardProps) {
  const scoreColor = getScoreColor(score);
  const scoreBgColor = getScoreBgColor(score);

  return (
    <Card className="p-6 hover:shadow-lg transition-all hover:scale-[1.02] duration-300">
      <div className="flex items-start justify-between mb-4">
        <div className={`p-3 rounded-xl ${scoreBgColor}`}>
          <Icon className={`w-5 h-5 ${scoreColor}`} />
        </div>
        <div className="flex items-center gap-1">
          {getTrendIcon(trend)}
        </div>
      </div>

      <h3 className="font-semibold text-text-primary mb-2">{title}</h3>

      <div className="flex items-baseline gap-2 mb-3">
        <span className={`text-3xl font-bold tabular-nums ${scoreColor}`}>{Math.round(score * 10) / 10}</span>
        <span className="text-sm text-text-tertiary">/ 100</span>
      </div>

      <p className="text-sm text-text-secondary">{description}</p>
    </Card>
  );
}
