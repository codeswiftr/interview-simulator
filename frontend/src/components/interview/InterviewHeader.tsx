import { X, Lightbulb } from 'lucide-react';
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
    <div className="bg-white/80 dark:bg-surface-dark/80 backdrop-blur-md border-b border-border-light dark:border-border-light/10 sticky top-0 z-50">
      <div className="container mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          {/* Timer */}
          <div className="flex items-center gap-4">
            <div className="text-sm font-medium text-text-secondary uppercase tracking-wider">Elapsed Time</div>
            <Timer startTime={sessionStartTime || undefined} className="text-2xl font-mono font-bold text-text-primary" />
          </div>

          {/* Progress - Mobile: badge, Desktop: full bar */}
          <div className="flex-1 flex justify-center mx-4 sm:mx-8">
            {/* Mobile: Compact progress badge */}
            <div className="md:hidden flex items-center gap-2">
              <div className="h-8 w-8 rounded-full bg-surface-tertiary flex items-center justify-center relative">
                <svg className="absolute inset-0 -rotate-90" viewBox="0 0 32 32">
                  <circle
                    cx="16"
                    cy="16"
                    r="14"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="3"
                    className="text-border-light"
                  />
                  <circle
                    cx="16"
                    cy="16"
                    r="14"
                    fill="none"
                    stroke="url(#progress-gradient)"
                    strokeWidth="3"
                    strokeDasharray={`${(progress / 100) * 88} 88`}
                    strokeLinecap="round"
                  />
                  <defs>
                    <linearGradient id="progress-gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                      <stop offset="0%" stopColor="#38bdf8" />
                      <stop offset="100%" stopColor="#6366f1" />
                    </linearGradient>
                  </defs>
                </svg>
                <span className="text-[10px] font-bold text-text-primary">{Math.round(progress)}%</span>
              </div>
            </div>
            {/* Desktop: Full progress bar */}
            <div className="hidden md:block text-center flex-1 max-w-md">
              <div className="flex justify-between text-xs font-medium text-text-tertiary mb-2 uppercase tracking-wider">
                <span>Progress</span>
                <span>{Math.round(progress)}%</span>
              </div>
              <div className="h-2 bg-surface-tertiary rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-electric-blue to-indigo-500 transition-all duration-500 ease-out"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
          </div>

          {/* Controls */}
          <div className="flex items-center gap-4">
            {/* Coach Toggle */}
            <button
              onClick={() => setShowCoach(!showCoach)}
              className={`p-2 rounded-lg transition-colors ${showCoach ? 'bg-electric-blue/10 text-electric-blue' : 'text-text-tertiary hover:text-text-secondary'}`}
              title="Toggle AI Coach"
              aria-label={showCoach ? 'Disable AI Coach' : 'Enable AI Coach'}
              aria-pressed={showCoach}
            >
              <Lightbulb size={20} />
            </button>

            {/* Exit Button */}
            <button
              onClick={handleExit}
              className="btn-ghost flex items-center gap-2 text-text-secondary hover:text-status-error hover:bg-status-error/10"
            >
              <X size={20} />
              <span className="hidden sm:inline">Exit</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
