import { useState, useCallback } from 'react';
import { SkipForward, RefreshCw, Video } from 'lucide-react';
import { useInterview } from '../../contexts/InterviewContext';
import { useAudioRecording } from '../../hooks/useAudioRecording';
import { useCoachingHint } from '../../hooks/useCoachingHint';
import { analytics, Events } from '../../lib/analytics';
import { Card } from '../ui/Card';
import RecordingDeck from './RecordingDeck';
import AudioPreview from './AudioPreview';
import CoachOverlay from './CoachOverlay';
import VideoRecordingDeck from './VideoRecordingDeck';

export default function RecordingSection() {
  const {
    session,
    currentQuestion,
    isSubmitting,
    submitProgress,
    showCoach,
    setShowCoach,
    lastFailedUpload,
    lastSubmittedResponseId,
    clearLastSubmittedResponseId,
    handleSubmitAnswer,
    handleSkipQuestion,
    handleRetryUpload,
    handleExit,
    setError,
  } = useInterview();

  // Audio recording hook
  const {
    duration,
    isRecording,
    recordingState,
    isPreviewMode,
    isPlaying,
    currentTime,
    audioDuration,
    startRecording,
    stopRecording,
    resetRecording,
    playPreview,
    pausePreview,
    clearPreview,
    pauseRecording,
    resumeRecording,
    confirmRecording,
    error: recordingError,
    mediaStream,
    mimeType
  } = useAudioRecording();

  // Local UI state
  const [showVideoRecorder, setShowVideoRecorder] = useState(false);

  // Live transcript state for coaching
  const [liveTranscript, setLiveTranscript] = useState('');

  // AI Coaching Hint hook
  const {
    hint: coachingHint,
    isLoading: isHintLoading,
    isStreaming: isHintStreaming,
    error: hintError
  } = useCoachingHint({
    question: currentQuestion?.content || '',
    questionType: (currentQuestion?.category as 'behavioral' | 'technical' | 'system_design') || 'behavioral',
    transcript: liveTranscript,
    enabled: isRecording && showCoach && !!currentQuestion
  });

  // Handle transcript updates from RecordingDeck
  const handleTranscriptChange = useCallback((transcript: string) => {
    setLiveTranscript(transcript);
  }, []);

  const handleStartRecording = async () => {
    try {
      await startRecording();
      // Track recording started
      if (session && currentQuestion) {
        analytics.track(Events.RECORDING_STARTED, {
          interview_id: session.id,
          question_id: currentQuestion.id,
        });
      }
    } catch (err) {
      const error = err as { message?: string };
      setError(error.message || 'Failed to start recording');
    }
  };

  const handleStopRecording = () => {
    stopRecording();
  };

  const handleReRecord = () => {
    clearPreview();
    setError(null);
  };

  const handleConfirmSubmit = async () => {
    const blob = confirmRecording();
    if (!blob) {
      setError('No recording available to submit');
      return;
    }
    await handleSubmitAnswer(blob, mimeType, duration);
    resetRecording();
  };

  const handleRetry = async () => {
    await handleRetryUpload(duration);
    resetRecording();
  };

  return (
    <div className="relative z-20">
      {/* Coach Overlay */}
      {currentQuestion && (
        <CoachOverlay
          isVisible={showCoach}
          onClose={() => setShowCoach(false)}
          questionType={currentQuestion.category}
          elapsedTime={duration}
          expectedDuration={currentQuestion.expected_duration_seconds}
          dynamicHint={coachingHint}
          isHintLoading={isHintLoading}
          isHintStreaming={isHintStreaming}
          hintError={hintError}
        />
      )}

      <Card variant="glass" className="p-4 sm:p-8 shadow-xl border-white/50 bg-white/80 backdrop-blur-xl">
        {isPreviewMode ? (
          /* Preview Mode */
          <AudioPreview
            isPlaying={isPlaying}
            currentTime={currentTime}
            duration={audioDuration}
            onPlay={playPreview}
            onPause={pausePreview}
            onReRecord={handleReRecord}
            onConfirm={handleConfirmSubmit}
            disabled={isSubmitting}
            isSubmitting={isSubmitting}
            submitProgress={submitProgress}
          />
        ) : (
          /* Recording Mode */
          <RecordingDeck
            isRecording={isRecording}
            recordingState={recordingState}
            duration={duration}
            mediaStream={mediaStream}
            onStart={handleStartRecording}
            onStop={handleStopRecording}
            onPause={pauseRecording}
            onResume={resumeRecording}
            onCancel={handleExit}
            onConfirm={handleConfirmSubmit}
            onSkip={handleSkipQuestion}
            disabled={isSubmitting}
            onTranscriptChange={handleTranscriptChange}
          />
        )}

        {/* Recording Error */}
        {recordingError && (
          <div className="mt-4 p-3 bg-status-error/10 border border-status-error/20 rounded-lg">
            <p className="text-sm text-status-error">{recordingError}</p>
          </div>
        )}
      </Card>

      {/* Secondary Actions - Outside the deck for cleaner UI */}
      {!isPreviewMode && (
        <div className="mt-6 flex flex-wrap justify-center gap-3 sm:gap-4">
          <button
            onClick={handleSkipQuestion}
            disabled={isSubmitting || isRecording}
            className="btn-ghost flex items-center justify-center gap-2 text-text-tertiary hover:text-text-secondary min-h-[44px] px-4"
          >
            <SkipForward size={20} />
            Skip Question
          </button>

          {lastFailedUpload && (
            <button
              onClick={handleRetry}
              disabled={isSubmitting}
              className="btn-primary flex items-center justify-center gap-2 bg-amber-500 hover:bg-amber-600 border-none min-h-[44px]"
            >
              <RefreshCw size={20} className={isSubmitting ? 'animate-spin' : ''} />
              {isSubmitting ? 'Retrying...' : 'Retry Upload'}
            </button>
          )}
        </div>
      )}

      {/* Optional Video Recording — after audio submission */}
      {lastSubmittedResponseId && !isRecording && !isSubmitting && (
        <div className="mt-6">
          {!showVideoRecorder ? (
            <div className="flex justify-center">
              <button
                onClick={() => setShowVideoRecorder(true)}
                className="flex items-center gap-2 px-4 py-2 text-sm text-indigo-600 border border-indigo-200 rounded-lg hover:bg-indigo-50 transition-colors"
              >
                <Video size={16} />
                Add video for your last answer
              </button>
            </div>
          ) : (
            <VideoRecordingDeck
              responseId={lastSubmittedResponseId}
              onUploadComplete={() => {
                setShowVideoRecorder(false);
                clearLastSubmittedResponseId();
              }}
              onUploadError={() => {
                // Keep the recorder open on error so user can retry
              }}
              onCancel={() => {
                setShowVideoRecorder(false);
                clearLastSubmittedResponseId();
              }}
            />
          )}
        </div>
      )}
    </div>
  );
}
