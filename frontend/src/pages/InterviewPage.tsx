import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { AlertCircle } from 'lucide-react';
import { ErrorBoundary } from '../components/ErrorBoundary';
import { InterviewProvider, useInterview } from '../contexts/InterviewContext';
import {
  InterviewHeader,
  RecordingSection,
  TranscriptionPanel,
  ExitConfirmationModal,
  QuestionDisplay,
} from '../components/interview';
import { SkeletonQuestion } from '../components/ui/Skeleton';

function InterviewContent() {
  const navigate = useNavigate();
  const {
    session,
    questions,
    currentQuestionIndex,
    currentQuestion,
    isLoading,
    error,
  } = useInterview();

  // Warn user before leaving with unsaved progress
  useEffect(() => {
    const hasUnsavedProgress = currentQuestionIndex > 0;

    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (hasUnsavedProgress) {
        e.preventDefault();
        e.returnValue = '';
        return '';
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [currentQuestionIndex]);

  // Loading state
  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <SkeletonQuestion />
      </div>
    );
  }

  // Error state (no session loaded)
  if (error && !session) {
    return (
      <div className="min-h-screen bg-surface-primary flex items-center justify-center p-6">
        <div
          className="card p-8 max-w-md w-full border-status-error/20 bg-status-error/5"
          role="alert"
        >
          <div className="flex items-center gap-3 text-status-error mb-4">
            <AlertCircle size={24} aria-hidden="true" />
            <h2 className="heading-card">Failed to load interview</h2>
          </div>
          <p className="text-text-secondary mb-6">{error}</p>
          <button onClick={() => navigate('/dashboard')} className="btn-primary w-full">
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-surface-primary flex flex-col">
      {/* Header with timer, progress, controls */}
      <InterviewHeader />

      {/* Main Content */}
      <div className="flex-1 container mx-auto px-6 py-8 max-w-4xl flex flex-col justify-center min-h-[calc(100vh-80px)] relative">
        {/* Error Alert */}
        {error && (
          <div
            className="card p-4 mb-6 border-status-error/20 bg-status-error/5 animate-fade-in"
            role="alert"
            aria-live="assertive"
          >
            <div className="flex items-center gap-3 text-status-error">
              <AlertCircle size={20} aria-hidden="true" />
              <p className="body-small">{error}</p>
            </div>
          </div>
        )}

        {/* Question Display */}
        {currentQuestion && (
          <div className="mb-12">
            <QuestionDisplay
              question={currentQuestion}
              questionNumber={currentQuestionIndex + 1}
              totalQuestions={questions.length}
            />
          </div>
        )}

        {/* Recording Section */}
        <RecordingSection />

        {/* Transcription Panel */}
        <TranscriptionPanel />
      </div>

      {/* Exit Confirmation Modal */}
      <ExitConfirmationModal />
    </div>
  );
}

export default function InterviewPage() {
  return (
    <ErrorBoundary>
      <InterviewProvider>
        <InterviewContent />
      </InterviewProvider>
    </ErrorBoundary>
  );
}
