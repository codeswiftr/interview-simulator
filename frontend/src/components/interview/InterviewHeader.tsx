import { X, Lightbulb, Clock } from 'lucide-react';
import { useInterview } from '../../contexts/InterviewContext';
import Timer from './Timer';

export default function InterviewHeader() {
  const {
    sessionStartTime,
    progress,
    showCoach,
    setShowCoach,
    handleExit,
  } = useInterview();

  return (
    <header className="bg-white/90 dark:bg-surface-dark/90 backdrop-blur-xl border-b border-border-light dark:border-white/5 sticky top-0 z-50 shadow-sm">
      <div className="container mx-auto px-4 sm:px-6">
        <div className="flex items-center justify-between h-14 sm:h-16">
          {/* Timer - Compact */}
          <div className="flex items-center gap-2 sm:gap-3 min-w-[120px] sm:min-w-[140px]">
            <Clock size={16} className="text-text-tertiary hidden sm:block" />
            <Timer
              startTime={sessionStartTime || undefined}
              className="text-lg sm:text-xl font-mono font-bold text-text-primary tabular-nums"
            />
          </div>

          {/* Progress - Unified design for all screens */}
          <div className="flex-1 max-w-[200px] sm:max-w-xs mx-3 sm:mx-8">
            <div className="flex items-center justify-between text-[10px] sm:text-xs font-medium text-text-tertiary mb-1 sm:mb-1.5 uppercase tracking-wider">
              <span>Progress</span>
              <span className="tabular-nums">{Math.round(progress)}%</span>
            </div>
            <div className="h-1.5 sm:h-2 bg-surface-tertiary dark:bg-white/5 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-electric-blue to-indigo-500 transition-all duration-700 ease-out rounded-full"
                style={{ width: `${progress}%` }}
                role="progressbar"
                aria-valuenow={progress}
                aria-valuemin={0}
                aria-valuemax={100}
                aria-label={`Interview progress: ${Math.round(progress)}%`}
              />
            </div>
          </div>

          {/* Controls - Consolidated */}
          <div className="flex items-center gap-1.5 sm:gap-3">
            {/* Coach Toggle */}
            <button
              onClick={() => setShowCoach(!showCoach)}
              className={`p-2 sm:p-2.5 rounded-lg transition-all min-w-[44px] min-h-[44px] flex items-center justify-center ${
                showCoach
                  ? 'bg-electric-blue/15 text-electric-blue ring-2 ring-electric-blue/30'
                  : 'text-text-tertiary hover:text-text-secondary hover:bg-surface-secondary'
              }`}
              title="Toggle AI Coach"
              aria-label={showCoach ? 'Disable AI Coach' : 'Enable AI Coach'}
              aria-pressed={showCoach}
            >
              <Lightbulb size={18} />
            </button>

            {/* Exit Button */}
            <button
              onClick={handleExit}
              className="p-2 sm:p-2.5 rounded-lg text-text-tertiary hover:text-status-error hover:bg-status-error/10 transition-all min-w-[44px] min-h-[44px] flex items-center justify-center gap-2"
              aria-label="Exit interview"
            >
              <X size={18} />
              <span className="hidden sm:inline text-sm font-medium">Exit</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
