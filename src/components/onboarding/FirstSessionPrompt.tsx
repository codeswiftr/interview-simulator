import { Play, X } from 'lucide-react';

interface FirstSessionPromptProps {
  isOpen: boolean;
  onCreateSession: () => void;
  onSkip: () => void;
}

export default function FirstSessionPrompt({
  isOpen,
  onCreateSession,
  onSkip,
}: FirstSessionPromptProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center p-4 z-50 animate-fade-in">
      <div className="bg-white dark:bg-surface-secondary rounded-2xl shadow-2xl max-w-md w-full overflow-hidden animate-scale-in">
        {/* Header */}
        <div className="bg-gradient-to-br from-electric-blue to-sky-500 p-6 text-white relative">
          <button
            onClick={onSkip}
            className="absolute top-4 right-4 text-white/80 hover:text-white transition-colors"
            aria-label="Close"
          >
            <X size={24} />
          </button>

          <div className="w-16 h-16 rounded-2xl bg-white/20 flex items-center justify-center mb-4">
            <Play size={32} />
          </div>

          <h2 className="text-2xl font-bold mb-2">
            Ready to Start Practicing?
          </h2>

          <p className="text-white/90 text-sm">
            Create your first interview session to begin practicing with AI-powered feedback.
          </p>
        </div>

        {/* Content */}
        <div className="p-6">
          <div className="bg-electric-blue/5 border border-electric-blue/20 rounded-lg p-4 mb-6">
            <p className="text-sky-600 dark:text-electric-blue font-medium text-sm">
              💡 Tip: Start with a behavioral question to practice the STAR method, or try a technical question to work on problem-solving skills.
            </p>
          </div>

          {/* Actions */}
          <div className="flex gap-3">
            <button
              onClick={onSkip}
              className="btn-ghost flex-1"
            >
              Maybe Later
            </button>
            <button
              onClick={onCreateSession}
              className="btn-primary flex-1 flex items-center justify-center gap-2"
            >
              <Play size={18} />
              Create Session
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
