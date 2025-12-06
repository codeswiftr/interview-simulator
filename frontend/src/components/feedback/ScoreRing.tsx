import { useEffect, useState } from 'react';
import { useTheme } from '../../contexts/ThemeContext';

export type ScoreSize = 'small' | 'medium' | 'large';

interface ScoreRingProps {
  score: number;
  size?: ScoreSize;
  showLabel?: boolean;
  animated?: boolean;
}

interface ScoreConfig {
  label: string;
  color: string;
}

const getScoreConfig = (score: number): ScoreConfig => {
  if (score >= 90) {
    return { label: 'Excellent', color: '#059669' }; // Emerald 600
  } else if (score >= 80) {
    return { label: 'Good', color: '#16A34A' }; // Green 600
  } else if (score >= 70) {
    return { label: 'Average', color: '#CA8A04' }; // Yellow 600
  } else if (score >= 60) {
    return { label: 'Needs Work', color: '#EA580C' }; // Orange 600
  } else {
    return { label: 'Poor', color: '#DC2626' }; // Red 600
  }
};

const getSizeDimensions = (size: ScoreSize) => {
  switch (size) {
    case 'small':
      return {
        width: 100,
        height: 100,
        strokeWidth: 8,
        fontSize: '1.5rem',
        labelSize: '0.75rem',
      };
    case 'medium':
      return {
        width: 150,
        height: 150,
        strokeWidth: 10,
        fontSize: '2rem',
        labelSize: '0.875rem',
      };
    case 'large':
      return {
        width: 200,
        height: 200,
        strokeWidth: 12,
        fontSize: '3rem',
        labelSize: '1rem',
      };
  }
};

export default function ScoreRing({
  score,
  size = 'large',
  showLabel = true,
  animated = true,
}: ScoreRingProps) {
  const [animatedScore, setAnimatedScore] = useState(animated ? 0 : Math.round(score * 10) / 10);
  const { resolvedTheme } = useTheme();
  const config = getScoreConfig(score);
  const dimensions = getSizeDimensions(size);

  // Dark mode adaptive colors
  const bgCircleColor = resolvedTheme === 'dark' ? '#334155' : '#E2E8F0';

  useEffect(() => {
    if (!animated) return;

    const duration = 1000; // 1 second
    const steps = 50;
    const increment = score / steps;
    const stepDuration = duration / steps;

    let currentStep = 0;
    const timer = setInterval(() => {
      currentStep++;
      if (currentStep >= steps) {
        setAnimatedScore(Math.round(score * 10) / 10);
        clearInterval(timer);
      } else {
        setAnimatedScore(Math.round(increment * currentStep));
      }
    }, stepDuration);

    return () => clearInterval(timer);
  }, [score, animated]);

  const { width, height, strokeWidth } = dimensions;
  const radius = (width - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (animatedScore / 100) * circumference;

  return (
    <div className="flex flex-col items-center gap-3">
      <div className="relative" style={{ width, height }}>
        <svg width={width} height={height} className="transform -rotate-90">
          {/* Background circle */}
          <circle
            cx={width / 2}
            cy={height / 2}
            r={radius}
            fill="none"
            stroke={bgCircleColor}
            strokeWidth={strokeWidth}
          />
          {/* Progress circle */}
          <circle
            cx={width / 2}
            cy={height / 2}
            r={radius}
            fill="none"
            stroke={config.color}
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            style={{
              transition: 'stroke-dashoffset 0.5s ease-out',
            }}
          />
        </svg>

        {/* Center text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span
            className="font-mono font-bold tabular-nums"
            style={{
              fontSize: dimensions.fontSize,
              color: config.color,
            }}
          >
            {animatedScore}
          </span>
        </div>
      </div>

      {showLabel && (
        <span
          className="font-semibold"
          style={{
            fontSize: dimensions.labelSize,
            color: config.color,
          }}
        >
          {config.label}
        </span>
      )}
    </div>
  );
}
