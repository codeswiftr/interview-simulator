import { useState, useEffect } from 'react';
import { Lightbulb, Clock, X, ChevronRight, ChevronLeft, MessageSquare, Info, Loader2, AlertCircle } from 'lucide-react';

interface CoachOverlayProps {
  // InterviewPage (full context)
  isVisible?: boolean;
  questionType?: string;
  elapsedTime?: number;
  expectedDuration?: number;

  // Shared
  onClose: () => void;

  // Dynamic hints (canonical)
  dynamicHint?: string | null;
  isHintLoading?: boolean;
  isHintStreaming?: boolean;
  hintError?: string | null;

  // Simplified aliases (PreparationPage)
  hint?: string | null;
  isLoading?: boolean;
  isStreaming?: boolean;
  error?: string | null;
  onToggle?: () => void;
  isCollapsed?: boolean;
}

export default function CoachOverlay({
  isVisible = true,
  onClose,
  questionType: rawQuestionType,
  elapsedTime: rawElapsedTime,
  expectedDuration: rawExpectedDuration,
  dynamicHint,
  isHintLoading,
  isHintStreaming,
  hintError,
  hint,
  isLoading,
  isStreaming,
  error,
  onToggle,
  isCollapsed,
}: CoachOverlayProps) {
  const [internalExpanded, setInternalExpanded] = useState(isCollapsed !== true);
  const [activeHint, setActiveHint] = useState(0);

  // Derive resolved props for backwards compatibility
  const resolvedHint = dynamicHint ?? hint ?? null;
  const resolvedLoading = isHintLoading ?? isLoading ?? false;
  const resolvedStreaming = isHintStreaming ?? isStreaming ?? false;
  const resolvedError = hintError ?? error ?? null;
  const questionType = rawQuestionType ?? 'behavioral';
  const elapsedTime = rawElapsedTime ?? 0;
  const expectedDuration = rawExpectedDuration ?? 0;
  const shouldBeExpanded = isCollapsed !== undefined ? !isCollapsed : internalExpanded;
  const isExpanded = shouldBeExpanded;

  // Auto-collapse on mobile after 5 seconds
  useEffect(() => {
    if (isCollapsed !== undefined) return; // controlled mode, don't override
    if (window.innerWidth < 768) {
      const timer = setTimeout(() => setInternalExpanded(false), 5000);
      return () => clearTimeout(timer);
    }
  }, [isCollapsed]);

  // Sync internal expanded state when controlled prop changes
  // Use derived state - no effect needed

  const handleToggle = () => {
    if (onToggle) {
      onToggle();
    } else {
      setInternalExpanded(prev => !prev);
    }
  };

  if (!isVisible) return null;

  const getHints = () => {
    const commonHints = [
      { title: 'Speak Clearly', text: 'Maintain a steady pace and clear enunciation.' },
      { title: 'Be Specific', text: 'Use concrete examples to back up your claims.' },
    ];

    const behavioralHints = [
      { title: 'STAR Framework', text: 'Structure your answer: Situation, Task, Action, Result.' },
      { title: 'Focus on "I"', text: 'Emphasize YOUR contribution, not just the team\'s.' },
      { title: 'Quantify Results', text: 'Mention numbers and metrics where possible.' },
    ];

    const technicalHints = [
      { title: 'Clarify First', text: 'Ask questions to remove ambiguity before solving.' },
      { title: 'Think Aloud', text: 'Explain your thought process as you go.' },
      { title: 'Consider Trade-offs', text: 'Discuss pros and cons of your approach.' },
    ];

    const systemDesignHints = [
      { title: 'Requirements', text: 'Define functional and non-functional requirements.' },
      { title: 'High-Level Design', text: 'Draw the big picture before diving deep.' },
      { title: 'Bottlenecks', text: 'Identify potential single points of failure.' },
    ];

    switch (questionType) {
      case 'behavioral': return [...behavioralHints, ...commonHints];
      case 'technical': return [...technicalHints, ...commonHints];
      case 'system_design': return [...systemDesignHints, ...commonHints];
      default: return commonHints;
    }
  };

  const hints = getHints();
  const timeLeft = Math.max(0, expectedDuration - elapsedTime);
  const isTimeRunningOut = expectedDuration > 0 && timeLeft < 60 && timeLeft > 0;

  return (
    <div
      className={`fixed right-4 top-24 z-40 transition-all duration-300 ease-in-out max-w-[calc(100vw-2rem)] ${isExpanded ? 'w-72 sm:w-80' : 'w-12'}`}
      role="complementary"
      aria-label="AI Coach"
    >
      <div className="bg-white/95 dark:bg-surface-dark/95 backdrop-blur-md border border-electric-blue/30 shadow-xl rounded-2xl overflow-hidden">
        {/* Header / Toggle */}
        <button
          onClick={handleToggle}
          className="w-full p-3 flex items-center justify-between bg-electric-blue/10 hover:bg-electric-blue/20 transition-colors"
          aria-expanded={isExpanded}
          aria-controls="coach-content"
        >
          {isExpanded ? (
            <div className="flex items-center gap-2 text-electric-blue font-semibold">
              <Lightbulb size={18} aria-hidden="true" />
              <span>AI Coach</span>
            </div>
          ) : (
            <Lightbulb size={20} className="text-electric-blue mx-auto" aria-hidden="true" />
          )}
          {isExpanded && <ChevronRight size={18} className="text-electric-blue" aria-hidden="true" />}
        </button>

        {/* Content */}
        {isExpanded && (
          <div id="coach-content" className="p-4 space-y-4">
            {/* Timer Warning - announced urgently */}
            {isTimeRunningOut && (
              <div
                className="flex items-start gap-3 p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 animate-pulse"
                role="alert"
                aria-live="assertive"
              >
                <Clock className="w-5 h-5 text-amber-500 shrink-0 mt-0.5" aria-hidden="true" />
                <div>
                  <p className="text-sm font-bold text-amber-600 dark:text-amber-400">Time is running out!</p>
                  <p className="text-xs text-text-secondary">Wrap up your answer in the next minute.</p>
                </div>
              </div>
            )}

            {/* Hint Carousel - hints announced to screen readers */}
            <div
              className="relative bg-surface-secondary rounded-xl p-4 min-h-[140px] flex flex-col justify-between border border-border-light"
              aria-live="polite"
              aria-atomic="true"
              aria-busy={resolvedLoading}
            >
              {resolvedHint ? (
                // Dynamic AI-generated hint
                <div>
                  <h4 className="font-bold text-text-primary mb-1 flex items-center gap-2">
                    <MessageSquare size={14} className="text-electric-blue" />
                    AI Suggestion
                    {resolvedStreaming && (
                      <span className="ml-1 inline-flex items-center gap-1 text-xs text-electric-blue">
                        <span className="relative flex h-2 w-2">
                          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-electric-blue opacity-75"></span>
                          <span className="relative inline-flex rounded-full h-2 w-2 bg-electric-blue"></span>
                        </span>
                        <span className="text-[10px] font-normal">Live</span>
                      </span>
                    )}
                  </h4>
                  <p className="text-sm text-text-secondary leading-relaxed relative">
                    {resolvedHint}
                    {resolvedStreaming && (
                      <span className="inline-block w-0.5 h-4 bg-electric-blue ml-1 animate-pulse" />
                    )}
                  </p>
                  {resolvedLoading && !resolvedStreaming && (
                    <div className="mt-2 flex items-center gap-2 text-xs text-text-tertiary">
                      <Loader2 size={12} className="animate-spin" />
                      <span>Updating hint...</span>
                    </div>
                  )}
                </div>
              ) : resolvedError ? (
                // Error state - fallback to static hints
                <div>
                  <div className="flex items-center gap-2 mb-2 text-amber-600 dark:text-amber-400">
                    <AlertCircle size={14} />
                    <span className="text-xs font-medium">Using default hints</span>
                  </div>
                  <h4 className="font-bold text-text-primary mb-1 flex items-center gap-2">
                    <MessageSquare size={14} className="text-electric-blue" />
                    {hints[activeHint].title}
                  </h4>
                  <p className="text-sm text-text-secondary leading-relaxed">
                    {hints[activeHint].text}
                  </p>
                  <div className="flex items-center justify-between mt-3 pt-3 border-t border-border-light/50">
                    <button
                      onClick={() => setActiveHint(prev => (prev - 1 + hints.length) % hints.length)}
                      className="p-1 hover:bg-white/50 rounded-full transition-colors"
                      title="Previous hint"
                    >
                      <ChevronLeft size={16} className="text-text-tertiary" />
                    </button>
                    <div className="flex gap-1">
                      {hints.map((_, idx) => (
                        <div
                          key={idx}
                          className={`w-1.5 h-1.5 rounded-full transition-colors ${idx === activeHint ? 'bg-electric-blue' : 'bg-border-medium'}`}
                        />
                      ))}
                    </div>
                    <button
                      onClick={() => setActiveHint(prev => (prev + 1) % hints.length)}
                      className="p-1 hover:bg-white/50 rounded-full transition-colors"
                      title="Next hint"
                    >
                      <ChevronRight size={16} className="text-text-tertiary" />
                    </button>
                  </div>
                </div>
              ) : isHintLoading ? (
                // Loading state
                <div className="flex flex-col items-center justify-center min-h-[100px]">
                  <Loader2 size={24} className="animate-spin text-electric-blue mb-2" />
                  <p className="text-sm text-text-secondary">Generating hint...</p>
                </div>
              ) : (
                // Default static hints
                <div>
                  <h4 className="font-bold text-text-primary mb-1 flex items-center gap-2">
                    <MessageSquare size={14} className="text-electric-blue" />
                    {hints[activeHint].title}
                  </h4>
                  <p className="text-sm text-text-secondary leading-relaxed">
                    {hints[activeHint].text}
                  </p>
                  <div className="flex items-center justify-between mt-3 pt-3 border-t border-border-light/50">
                    <button
                      onClick={() => setActiveHint(prev => (prev - 1 + hints.length) % hints.length)}
                      className="p-1 hover:bg-white/50 rounded-full transition-colors"
                      title="Previous hint"
                    >
                      <ChevronLeft size={16} className="text-text-tertiary" />
                    </button>
                    <div className="flex gap-1">
                      {hints.map((_, idx) => (
                        <div
                          key={idx}
                          className={`w-1.5 h-1.5 rounded-full transition-colors ${idx === activeHint ? 'bg-electric-blue' : 'bg-border-medium'}`}
                        />
                      ))}
                    </div>
                    <button
                      onClick={() => setActiveHint(prev => (prev + 1) % hints.length)}
                      className="p-1 hover:bg-white/50 rounded-full transition-colors"
                      title="Next hint"
                    >
                      <ChevronRight size={16} className="text-text-tertiary" />
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* STAR Framework Quick Ref (Behavioral only) */}
            {questionType === 'behavioral' && (
              <div className="bg-blue-50/50 dark:bg-blue-900/10 rounded-lg p-3 border border-blue-100 dark:border-blue-800/30">
                <div className="flex items-center gap-2 mb-2 text-xs font-bold text-blue-700 dark:text-blue-300 uppercase tracking-wider">
                  <Info size={12} />
                  STAR Framework
                </div>
                <div className="grid grid-cols-4 gap-1 text-center text-[10px]">
                  <div className="p-1.5 rounded bg-white dark:bg-surface-dark border border-blue-100 dark:border-blue-800/30 shadow-sm">
                    <div className="font-bold text-blue-600 dark:text-blue-400">S</div>
                    <div className="text-text-tertiary scale-90">Situation</div>
                  </div>
                  <div className="p-1.5 rounded bg-white dark:bg-surface-dark border border-blue-100 dark:border-blue-800/30 shadow-sm">
                    <div className="font-bold text-blue-600 dark:text-blue-400">T</div>
                    <div className="text-text-tertiary scale-90">Task</div>
                  </div>
                  <div className="p-1.5 rounded bg-white dark:bg-surface-dark border border-blue-100 dark:border-blue-800/30 shadow-sm">
                    <div className="font-bold text-blue-600 dark:text-blue-400">A</div>
                    <div className="text-text-tertiary scale-90">Action</div>
                  </div>
                  <div className="p-1.5 rounded bg-white dark:bg-surface-dark border border-blue-100 dark:border-blue-800/30 shadow-sm">
                    <div className="font-bold text-blue-600 dark:text-blue-400">R</div>
                    <div className="text-text-tertiary scale-90">Result</div>
                  </div>
                </div>
              </div>
            )}

            <button
              onClick={onClose}
              className="w-full py-2 text-xs text-text-tertiary hover:text-text-secondary flex items-center justify-center gap-1 transition-colors"
            >
              <X size={12} />
              Dismiss Coach
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
