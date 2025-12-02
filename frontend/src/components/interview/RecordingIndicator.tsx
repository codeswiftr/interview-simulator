import { Mic, Radio } from 'lucide-react';

interface RecordingIndicatorProps {
  isRecording: boolean;
  duration: number;
  className?: string;
  showIdleState?: boolean;
}

export default function RecordingIndicator({
  isRecording,
  duration,
  className = '',
  showIdleState = true
}: RecordingIndicatorProps) {
  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  };

  if (isRecording) {
    return (
      <div className={`flex flex-col items-center gap-3 ${className}`}>
        {/* Animated recording indicator */}
        <div className="relative">
          <div className="w-20 h-20 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center">
            <div className="w-16 h-16 rounded-full bg-red-200 dark:bg-red-800/50 flex items-center justify-center animate-pulse">
              <Radio className="w-8 h-8 text-red-500 animate-pulse" />
            </div>
          </div>
          {/* Ripple effect */}
          <div className="absolute inset-0 rounded-full border-2 border-red-400 animate-ping opacity-75" />
        </div>

        {/* Status text */}
        <div className="flex items-center gap-2">
          <span className="inline-block w-2 h-2 bg-red-500 rounded-full animate-pulse" />
          <span className="text-red-500 font-semibold">Recording</span>
        </div>

        {/* Duration */}
        <div className="font-mono text-2xl text-text-primary font-bold">
          {formatDuration(duration)}
        </div>

        {/* Hint */}
        <p className="text-sm text-text-secondary text-center">
          Click the stop button when you're done
        </p>
      </div>
    );
  }

  if (!showIdleState) {
    return null;
  }

  return (
    <div className={`flex flex-col items-center gap-3 ${className}`}>
      {/* Idle state */}
      <div className="w-20 h-20 rounded-full bg-surface-secondary flex items-center justify-center">
        <Mic className="w-8 h-8 text-text-tertiary" />
      </div>

      <div className="text-center">
        <p className="text-text-secondary font-medium">Ready to Record</p>
        <p className="text-sm text-text-tertiary mt-1">
          Click the microphone button to start recording your answer
        </p>
      </div>
    </div>
  );
}
