import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Sparkles, AlertCircle } from 'lucide-react';
import { PreparationProvider, usePreparation } from '../contexts/PreparationContext';
import { DetectiveStage, DraftStage, PracticeStage } from '../components/preparation';

function PreparationContent() {
  const navigate = useNavigate();
  const {
    stage,
    questionContext,
    isComplete,
    draft,
    error,
    setError,
  } = usePreparation();

  return (
    <div className="min-h-screen bg-surface-primary">
      <div className="container mx-auto px-6 py-8 max-w-4xl">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => navigate('/questions')}
            className="btn-ghost flex items-center gap-2 mb-4"
          >
            <ArrowLeft size={20} />
            Back to Questions
          </button>
          <div className="flex items-center gap-3 mb-2">
            <Sparkles className="w-8 h-8 text-electric-blue" />
            <h1 className="heading-page">Prepare Your Answer</h1>
          </div>
          <p className="text-text-secondary">
            Answer a few questions to get a personalized, STAR-formatted draft answer.
          </p>
        </div>

        {/* Question Context */}
        {questionContext && (
          <div className="card p-4 mb-6">
            <p className="font-semibold text-text-primary mb-1">Question</p>
            <p className="text-text-secondary">{questionContext.content}</p>
            <div className="flex flex-wrap gap-3 text-xs text-text-tertiary mt-3">
              {questionContext.category && <span>Type: {questionContext.category}</span>}
              {questionContext.difficulty && <span>Difficulty: {questionContext.difficulty}</span>}
              {questionContext.company_tags && questionContext.company_tags.length > 0 && (
                <span>Companies: {questionContext.company_tags.join(', ')}</span>
              )}
            </div>
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div className="card p-4 mb-6 border-status-error/20 bg-status-error/5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3 text-status-error">
                <AlertCircle size={20} />
                <p className="body-small">{error}</p>
              </div>
              <button
                onClick={() => setError(null)}
                className="text-xs text-status-error hover:underline"
                aria-label="Dismiss error"
              >
                Dismiss
              </button>
            </div>
            {(error.includes('network') || error.includes('connection') || error.includes('failed')) && (
              <div className="mt-3 pt-3 border-t border-status-error/20">
                <p className="text-xs text-text-secondary mb-2">Try:</p>
                <ul className="text-xs text-text-secondary list-disc list-inside space-y-1">
                  <li>Check your internet connection</li>
                  <li>Refresh the page and try again</li>
                  <li>Wait a moment and retry</li>
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Stage Content */}
        {stage === 'detective' && !isComplete && <DetectiveStage />}

        {stage === 'draft' && isComplete && !draft && <DraftStage showGenerateButton />}

        {draft && stage !== 'practice' && <DraftStage />}

        {stage === 'practice' && draft && <PracticeStage />}
      </div>
    </div>
  );
}

export default function PreparationPage() {
  return (
    <PreparationProvider>
      <PreparationContent />
    </PreparationProvider>
  );
}
