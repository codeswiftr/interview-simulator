import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip
} from 'recharts';
import { Skeleton } from '../ui/Skeleton';

interface SkillData {
  subject: string;
  current: number; // Current Score
  target: number;  // Target Score (Full Mark)
}

interface SkillsRadarProps {
  data?: SkillData[];
  isLoading?: boolean;
}

export default function SkillsRadar({ data, isLoading }: SkillsRadarProps) {
  // Loading state
  if (isLoading) {
    return (
      <div className="w-full h-[240px] flex items-center justify-center">
        <div className="text-center">
          <Skeleton variant="circular" width={160} height={160} />
        </div>
      </div>
    );
  }

  // Empty state - not enough data
  if (!data || data.length === 0) {
    return (
      <div className="w-full h-[240px] flex items-center justify-center">
        <div className="text-center px-4">
          <p className="text-text-secondary text-sm mb-2">
            Complete 2+ interview sessions to see your skills analysis.
          </p>
          <p className="text-text-tertiary text-xs">
            Each session contributes to your skill dimensions.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-[240px]">
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart cx="50%" cy="50%" outerRadius="75%" data={data}>
          <PolarGrid stroke="currentColor" strokeOpacity={0.15} className="text-text-secondary" />
          <PolarAngleAxis
            dataKey="subject"
            tick={{ fill: '#64748b', fontSize: 10 }}
            className="dark:[&_text]:fill-slate-400"
          />
          <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />

          {/* Current Skills */}
          <Radar
            name="Score"
            dataKey="current"
            stroke="#0ea5e9"
            strokeWidth={2}
            fill="#0ea5e9"
            fillOpacity={0.3}
          />

          <Tooltip
            contentStyle={{
              backgroundColor: 'hsl(var(--surface-primary))',
              borderColor: 'hsl(var(--border-light))',
              borderRadius: '0.375rem',
              fontSize: '12px'
            }}
            itemStyle={{ color: 'hsl(var(--text-primary))' }}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}
