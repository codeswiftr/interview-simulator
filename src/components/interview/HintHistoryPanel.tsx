import { ChevronDown, ChevronUp, History, MessageSquare } from 'lucide-react';
import { cn } from '../../lib/utils';

interface Hint {
  timestamp: Date;
  hint: string;
  stage: 'detective' | 'practice';
}

interface HintHistoryPanelProps {
  hints: Hint[];
  isExpanded: boolean;
  onToggle: () => void;
  className?: string;
}

export default function HintHistoryPanel({
  hints,
  isExpanded,
  onToggle,
  className,
}: HintHistoryPanelProps) {
  if (hints.length === 0) return null;

  return (
    <div className={cn('border border-border-light rounded-lg overflow-hidden', className)}>
      {/* Header */}
      <button
        onClick={onToggle}
        className="w-full p-3 flex items-center justify-between bg-surface-secondary hover:bg-surface-tertiary transition-colors"
        aria-expanded={isExpanded ? 'true' : 'false'}
        aria-label={isExpanded ? 'Collapse hint history' : 'Expand hint history'}
      >
        <div className="flex items-center gap-2 text-text-primary">
          <History size={18} className="text-electric-blue" />
          <span className="font-semibold">Hint History</span>
          <span className="text-xs text-text-tertiary bg-surface-primary px-2 py-0.5 rounded-full">
            {hints.length}
          </span>
        </div>
        {isExpanded ? (
          <ChevronUp size={18} className="text-text-tertiary" />
        ) : (
          <ChevronDown size={18} className="text-text-tertiary" />
        )}
      </button>

      {/* Content */}
      {isExpanded && (
        <div className="max-h-64 overflow-y-auto bg-surface-primary">
          <div className="p-3 space-y-3">
            {hints.map((hint, index) => (
              <div
                key={index}
                className="p-3 rounded-lg bg-surface-secondary border border-border-light"
              >
                <div className="flex items-start justify-between gap-2 mb-1">
                  <div className="flex items-center gap-2">
                    <MessageSquare size={14} className="text-electric-blue shrink-0 mt-0.5" />
                    <span className="text-xs font-medium text-text-tertiary">
                      {hint.stage === 'detective' ? 'Detective' : 'Practice'}
                    </span>
                  </div>
                  <span className="text-xs text-text-tertiary shrink-0">
                    {hint.timestamp.toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </span>
                </div>
                <p className="text-sm text-text-secondary leading-relaxed">{hint.hint}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
