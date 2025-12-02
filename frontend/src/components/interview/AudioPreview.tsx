import { Play, Pause, RotateCcw, CheckCircle } from 'lucide-react';

interface AudioPreviewProps {
  isPlaying: boolean;
  currentTime: number;
  duration: number;
  onPlay: () => void;
  onPause: () => void;
  onReRecord: () => void;
  onConfirm: () => void;
  disabled?: boolean;
}

function formatTime(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

export default function AudioPreview({
  isPlaying,
  currentTime,
  duration,
  onPlay,
  onPause,
  onReRecord,
  onConfirm,
  disabled = false
}: AudioPreviewProps) {
  const progress = duration > 0 ? (currentTime / duration) * 100 : 0;

  return (
    <div className="w-full space-y-6">
      {/* Preview Header */}
      <div className="flex items-center justify-center gap-2 text-status-success">
        <CheckCircle size={20} />
        <span className="body-small font-medium">Recording Complete - Preview Your Answer</span>
      </div>

      {/* Audio Player */}
      <div className="bg-surface-secondary rounded-lg p-6 space-y-4">
        {/* Time Display */}
        <div className="flex items-center justify-between text-sm text-text-secondary">
          <span>{formatTime(currentTime)}</span>
          <span>{formatTime(duration)}</span>
        </div>

        {/* Progress Bar */}
        <div className="relative w-full h-2 bg-surface-tertiary rounded-full overflow-hidden">
          <div
            className="absolute left-0 top-0 h-full bg-electric-blue transition-all duration-100"
            style={{ width: `${progress}%` }}
          />
        </div>

        {/* Play/Pause Button */}
        <div className="flex justify-center">
          <button
            onClick={isPlaying ? onPause : onPlay}
            disabled={disabled}
            className={`
              flex items-center justify-center
              w-16 h-16 rounded-full
              bg-electric-blue text-white
              hover:bg-sky-600 hover:scale-105
              transition-all duration-200
              shadow-lg hover:shadow-blue-glow
              ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
              focus:outline-none focus:ring-4 focus:ring-electric-blue/50
            `}
          >
            {isPlaying ? <Pause size={28} fill="white" /> : <Play size={28} fill="white" />}
          </button>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-4">
        <button
          onClick={onReRecord}
          disabled={disabled}
          className="btn-secondary flex-1 flex items-center justify-center gap-2"
        >
          <RotateCcw size={20} />
          Re-record
        </button>

        <button
          onClick={onConfirm}
          disabled={disabled}
          className="btn-primary flex-1 flex items-center justify-center gap-2"
        >
          <CheckCircle size={20} />
          Submit Answer
        </button>
      </div>
    </div>
  );
}
