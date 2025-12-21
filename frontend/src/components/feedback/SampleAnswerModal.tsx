import { X, Lightbulb, BookOpen } from 'lucide-react';
import { useFocusTrap } from '../../hooks/useFocusTrap';

interface SampleAnswerModalProps {
  isOpen: boolean;
  onClose: () => void;
  question: string;
  sampleAnswer: string;
  questionNumber: number;
}

export default function SampleAnswerModal({
  isOpen,
  onClose,
  question,
  sampleAnswer,
  questionNumber,
}: SampleAnswerModalProps) {
  const containerRef = useFocusTrap({
    isActive: isOpen,
    onEscape: onClose,
  });

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-charcoal/50 dark:bg-dark-charcoal/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div
        ref={containerRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="sample-answer-modal-title"
        className="card max-w-2xl w-full max-h-[85vh] flex flex-col p-0 animate-[scale-in_0.2s_ease-out]"
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-border-light dark:border-dark-border">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-electric-blue/10 text-electric-blue flex items-center justify-center">
              <Lightbulb size={20} aria-hidden="true" />
            </div>
            <div>
              <h2 id="sample-answer-modal-title" className="heading-section">Sample Answer</h2>
              <p className="body-small text-text-secondary dark:text-dark-text-secondary">
                Question {questionNumber}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-surface-secondary dark:hover:bg-dark-surface-tertiary rounded-lg transition-colors"
            aria-label="Close sample answer"
          >
            <X size={24} className="text-text-secondary dark:text-dark-text-secondary" aria-hidden="true" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Question */}
          <div>
            <h4 className="body-small font-semibold text-text-secondary dark:text-dark-text-secondary uppercase tracking-wide mb-2 flex items-center gap-2">
              <BookOpen className="w-4 h-4" />
              Question
            </h4>
            <div className="bg-surface-secondary dark:bg-dark-surface-tertiary rounded-lg p-4">
              <p className="body-large font-medium text-text-primary dark:text-dark-text-primary">
                {question}
              </p>
            </div>
          </div>

          {/* Sample Answer */}
          <div>
            <h4 className="body-small font-semibold text-text-secondary dark:text-dark-text-secondary uppercase tracking-wide mb-2 flex items-center gap-2">
              <Lightbulb className="w-4 h-4 text-electric-blue" />
              Recommended Answer Structure
            </h4>
            <div className="bg-electric-blue/5 dark:bg-electric-blue/10 border border-electric-blue/20 rounded-lg p-5">
              <p className="body-default text-text-primary dark:text-dark-text-primary whitespace-pre-wrap leading-relaxed">
                {sampleAnswer}
              </p>
            </div>
          </div>

          {/* Tip */}
          <div className="bg-status-info/5 dark:bg-status-info/10 border border-status-info/20 rounded-lg p-4">
            <p className="body-small text-text-secondary dark:text-dark-text-secondary">
              <strong>Tip:</strong> Use this as a reference for structure and key points.
              Your own experiences and examples will make your answer unique and authentic.
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-border-light dark:border-dark-border">
          <button
            onClick={onClose}
            className="btn-secondary w-full"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
