import { Play, Pause, RotateCcw, CheckCircle, Loader2, Upload, Send } from 'lucide-react';

interface AudioPreviewProps {
  isPlaying: boolean;
  currentTime: number;
  duration: number;
  onPlay: () => void;
  onPause: () => void;
  onReRecord: () => void;
  onConfirm: () => void;
  disabled?: boolean;
  isSubmitting?: boolean;
  submitProgress?: 'uploading' | 'processing' | null;
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
  disabled = false,
  isSubmitting = false,
  submitProgress = null
}: AudioPreviewProps) {
  const progress = duration > 0 ? (currentTime / duration) * 100 : 0;

  const getSubmitButtonContent = () => {
    if (isSubmitting) {
      if (submitProgress === 'uploading') {
        return (
          <>
            <Upload size={20} className="animate-bounce" />
            Uploading...
          </>
        );
      }
      if (submitProgress === 'processing') {
        return (
          <>
            <Loader2 size={20} className="animate-spin" />
            Processing...
          </>
        );
      }
      return (
        <>
          <Loader2 size={20} className="animate-spin" />
          Submitting...
        </>
      );
    }
    return (
      <>
        <Send size={20} />
        Submit Answer
      </>
    );
  };

  return (
    <div className="w-full space-y-6">
      {/* Preview Header */}
      <div className="flex items-center justify-center gap-2 text-status-success">
        <CheckCircle size={20} />
        <span className="body-small font-medium">Recording Complete - Preview Your Answer</span>
      </div>

      {/* Audio Player */}
      <div className="bg-surface-secondary rounded-lg p-6 space-y-4">
        {/* Recording Duration Summary */}
        <div className="text-center mb-2">
          <span className="text-text-secondary text-sm">Recording Length: </span>
          <span className="font-mono font-semibold text-text-primary">{formatTime(duration)}</span>
        </div>

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
            disabled={disabled || isSubmitting}
            className={`
              flex items-center justify-center
              w-16 h-16 rounded-full
              bg-electric-blue text-white
              hover:bg-sky-600 hover:scale-105
              transition-all duration-200
              shadow-lg hover:shadow-blue-glow
              ${(disabled || isSubmitting) ? 'opacity-50 cursor-not-allowed' : ''}
              focus:outline-none focus:ring-4 focus:ring-electric-blue/50
            `}
          >
            {isPlaying ? <Pause size={28} fill="white" /> : <Play size={28} fill="white" />}
          </button>
        </div>

        {/* Playback hint */}
        <p className="text-center text-sm text-text-tertiary">
          {isPlaying ? 'Click to pause' : 'Click to preview your recording'}
        </p>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-4">
        <button
          onClick={onReRecord}
          disabled={disabled || isSubmitting}
          className="btn-secondary flex-1 flex items-center justify-center gap-2"
        >
          <RotateCcw size={20} />
          Re-record
        </button>

        <button
          onClick={onConfirm}
          disabled={disabled || isSubmitting}
          className={`btn-primary flex-1 flex items-center justify-center gap-2 ${
            isSubmitting ? 'bg-electric-blue/70' : ''
          }`}
        >
          {getSubmitButtonContent()}
        </button>
      </div>

      {/* Submission progress message */}
      {isSubmitting && (
        <div className="text-center text-sm text-text-secondary bg-surface-secondary rounded-lg p-3">
          {submitProgress === 'uploading' && 'Uploading your audio recording...'}
          {submitProgress === 'processing' && 'Your answer is being processed. This may take a moment.'}
          {!submitProgress && 'Submitting your answer...'}
        </div>
      )}
    </div>
  );
}
