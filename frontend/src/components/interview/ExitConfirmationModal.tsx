import { useEffect, useRef } from 'react';
import { useInterview } from '../../contexts/InterviewContext';

export default function ExitConfirmationModal() {
  const { showExitModal, cancelExit, confirmExit } = useInterview();
  const modalRef = useRef<HTMLDivElement>(null);
  const previousFocusRef = useRef<HTMLElement | null>(null);

  // Focus management
  useEffect(() => {
    if (showExitModal) {
      previousFocusRef.current = document.activeElement as HTMLElement;
      modalRef.current?.focus();
    } else if (previousFocusRef.current) {
      previousFocusRef.current.focus();
    }
  }, [showExitModal]);

  // Handle escape key
  useEffect(() => {
    if (!showExitModal) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        cancelExit();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [showExitModal, cancelExit]);

  if (!showExitModal) {
    return null;
  }

  return (
    <div
      className="fixed inset-0 bg-charcoal/60 backdrop-blur-sm flex items-center justify-center p-6 z-[100] animate-fade-in"
      role="dialog"
      aria-modal="true"
      aria-labelledby="exit-modal-title"
      aria-describedby="exit-modal-description"
    >
      <div
        ref={modalRef}
        tabIndex={-1}
        className="card p-8 max-w-md w-full shadow-2xl animate-scale-in outline-none"
      >
        <h3 id="exit-modal-title" className="heading-card mb-4 text-text-primary">
          Exit Interview?
        </h3>
        <p id="exit-modal-description" className="text-text-secondary mb-8 leading-relaxed">
          Are you sure you want to exit? Your progress will be saved, but you won't be able to resume this session.
        </p>
        <div className="flex gap-4">
          <button
            onClick={cancelExit}
            className="btn-secondary flex-1 justify-center"
          >
            Continue
          </button>
          <button
            onClick={confirmExit}
            className="btn-primary flex-1 justify-center bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 shadow-red-500/20"
          >
            Exit
          </button>
        </div>
      </div>
    </div>
  );
}
