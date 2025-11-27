interface RecordingIndicatorProps {
  isRecording: boolean;
  duration: number;
  className?: string;
}

export default function RecordingIndicator({
  isRecording,
  duration,
  className = ''
}: RecordingIndicatorProps) {
  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  };

  if (!isRecording) {
    return null;
  }

  return (
    <div className={`recording-indicator ${className}`}>
      <span className="text-sm">Recording</span>
      <span className="font-mono text-sm ml-2">{formatDuration(duration)}</span>
    </div>
  );
}
