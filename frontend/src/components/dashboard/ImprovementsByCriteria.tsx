import { TrendingUp, TrendingDown, Minus, CheckCircle, XCircle } from 'lucide-react';
import { Card } from '../ui/Card';
import type { ImprovementsByCriteriaResponse, CriteriaImprovement } from '../../types';

interface Props {
  data: ImprovementsByCriteriaResponse | null;
  isLoading: boolean;
}

interface CriteriaCardProps {
  title: string;
  data: CriteriaImprovement;
  color: 'blue' | 'purple' | 'emerald';
}

const colorMap = {
  blue: {
    dot: 'bg-electric-blue',
    trend: {
      improving: 'text-emerald-500',
      declining: 'text-orange-500',
      stable: 'text-text-secondary',
    },
  },
  purple: {
    dot: 'bg-purple-500',
    trend: {
      improving: 'text-emerald-500',
      declining: 'text-orange-500',
      stable: 'text-text-secondary',
    },
  },
  emerald: {
    dot: 'bg-emerald-500',
    trend: {
      improving: 'text-emerald-500',
      declining: 'text-orange-500',
      stable: 'text-text-secondary',
    },
  },
};

function TrendIcon({ trend }: { trend: 'improving' | 'declining' | 'stable' }) {
  if (trend === 'improving') return <TrendingUp className="w-4 h-4" />;
  if (trend === 'declining') return <TrendingDown className="w-4 h-4" />;
  return <Minus className="w-4 h-4" />;
}

function CriteriaCard({ title, data, color }: CriteriaCardProps) {
  const colors = colorMap[color];
  const scoreDiff = data.current_score - data.previous_score;

  return (
    <div className="p-4 rounded-xl bg-[hsl(var(--muted)/0.3)] border border-[hsl(var(--border))]">
      <div className="flex items-center justify-between mb-3">
        <h4 className="font-semibold text-text-primary flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${colors.dot}`}></span>
          {title}
        </h4>
        <div className={`flex items-center gap-1 text-sm ${colors.trend[data.trend]}`}>
          <TrendIcon trend={data.trend} />
          <span>
            {scoreDiff >= 0 ? '+' : ''}{scoreDiff.toFixed(0)}
          </span>
        </div>
      </div>

      <div className="mb-3">
        <div className="flex items-baseline gap-2">
          <span className="text-2xl font-bold text-text-primary">{data.current_score.toFixed(0)}</span>
          <span className="text-sm text-text-tertiary">/ 100</span>
        </div>
        <p className="text-xs text-text-tertiary">
          Previous: {data.previous_score.toFixed(0)}
        </p>
      </div>

      <ul className="space-y-2">
        {data.improvements.slice(0, 2).map((improvement, idx) => (
          <li key={`imp-${idx}`} className="flex items-start gap-2 text-sm text-text-secondary">
            <CheckCircle className="w-4 h-4 text-emerald-500 mt-0.5 shrink-0" />
            <span>{improvement}</span>
          </li>
        ))}
        {data.areas_to_work_on.slice(0, 2).map((area, idx) => (
          <li key={`area-${idx}`} className="flex items-start gap-2 text-sm text-text-secondary">
            <XCircle className="w-4 h-4 text-orange-500 mt-0.5 shrink-0" />
            <span>{area}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function ImprovementsSkeleton() {
  return (
    <Card className="p-6 mb-8">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 rounded-lg bg-amber-500/10">
          <TrendingUp className="w-5 h-5 text-amber-500" />
        </div>
        <div className="h-6 w-48 bg-surface-secondary rounded animate-pulse" />
      </div>

      <div className="grid md:grid-cols-3 gap-6">
        {[1, 2, 3].map((i) => (
          <div key={i} className="p-4 rounded-xl bg-surface-secondary/50 border border-border-light">
            <div className="h-5 w-24 bg-surface-secondary rounded animate-pulse mb-3" />
            <div className="h-8 w-16 bg-surface-secondary rounded animate-pulse mb-3" />
            <div className="space-y-2">
              <div className="h-4 w-full bg-surface-secondary rounded animate-pulse" />
              <div className="h-4 w-3/4 bg-surface-secondary rounded animate-pulse" />
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}

export default function ImprovementsByCriteria({ data, isLoading }: Props) {
  if (isLoading) return <ImprovementsSkeleton />;

  // Don't show section if no data available
  if (!data?.data_available) return null;

  // Check if we have at least one category with data
  const hasAnyData = data.delivery || data.behavioral || data.technical;
  if (!hasAnyData) return null;

  return (
    <Card className="p-6 mb-8">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 rounded-lg bg-amber-500/10">
          <TrendingUp className="w-5 h-5 text-amber-500" />
        </div>
        <div>
          <h3 className="heading-card">Improvements by Criteria</h3>
          <p className="text-xs text-text-tertiary mt-1">
            Based on {data.sessions_analyzed} sessions
          </p>
        </div>
      </div>

      <div className="grid md:grid-cols-3 gap-6">
        {data.delivery && (
          <CriteriaCard title="Delivery" data={data.delivery} color="blue" />
        )}
        {data.behavioral && (
          <CriteriaCard title="Behavioral" data={data.behavioral} color="purple" />
        )}
        {data.technical && (
          <CriteriaCard title="Technical" data={data.technical} color="emerald" />
        )}
      </div>
    </Card>
  );
}
