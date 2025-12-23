import { Loader2, Mic, Volume2, Hand } from 'lucide-react';
import type { ConversationMode } from '../../hooks/useConversationMode';
import { cn } from '../../lib/utils';

interface ConversationIndicatorProps {
  mode: ConversationMode;
  mentorName?: string;
  onInterrupt?: () => void;
  className?: string;
  isListening?: boolean;  // True if mic is actively listening
}

/**
 * Visual indicator for conversation state (mentor speaking, user turn, processing)
 *
 * Shows who should be speaking with animated icons and optional interrupt button.
 */
export function ConversationIndicator({
  mode,
  mentorName = 'Mentor',
  onInterrupt,
  className,
  isListening = false,
}: ConversationIndicatorProps) {
  if (mode === 'idle') {
    return null;
  }

  return (
    <div
      className={cn(
        'flex items-center gap-3 p-4 rounded-lg transition-all duration-300',
        mode === 'mentor_speaking' && 'bg-electric-blue/10 border border-electric-blue/30',
        mode === 'user_turn' && 'bg-green-500/10 border border-green-500/30',
        mode === 'processing' && 'bg-amber-500/10 border border-amber-500/30',
        className
      )}
      role="status"
      aria-live="polite"
    >
      {mode === 'mentor_speaking' && (
        <>
          <div className="relative">
            <Volume2 className="w-8 h-8 text-electric-blue" />
            <span className="absolute -top-1 -right-1 w-3 h-3 bg-electric-blue rounded-full animate-ping" />
          </div>
          <div className="flex-1">
            <p className="text-sm font-semibold text-text-primary">{mentorName} is speaking...</p>
            <p className="text-xs text-text-tertiary">Listen to the question</p>
          </div>
          {onInterrupt && (
            <button
              onClick={onInterrupt}
              className="btn-ghost flex items-center gap-2 text-sm text-text-secondary hover:text-text-primary"
              aria-label="Interrupt mentor"
            >
              <Hand size={16} />
              <span className="hidden sm:inline">Interrupt</span>
            </button>
          )}
        </>
      )}

      {mode === 'user_turn' && (
        <>
          <div className="relative">
            <Mic className={cn('w-8 h-8', isListening ? 'text-status-error' : 'text-green-500')} />
            {isListening && (
              <span className="absolute -top-1 -right-1 w-3 h-3 bg-status-error rounded-full animate-ping" />
            )}
            {!isListening && (
              <span className="absolute -top-1 -right-1 w-3 h-3 bg-green-500 rounded-full animate-pulse" />
            )}
          </div>
          <div className="flex-1">
            <p className="text-sm font-semibold text-text-primary">
              {isListening ? 'Recording your answer...' : 'Your turn to speak'}
            </p>
            <p className="text-xs text-text-tertiary">
              {isListening ? 'Speak clearly - click "Done speaking" when finished' : 'Click the button above to start speaking'}
            </p>
          </div>
        </>
      )}

      {mode === 'processing' && (
        <>
          <Loader2 className="w-8 h-8 text-amber-500 animate-spin" />
          <div className="flex-1">
            <p className="text-sm font-semibold text-text-primary">Processing...</p>
            <p className="text-xs text-text-tertiary">Preparing next question</p>
          </div>
        </>
      )}
    </div>
  );
}

export default ConversationIndicator;
