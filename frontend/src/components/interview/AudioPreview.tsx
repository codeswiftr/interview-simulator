import { useEffect, useRef } from 'react';
import { Play, Pause, RotateCcw, CheckCircle, Loader2, Upload, Send, AlertCircle, RefreshCw } from 'lucide-react';

interface AudioPreviewProps {
  isPlaying: boolean;
  currentTime: number;
  duration: number;
  onPlay: () => void;
  onPause: () => void;
  onReRecord: () => void;
  onConfirm: () => void;
  onRetry?: () => void;
  disabled?: boolean;
  isSubmitting?: boolean;
  submitProgress?: 'uploading' | 'processing' | null;
  submitError?: string | null;
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
  onRetry,
  disabled = false,
  isSubmitting = false,
  submitProgress = null,
  submitError = null
}: AudioPreviewProps) {
  const progress = duration > 0 ? (currentTime / duration) * 100 : 0;
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number | undefined>(undefined);

  // Simulated visualizer for preview mode (since we don't have the raw stream stream anymore easily)
  // We'll generate a pleasing "playback" animation when playing
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const draw = () => {
      // Clear canvas
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const bars = 40;
      const barWidth = canvas.width / bars;

      for (let i = 0; i < bars; i++) {
        // Create a wave effect based on time and index
        const heightMultiplier = isPlaying
          ? Math.max(0.2, (Math.sin((Date.now() / 100) + i * 0.5) + 1) / 2)
          : 0.2; // Static low bars when paused

        const barHeight = (canvas.height * 0.8) * heightMultiplier;
        const x = i * barWidth;
        const y = (canvas.height - barHeight) / 2;

        // Gradient based on playing state
        const gradient = ctx.createLinearGradient(0, 0, 0, canvas.height);
        if (isPlaying) {
          gradient.addColorStop(0, '#38bdf8'); // sky-400
          gradient.addColorStop(1, '#6366f1'); // indigo-500
        } else {
          gradient.addColorStop(0, '#94a3b8'); // slate-400
          gradient.addColorStop(1, '#64748b'); // slate-500
        }

        ctx.fillStyle = gradient;

        // Rounded caps manually or just rects
        ctx.fillRect(x + 1, y, barWidth - 2, barHeight);
      }

      animationRef.current = requestAnimationFrame(draw);
    };

    draw();

    return () => {
      if (animationRef.current) cancelAnimationFrame(animationRef.current);
    };
  }, [isPlaying]);


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
      <div className="flex items-center justify-center gap-2 text-status-success animate-fade-in">
        <CheckCircle size={20} />
        <span className="body-small font-medium">Recording Complete</span>
      </div>

      {/* Audio Player Card - Premium Glassmorphism */}
      <div className="bg-white/80 dark:bg-surface-secondary/80 backdrop-blur-md rounded-2xl p-6 shadow-xl border border-white/50 dark:border-white/10 relative overflow-hidden group">

        {/* Background Glow Effect */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-1/2 h-1/2 bg-electric-blue/10 blur-[50px] rounded-full pointer-events-none"></div>

        {/* Visualizer Canvas */}
        <div className="h-32 w-full mb-6 relative flex items-center justify-center">
          <canvas
            ref={canvasRef}
            width={600}
            height={128}
            className="w-full h-full opacity-90"
            style={{ maxWidth: '100%', display: 'block' }}
          />

          {/* Play/Pause Overlay Button */}
          <div className="absolute inset-0 flex items-center justify-center">
            <button
              onClick={isPlaying ? onPause : onPlay}
              disabled={disabled || isSubmitting}
              className={`
                    flex items-center justify-center
                    w-16 h-16 rounded-full
                    bg-electric-blue text-white
                    hover:bg-sky-500 hover:scale-110 active:scale-95
                    transition-all duration-300
                    shadow-lg hover:shadow-blue-glow z-10
                    ${(disabled || isSubmitting) ? 'opacity-50 cursor-not-allowed' : ''}
                    `}
            >
              {isPlaying ? <Pause size={28} fill="white" /> : <Play size={28} fill="white" className="ml-1" />}
            </button>
          </div>
        </div>

        {/* Metadata & Progress */}
        <div className="space-y-3 relative z-10">
          <div className="flex items-center justify-between text-xs font-mono font-medium text-text-tertiary uppercase tracking-wider">
            <span>{isPlaying ? 'Playing' : 'Paused'}</span>
            <span>{formatTime(currentTime)} / {formatTime(duration)}</span>
          </div>

          {/* Custom Progress Bar */}
          <div className="relative w-full h-1.5 bg-surface-tertiary rounded-full overflow-hidden cursor-pointer group-hover:h-2 transition-all">
            <div
              className="absolute left-0 top-0 h-full bg-gradient-to-r from-electric-blue to-indigo-500 transition-all duration-100 ease-linear shadow-[0_0_10px_rgba(56,189,248,0.5)]"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-4">
        <button
          onClick={onReRecord}
          disabled={disabled || isSubmitting}
          className="btn-secondary flex-1 flex items-center justify-center gap-2 group border-transparent hover:border-gray-200 dark:hover:border-gray-700"
        >
          <RotateCcw size={18} className="group-hover:-rotate-90 transition-transform duration-300" />
          Re-record
        </button>

        <button
          onClick={onConfirm}
          disabled={disabled || isSubmitting}
          className={`btn-primary flex-1 flex items-center justify-center gap-2 shadow-lg shadow-electric-blue/20 hover:shadow-electric-blue/40 ${isSubmitting ? 'bg-electric-blue/70' : ''
            }`}
        >
          {getSubmitButtonContent()}
        </button>
      </div>

      {/* Submission progress message */}
      {isSubmitting && (
        <div className="text-center text-sm font-medium text-electric-blue bg-electric-blue/5 rounded-lg p-3 animate-pulse">
          {submitProgress === 'uploading' && 'Uploading your audio recording...'}
          {submitProgress === 'processing' && 'Your answer is being processed...'}
          {!submitProgress && 'Submitting...'}
        </div>
      )}

      {/* Error state with retry */}
      {submitError && !isSubmitting && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 space-y-3">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm font-medium text-red-600 dark:text-red-400">Submission Failed</p>
              <p className="text-xs text-text-secondary mt-1">{submitError}</p>
            </div>
          </div>
          {onRetry && (
            <button
              onClick={onRetry}
              className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg bg-red-500 text-white font-medium text-sm hover:bg-red-600 active:scale-[0.98] transition-all"
            >
              <RefreshCw size={16} />
              Retry Upload
            </button>
          )}
        </div>
      )}
    </div>
  );
}
