import type { LucideIcon } from 'lucide-react';

interface MetricCardProps {
  title: string;
  score: number;
  description: string;
  icon: LucideIcon;
  trend?: 'up' | 'down' | 'neutral';
}

const getScoreColor = (score: number): string => {
  if (score >= 90) return 'text-score-excellent';
  if (score >= 80) return 'text-score-good';
  if (score >= 70) return 'text-score-average';
  if (score >= 60) return 'text-score-needs-work';
  return 'text-score-poor';
};

const getScoreBgColor = (score: number): string => {
  if (score >= 90) return 'bg-score-excellent/10';
  if (score >= 80) return 'bg-score-good/10';
  if (score >= 70) return 'bg-score-average/10';
  if (score >= 60) return 'bg-score-needs-work/10';
  return 'bg-score-poor/10';
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
    <div className="card p-6 hover:shadow-lg transition-all">
      <div className="flex items-start justify-between mb-4">
        <div className={`p-3 rounded-lg ${scoreBgColor}`}>
          <Icon className={`w-6 h-6 ${scoreColor}`} />
        </div>
        <div className="flex items-center gap-1">
          {getTrendIcon(trend)}
        </div>
      </div>

      <h3 className="heading-card mb-2">{title}</h3>

      <div className="flex items-baseline gap-2 mb-3">
        <span className={`score-display ${scoreColor}`}>{score}</span>
        <span className="body-small text-text-tertiary">/ 100</span>
      </div>

      <p className="body-small text-text-secondary">{description}</p>
    </div>
  );
}
