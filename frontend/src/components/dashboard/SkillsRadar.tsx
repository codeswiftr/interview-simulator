import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip
} from 'recharts';

interface SkillData {
  subject: string;
  current: number; // Current Score
  target: number;  // Target Score (Full Mark)
}

interface SkillsRadarProps {
  data?: SkillData[];
}

// Dummy data fallback for Gap Analysis
const defaultData: SkillData[] = [
  { subject: 'Technical', current: 65, target: 90 },
  { subject: 'Behavioral', current: 80, target: 90 },
  { subject: 'System Design', current: 45, target: 85 },
  { subject: 'Communication', current: 90, target: 95 },
  { subject: 'Confidence', current: 70, target: 90 },
  { subject: 'Delivery', current: 60, target: 85 },
];

export default function SkillsRadar({ data = defaultData }: SkillsRadarProps) {
  return (
    <div className="w-full h-[240px]">
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart cx="50%" cy="50%" outerRadius="75%" data={data}>
          <PolarGrid stroke="var(--color-border-light)" strokeOpacity={0.5} />
          <PolarAngleAxis
            dataKey="subject"
            tick={{ fill: 'var(--color-text-secondary)', fontSize: 10 }}
          />
          <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />

          {/* Current Skills */}
          <Radar
            name="Score"
            dataKey="current"
            stroke="var(--color-electric-blue)"
            strokeWidth={2}
            fill="var(--color-electric-blue)"
            fillOpacity={0.3}
          />

          <Tooltip
            contentStyle={{
              backgroundColor: 'var(--bg-primary)',
              borderColor: 'var(--border-color)',
              borderRadius: '0.375rem',
              fontSize: '12px'
            }}
            itemStyle={{ color: 'var(--color-text-primary)' }}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}
