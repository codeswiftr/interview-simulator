import { useMemo } from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface ScoreDataPoint {
  date: string;
  score: number;
  content_score?: number;
  audio_score?: number;
}

interface ProgressChartProps {
  data: ScoreDataPoint[];
  height?: number;
}

export default function ProgressChart({ data, height = 200 }: ProgressChartProps) {
  // Calculate chart dimensions
  const chartPadding = { top: 20, right: 20, bottom: 30, left: 40 };
  const chartHeight = height - chartPadding.top - chartPadding.bottom;

  // Calculate trend
  const trend = useMemo(() => {
    if (data.length < 2) return { direction: 'neutral', change: 0 };

    const recentScores = data.slice(-5);
    const firstHalf = recentScores.slice(0, Math.ceil(recentScores.length / 2));
    const secondHalf = recentScores.slice(Math.ceil(recentScores.length / 2));

    const firstAvg = firstHalf.reduce((sum, d) => sum + d.score, 0) / firstHalf.length;
    const secondAvg = secondHalf.reduce((sum, d) => sum + d.score, 0) / secondHalf.length;

    const change = secondAvg - firstAvg;

    return {
      direction: change > 2 ? 'up' : change < -2 ? 'down' : 'neutral',
      change: Math.abs(change).toFixed(1),
    };
  }, [data]);

  // Calculate chart points
  const chartPoints = useMemo(() => {
    if (data.length === 0) return [];

    const minScore = Math.min(...data.map((d) => d.score), 0);
    const maxScore = Math.max(...data.map((d) => d.score), 100);
    const range = maxScore - minScore || 1;

    return data.map((d, i) => ({
      x: (i / Math.max(data.length - 1, 1)) * 100,
      y: chartHeight - ((d.score - minScore) / range) * chartHeight,
      score: d.score,
      date: new Date(d.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    }));
  }, [data, chartHeight]);

  // Generate SVG path
  const linePath = useMemo(() => {
    if (chartPoints.length === 0) return '';

    return chartPoints
      .map((point, i) => `${i === 0 ? 'M' : 'L'} ${point.x} ${point.y}`)
      .join(' ');
  }, [chartPoints]);

  // Generate area path (for gradient fill)
  const areaPath = useMemo(() => {
    if (chartPoints.length === 0) return '';

    return (
      linePath +
      ` L ${chartPoints[chartPoints.length - 1].x} ${chartHeight} L ${chartPoints[0].x} ${chartHeight} Z`
    );
  }, [linePath, chartPoints, chartHeight]);

  if (data.length === 0) {
    return (
      <div className="card p-6">
        <h3 className="heading-card mb-4">Score Progress</h3>
        <div
          className="flex items-center justify-center text-text-tertiary"
          style={{ height }}
        >
          <p>Complete some interviews to see your progress</p>
        </div>
      </div>
    );
  }

  const TrendIcon = trend.direction === 'up' ? TrendingUp : trend.direction === 'down' ? TrendingDown : Minus;
  const trendColor = trend.direction === 'up' ? 'text-status-success' : trend.direction === 'down' ? 'text-status-error' : 'text-text-tertiary';

  return (
    <div className="card p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="heading-card">Score Progress</h3>
        <div className={`flex items-center gap-1 ${trendColor}`}>
          <TrendIcon size={16} />
          <span className="text-sm font-medium">
            {trend.direction === 'neutral' ? 'Stable' : `${trend.change}pts ${trend.direction}`}
          </span>
        </div>
      </div>

      <div style={{ height }}>
        <svg
          viewBox={`0 0 100 ${height}`}
          preserveAspectRatio="none"
          className="w-full h-full"
        >
          <defs>
            <linearGradient id="progressGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="var(--color-electric-blue)" stopOpacity="0.3" />
              <stop offset="100%" stopColor="var(--color-electric-blue)" stopOpacity="0" />
            </linearGradient>
          </defs>

          {/* Grid lines */}
          {[0, 25, 50, 75, 100].map((y) => (
            <line
              key={y}
              x1="0"
              y1={chartPadding.top + (chartHeight * (100 - y)) / 100}
              x2="100"
              y2={chartPadding.top + (chartHeight * (100 - y)) / 100}
              stroke="var(--color-border-light)"
              strokeWidth="0.5"
              strokeDasharray="2,2"
            />
          ))}

          {/* Area fill */}
          <path
            d={areaPath}
            fill="url(#progressGradient)"
            transform={`translate(0, ${chartPadding.top})`}
          />

          {/* Line */}
          <path
            d={linePath}
            fill="none"
            stroke="var(--color-electric-blue)"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            transform={`translate(0, ${chartPadding.top})`}
          />

          {/* Data points */}
          {chartPoints.map((point, i) => (
            <g key={i} transform={`translate(${point.x}, ${point.y + chartPadding.top})`}>
              <circle
                r="3"
                fill="var(--color-electric-blue)"
                className="hover:r-4 transition-all"
              />
              <title>{`${point.date}: ${point.score}%`}</title>
            </g>
          ))}
        </svg>
      </div>

      {/* Legend */}
      <div className="flex items-center justify-between mt-4 text-xs text-text-tertiary">
        <span>{chartPoints[0]?.date || ''}</span>
        <span>{data.length} sessions</span>
        <span>{chartPoints[chartPoints.length - 1]?.date || ''}</span>
      </div>
    </div>
  );
}
