import * as React from "react";
import { cn } from "../../lib/cn";

export interface ScoreRingProps extends React.HTMLAttributes<HTMLDivElement> {
  value: number;
  max?: number;
  label?: string;
  size?: "sm" | "md" | "lg";
}

const SIZE_CONFIG = {
  sm: { size: 80, strokeWidth: 6, textSize: "text-lg" },
  md: { size: 120, strokeWidth: 8, textSize: "text-2xl" },
  lg: { size: 160, strokeWidth: 10, textSize: "text-3xl" },
};

const getScoreColor = (value: number): string => {
  if (value >= 90) return "hsl(142, 71%, 45%)"; // excellent - emerald
  if (value >= 75) return "hsl(142, 71%, 45%)"; // good - green
  if (value >= 60) return "hsl(45, 93%, 47%)"; // average - yellow
  if (value >= 40) return "hsl(25, 95%, 53%)"; // needs-work - orange
  return "hsl(0, 84%, 60%)"; // poor - red
};

export const ScoreRing = React.forwardRef<HTMLDivElement, ScoreRingProps>(
  ({ className, value, max = 100, label, size = "md", ...props }, ref) => {
    const config = SIZE_CONFIG[size];
    const percentage = Math.min(Math.max((value / max) * 100, 0), 100);
    const radius = (config.size - config.strokeWidth) / 2;
    const circumference = 2 * Math.PI * radius;
    const strokeDasharray = circumference;
    const strokeDashoffset = circumference - (percentage / 100) * circumference;
    const color = getScoreColor(value);

    return (
      <div
        ref={ref}
        className={cn("relative inline-flex items-center justify-center", className)}
        {...props}
      >
        <svg
          width={config.size}
          height={config.size}
          className="transform -rotate-90"
        >
          {/* Background circle */}
          <circle
            cx={config.size / 2}
            cy={config.size / 2}
            r={radius}
            fill="none"
            stroke="hsl(var(--muted))"
            strokeWidth={config.strokeWidth}
          />
          {/* Progress circle */}
          <circle
            cx={config.size / 2}
            cy={config.size / 2}
            r={radius}
            fill="none"
            stroke={color}
            strokeWidth={config.strokeWidth}
            strokeDasharray={strokeDasharray}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            className="transition-all duration-500 ease-out"
          />
        </svg>
        {/* Score text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className={cn("font-mono font-bold", config.textSize)}>
            {Math.round(value)}
          </span>
          {label && (
            <span className="text-xs text-muted-foreground mt-1">{label}</span>
          )}
        </div>
      </div>
    );
  }
);

ScoreRing.displayName = "ScoreRing";