import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip,
  Legend
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
    <div className="w-full h-[300px]">
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart cx="50%" cy="50%" outerRadius="70%" data={data}>
          <PolarGrid stroke="var(--color-border-light)" />
          <PolarAngleAxis 
            dataKey="subject" 
            tick={{ fill: 'var(--color-text-secondary)', fontSize: 11, fontWeight: 500 }}
          />
          <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
          
          {/* Target / Goal Area (Background) */}
          <Radar
            name="Target Goal"
            dataKey="target"
            stroke="var(--color-text-tertiary)"
            strokeDasharray="4 4"
            strokeWidth={1}
            fill="var(--color-surface-tertiary)"
            fillOpacity={0.2}
          />

          {/* Current Skills (Foreground) */}
          <Radar
            name="Current Level"
            dataKey="current"
            stroke="var(--color-electric-blue)"
            strokeWidth={2}
            fill="var(--color-electric-blue)"
            fillOpacity={0.4}
          />

          <Tooltip 
            contentStyle={{ 
              backgroundColor: 'var(--bg-primary)', 
              borderColor: 'var(--border-color)',
              borderRadius: '0.5rem',
              boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
            }}
            itemStyle={{ color: 'var(--color-text-primary)' }}
          />
          <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }} />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}
