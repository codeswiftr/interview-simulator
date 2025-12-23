import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { History, TrendingUp, BarChart3, Loader2, RefreshCw, Wand2 } from 'lucide-react';
import { usePreparation } from '../../contexts/PreparationContext';
import { useAudioRecording } from '../../hooks/useAudioRecording';
import { useCoachingHint } from '../../hooks/useCoachingHint';
import RecordingDeck from '../interview/RecordingDeck';
import CoachOverlay from '../interview/CoachOverlay';
import HintHistoryPanel from '../interview/HintHistoryPanel';
import ContextualTooltip from '../common/ContextualTooltip';

export default function PracticeStage() {
  const navigate = useNavigate();
  const {
    draft,
    qnaList,
    attempts,
    comparisonData,
    selectedAttemptForComparison,
    isSubmitting,
    isRating,
    setStage,
    handleStartPractice,
    handleSubmitPractice,
    handleRateAttempt,
    handleViewComparison,
    clearComparison,
    reloadAttempts,
  } = usePreparation();

  const [showCoach, setShowCoach] = useState(true);
  const [liveTranscript, setLiveTranscript] = useState<string>('');
  const [hintHistory, setHintHistory] = useState<Array<{ timestamp: Date; hint: string; stage: 'detective' | 'practice' }>>([]);
  const [isHintHistoryExpanded, setIsHintHistoryExpanded] = useState(false);

  // Audio recording hook
  const {
    duration,
    isRecording,
    recordingState,
    startRecording,
    stopRecording,
    resetRecording,
    clearPreview,
    pauseRecording,
    resumeRecording,
    confirmRecording,
    error: recordingError,
    mediaStream,
    mimeType,
  } = useAudioRecording();

  // Get question for coaching
  const practiceQuestion = qnaList.length > 0
    ? qnaList[0].question
    : 'Practice your prepared answer';

  // AI Coaching Hint hook
  const {
    hint: coachingHint,
    isLoading: isHintLoading,
    isStreaming: isHintStreaming,
    error: hintError
  } = useCoachingHint({
    question: practiceQuestion,
    questionType: 'behavioral',
    transcript: liveTranscript,
    enabled: isRecording && showCoach && !!draft
  });

  // Track hints in history
  useEffect(() => {
    if (coachingHint && !isHintStreaming && !isHintLoading) {
      setHintHistory((prev) => {
        const lastHint = prev[prev.length - 1];
        if (lastHint && lastHint.hint === coachingHint) {
          return prev;
        }
        return [
          ...prev,
          {
            timestamp: new Date(),
            hint: coachingHint,
            stage: 'practice' as const,
          },
        ].slice(-20);
      });
    }
  }, [coachingHint, isHintStreaming, isHintLoading]);

  const handleTranscriptChange = useCallback((transcript: string) => {
    setLiveTranscript(transcript);
  }, []);

  const handleStartRecording = async () => {
    try {
      await handleStartPractice();
      await startRecording();
    } catch {
      // Error handled by context
    }
  };

  const handleStopRecording = () => {
    stopRecording();
  };

  const handleCancelRecording = () => {
    clearPreview();
    resetRecording();
  };

  const handleConfirmRecording = async () => {
    const blob = confirmRecording();
    if (!blob) return;
    await handleSubmitPractice(blob, mimeType);
    resetRecording();
    await reloadAttempts();
  };

  const handleTryAgain = () => {
    clearComparison();
    resetRecording();
    handleStartPractice();
  };

  const handleRefineDraft = () => {
    clearComparison();
    setStage('draft');
  };

  return (
    <div className="space-y-6">
      {/* Draft Display */}
      <div className="card p-6">
        <h2 className="heading-card mb-4">Your Draft Answer</h2>
        <div className="bg-surface-secondary p-4 rounded-lg">
          <div className="prose prose-sm max-w-none dark:prose-invert">
            <pre className="whitespace-pre-wrap font-sans text-text-primary text-sm">{draft}</pre>
          </div>
        </div>
      </div>

      {/* Recording Interface */}
      <div className="card p-6">
        <div className="flex items-center gap-2 mb-4">
          <h2 className="heading-card">Practice Your Delivery</h2>
          <ContextualTooltip
            content="Record yourself speaking your draft answer naturally. Practice multiple times to improve. Our AI coach will provide real-time hints while you speak. After recording, you can get feedback comparing your delivery to your draft."
            position="right"
            trigger="click"
            title="Practice Tips"
          />
        </div>
        <p className="text-text-secondary mb-6">
          Record yourself delivering your prepared answer. You can practice multiple times.
        </p>

        {recordingError && (
          <div className="mb-4 p-4 bg-status-error/10 border border-status-error/20 rounded-lg">
            <p className="text-status-error text-sm">{recordingError}</p>
          </div>
        )}

        <div className="relative">
          <RecordingDeck
            isRecording={isRecording}
            recordingState={recordingState}
            duration={duration}
            mediaStream={mediaStream}
            onStart={handleStartRecording}
            onStop={handleStopRecording}
            onPause={pauseRecording}
            onResume={resumeRecording}
            onCancel={handleCancelRecording}
            onConfirm={handleConfirmRecording}
            disabled={isSubmitting}
            onTranscriptChange={handleTranscriptChange}
          />

          {/* AI Coaching Overlay */}
          {isRecording && showCoach && (
            <CoachOverlay
              hint={coachingHint}
              isLoading={isHintLoading}
              isStreaming={isHintStreaming}
              error={hintError}
              onClose={() => setShowCoach(false)}
              onToggle={() => setShowCoach(!showCoach)}
              isCollapsed={!showCoach}
            />
          )}
        </div>

        {isSubmitting && (
          <div className="mt-4 text-center">
            <Loader2 size={20} className="animate-spin text-electric-blue mx-auto mb-2" />
            <p className="text-text-secondary text-sm">Submitting and transcribing...</p>
            <p className="text-xs text-text-tertiary mt-1">This may take 10-20 seconds</p>
          </div>
        )}

        {/* Hint History Panel */}
        {hintHistory.length > 0 && (
          <div className="mt-6">
            <HintHistoryPanel
              hints={hintHistory}
              isExpanded={isHintHistoryExpanded}
              onToggle={() => setIsHintHistoryExpanded(!isHintHistoryExpanded)}
            />
          </div>
        )}
      </div>

      {/* Attempt History */}
      {attempts.length > 0 && (
        <div className="card p-6">
          <div className="flex items-center gap-2 mb-4">
            <History size={20} className="text-electric-blue" />
            <h2 className="heading-card">Practice History</h2>
          </div>
          <div className="space-y-4">
            {attempts.map((attempt) => (
              <div key={attempt.id} className="bg-surface-secondary p-4 rounded-lg border border-border-light">
                <div className="flex items-start justify-between mb-2">
                  <span className="text-xs text-text-tertiary">
                    {new Date(attempt.created_at).toLocaleString()}
                  </span>
                  <div className="flex items-center gap-2">
                    {attempt.delivery_score !== null ? (
                      <>
                        <span className="text-sm font-semibold text-electric-blue">
                          Score: {attempt.delivery_score.toFixed(1)}%
                        </span>
                        <button
                          onClick={() => handleViewComparison(attempt.id)}
                          className="text-xs text-electric-blue hover:underline"
                        >
                          View Comparison
                        </button>
                      </>
                    ) : (
                      attempt.transcript && (
                        <button
                          onClick={() => handleRateAttempt(attempt.id)}
                          disabled={isRating}
                          className="btn-secondary text-xs"
                        >
                          {isRating ? (
                            <>
                              <Loader2 size={12} className="animate-spin" />
                              <span className="flex items-center gap-1">
                                Rating...
                                <span className="text-xs opacity-75">(5-10s)</span>
                              </span>
                            </>
                          ) : (
                            <>
                              <BarChart3 size={12} />
                              Rate Delivery
                            </>
                          )}
                        </button>
                      )
                    )}
                  </div>
                </div>
                {attempt.transcript && (
                  <p className="text-text-secondary text-sm mt-2 line-clamp-2">{attempt.transcript}</p>
                )}
                {attempt.comparison_feedback && (
                  <div className="mt-3 p-3 bg-surface-primary rounded border border-border-light">
                    <p className="text-xs font-semibold text-text-primary mb-1">Feedback:</p>
                    <p className="text-xs text-text-secondary">{attempt.comparison_feedback}</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Comparison View */}
      {comparisonData && selectedAttemptForComparison && (
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <TrendingUp size={20} className="text-electric-blue" />
              <h2 className="heading-card">Delivery Comparison</h2>
            </div>
            <button
              onClick={clearComparison}
              className="text-sm text-text-tertiary hover:text-text-primary"
            >
              Close
            </button>
          </div>

          {comparisonData.delivery_score !== null && (
            <div className="mb-6 p-4 bg-electric-blue/10 border border-electric-blue/20 rounded-lg">
              <div className="flex items-center gap-4">
                <div>
                  <p className="text-xs text-text-tertiary mb-1">Overall Score</p>
                  <p className="text-3xl font-bold text-electric-blue">
                    {comparisonData.delivery_score.toFixed(1)}%
                  </p>
                </div>
                {comparisonData.strengths.length > 0 && (
                  <div className="flex-1">
                    <p className="text-xs text-text-tertiary mb-1">Strengths</p>
                    <ul className="text-sm text-text-primary list-disc list-inside">
                      {comparisonData.strengths.map((strength, idx) => (
                        <li key={idx}>{strength}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          )}

          <div className="grid md:grid-cols-2 gap-4 mb-4">
            <div className="bg-surface-secondary p-4 rounded-lg">
              <h3 className="text-sm font-semibold text-text-primary mb-2">Your Draft (Planned)</h3>
              <div className="prose prose-sm max-w-none dark:prose-invert">
                <pre className="whitespace-pre-wrap font-sans text-text-primary text-sm bg-surface-primary p-3 rounded">
                  {comparisonData.draft}
                </pre>
              </div>
            </div>
            <div className="bg-surface-secondary p-4 rounded-lg">
              <h3 className="text-sm font-semibold text-text-primary mb-2">Your Delivery (Actual)</h3>
              <p className="text-text-primary text-sm bg-surface-primary p-3 rounded whitespace-pre-wrap">
                {comparisonData.delivery}
              </p>
            </div>
          </div>

          {comparisonData.comparison_feedback && (
            <div className="mt-4 p-4 bg-surface-secondary rounded-lg border border-border-light">
              <p className="text-sm font-semibold text-text-primary mb-2">Detailed Feedback</p>
              <p className="text-sm text-text-secondary whitespace-pre-wrap">
                {comparisonData.comparison_feedback}
              </p>
            </div>
          )}

          {comparisonData.improvements.length > 0 && (
            <div className="mt-4 p-4 bg-status-warning/10 border border-status-warning/20 rounded-lg">
              <p className="text-sm font-semibold text-text-primary mb-2">Improvements</p>
              <ul className="text-sm text-text-secondary list-disc list-inside space-y-1">
                {comparisonData.improvements.map((improvement, idx) => (
                  <li key={idx}>{improvement}</li>
                ))}
              </ul>
            </div>
          )}

          <div className="mt-6 flex items-center gap-4 pt-4 border-t border-border-light">
            <button
              onClick={handleTryAgain}
              className="btn-secondary flex items-center gap-2"
            >
              <RefreshCw size={16} />
              Try Again
            </button>
            <button
              onClick={handleRefineDraft}
              className="btn-secondary flex items-center gap-2"
            >
              <Wand2 size={16} />
              Refine Draft
            </button>
            <button
              onClick={clearComparison}
              className="btn-ghost"
            >
              Done
            </button>
          </div>
        </div>
      )}

      <div className="flex items-center gap-4">
        <button
          onClick={() => setStage('draft')}
          className="btn-secondary"
        >
          Back to Draft
        </button>
        <button
          onClick={() => navigate('/questions')}
          className="btn-ghost"
        >
          Done
        </button>
      </div>
    </div>
  );
}
