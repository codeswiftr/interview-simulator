import { cn } from '../../lib/utils';

interface WaveformPlaceholderProps {
  isActive?: boolean;
  barCount?: number;
  className?: string;
}

/**
 * WaveformPlaceholder - Animated placeholder for the audio visualizer
 * Shows when no mediaStream is available (before recording starts)
 */
export function WaveformPlaceholder({
  isActive = false,
  barCount = 32,
  className
}: WaveformPlaceholderProps) {
  return (
    <div
      className={cn(
        "flex items-end justify-center gap-[2px] h-full w-full px-4",
        className
      )}
      aria-hidden="true"
    >
      {Array.from({ length: barCount }).map((_, i) => {
        // Create a sine wave pattern for natural look
        const baseHeight = 25 + Math.sin(i * 0.4) * 20;
        const delay = (i * 0.04).toFixed(2);

        return (
          <div
            key={i}
            className={cn(
              "w-1 sm:w-1.5 rounded-full transition-all duration-500",
              isActive
                ? "bg-gradient-to-t from-electric-blue to-indigo-500 animate-bar-bounce"
                : "bg-gradient-to-t from-slate-600 to-slate-500 opacity-20"
            )}
            style={{
              height: `${baseHeight}%`,
              animationDelay: isActive ? `${delay}s` : undefined,
            }}
          />
        );
      })}
    </div>
  );
}

export default WaveformPlaceholder;
