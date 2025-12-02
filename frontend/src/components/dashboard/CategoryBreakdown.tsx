import { useMemo } from 'react';
import { Briefcase, Code, Layout, Shuffle } from 'lucide-react';
import { cn } from '../../lib/utils';

interface CategoryData {
  category: string;
  count: number;
  averageScore?: number;
}

interface CategoryBreakdownProps {
  data: CategoryData[];
}

const categoryConfig = {
  behavioral: {
    label: 'Behavioral',
    icon: Briefcase,
    color: 'bg-blue-500',
    lightColor: 'bg-blue-100 text-blue-700',
  },
  technical: {
    label: 'Technical',
    icon: Code,
    color: 'bg-purple-500',
    lightColor: 'bg-purple-100 text-purple-700',
  },
  system_design: {
    label: 'System Design',
    icon: Layout,
    color: 'bg-orange-500',
    lightColor: 'bg-orange-100 text-orange-700',
  },
  mixed: {
    label: 'Mixed',
    icon: Shuffle,
    color: 'bg-gray-500',
    lightColor: 'bg-gray-100 text-gray-700',
  },
};

export default function CategoryBreakdown({ data }: CategoryBreakdownProps) {
  const totalCount = useMemo(() => data.reduce((sum, d) => sum + d.count, 0), [data]);

  const enrichedData = useMemo(() => {
    return data.map((d) => ({
      ...d,
      percentage: totalCount > 0 ? (d.count / totalCount) * 100 : 0,
      config: categoryConfig[d.category as keyof typeof categoryConfig] || categoryConfig.mixed,
    }));
  }, [data, totalCount]);

  if (data.length === 0 || totalCount === 0) {
    return (
      <div className="card p-6">
        <h3 className="heading-card mb-4">Category Breakdown</h3>
        <div className="flex items-center justify-center h-40 text-text-tertiary">
          <p>Complete some interviews to see category breakdown</p>
        </div>
      </div>
    );
  }

  return (
    <div className="card p-6">
      <h3 className="heading-card mb-6">Category Breakdown</h3>

      {/* Pie-like visualization using stacked bars */}
      <div className="flex h-4 rounded-full overflow-hidden mb-6">
        {enrichedData.map((d) => (
          <div
            key={d.category}
            className={cn(d.config.color, 'transition-all')}
            style={{ width: `${d.percentage}%` }}
            title={`${d.config.label}: ${d.count} sessions (${d.percentage.toFixed(0)}%)`}
          />
        ))}
      </div>

      {/* Category details */}
      <div className="space-y-4">
        {enrichedData.map((d) => {
          const Icon = d.config.icon;
          return (
            <div key={d.category} className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className={cn('p-2 rounded-lg', d.config.lightColor)}>
                  <Icon size={16} />
                </div>
                <div>
                  <p className="font-medium text-text-primary">{d.config.label}</p>
                  <p className="text-sm text-text-tertiary">
                    {d.count} session{d.count !== 1 ? 's' : ''}
                  </p>
                </div>
              </div>
              <div className="text-right">
                <p className="font-medium text-text-primary">{d.percentage.toFixed(0)}%</p>
                {d.averageScore !== undefined && d.averageScore !== null && (
                  <p className="text-sm text-text-tertiary">
                    Avg: {d.averageScore.toFixed(0)}%
                  </p>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Total */}
      <div className="mt-6 pt-4 border-t border-border-light">
        <div className="flex items-center justify-between text-sm">
          <span className="text-text-secondary">Total Sessions</span>
          <span className="font-semibold text-text-primary">{totalCount}</span>
        </div>
      </div>
    </div>
  );
}
