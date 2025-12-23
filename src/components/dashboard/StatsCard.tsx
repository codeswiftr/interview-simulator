import type { LucideIcon } from 'lucide-react';

interface StatsCardProps {
  title: string;
  value: string | number;
  icon: LucideIcon;
  subtitle?: string;
  trend?: {
    value: number;
    isPositive: boolean;
  };
}

export default function StatsCard({ title, value, icon: Icon, subtitle, trend }: StatsCardProps) {
  return (
    <div className="card p-6">
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <p className="label text-text-secondary mb-1">{title}</p>
          <p className="heading-section">{value}</p>
          {subtitle && (
            <p className="body-small text-text-tertiary mt-1">{subtitle}</p>
          )}
        </div>
        <div className="p-3 rounded-lg bg-electric-blue/10">
          <Icon size={24} className="text-electric-blue" />
        </div>
      </div>

      {trend && (
        <div className="flex items-center gap-1 text-sm">
          <span className={trend.isPositive ? 'text-status-success' : 'text-status-error'}>
            {trend.isPositive ? '↑' : '↓'} {Math.abs(trend.value)}%
          </span>
          <span className="text-text-tertiary">vs last month</span>
        </div>
      )}
    </div>
  );
}
