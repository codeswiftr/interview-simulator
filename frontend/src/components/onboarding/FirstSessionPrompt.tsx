import { Play, X, Lightbulb } from 'lucide-react';
import { cn } from '../../lib/utils';
import { GrowthIllustration } from './OnboardingIllustrations';

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
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 z-50 animate-fade-in">
      <div className="bg-gradient-to-b from-slate-900 via-slate-800 to-slate-900 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950 rounded-2xl shadow-2xl max-w-md w-full overflow-hidden animate-scale-in border border-white/5">
        {/* Close button */}
        <button
          onClick={onSkip}
          className="absolute top-4 right-4 z-10 p-2 text-white/50 hover:text-white/80 transition-colors rounded-lg hover:bg-white/5"
          aria-label="Close"
        >
          <X size={20} />
        </button>

        {/* Main content area */}
        <div className="relative">
          {/* Ambient glow */}
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-electric-blue/15 via-transparent to-transparent pointer-events-none" />

          {/* Illustration */}
          <div className="relative h-40 flex items-center justify-center pt-6">
            <GrowthIllustration className="w-32 h-32" animate={true} />
          </div>

          {/* Content */}
          <div className="px-8 pb-6 pt-2 text-center">
            <h2 className="text-2xl font-bold text-white mb-1">
              Start Your First Interview
            </h2>
            <p className="text-electric-blue font-medium text-sm mb-3">
              Get your score in under 15 minutes
            </p>
            <p className="text-white/70 text-sm leading-relaxed mb-6 max-w-sm mx-auto">
              Choose a behavioral question, record your answer, and get instant feedback on exactly what to improve.
            </p>

            {/* Tip box */}
            <div className="bg-white/5 border border-white/10 rounded-xl p-4 mb-6">
              <p className="text-white/80 text-sm flex items-start gap-2 text-left">
                <Lightbulb size={16} className="text-amber-400 flex-shrink-0 mt-0.5" />
                <span>
                  <strong className="text-white">Pro tip:</strong> Start with "Tell me about yourself" — it&apos;s the most common question and gives you a baseline score fast.
                </span>
              </p>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="px-8 pb-8 flex gap-3">
          <button
            onClick={onSkip}
            className="flex-1 px-4 py-3 rounded-xl text-white/60 hover:text-white hover:bg-white/5 transition-all font-medium"
          >
            Maybe Later
          </button>
          <button
            onClick={onCreateSession}
            className={cn(
              'flex-1 flex items-center justify-center gap-2 px-6 py-3 rounded-xl font-semibold transition-all',
              'bg-electric-blue hover:bg-sky-500 text-white',
              'hover:translate-y-[-1px] hover:shadow-lg hover:shadow-electric-blue/25',
              'active:translate-y-0 active:shadow-none'
            )}
          >
            <Play size={18} />
            Start Interview
          </button>
        </div>
      </div>
    </div>
  );
}
