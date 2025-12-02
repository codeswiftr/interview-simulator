import { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { X, AlertCircle, SkipForward, RefreshCw, ChevronDown, ChevronUp } from 'lucide-react';
import { ErrorBoundary } from '../components/ErrorBoundary';
import { interviewsAPI, responsesAPI, uploadAPI } from '../lib/api';
import { useAudioRecording } from '../hooks/useAudioRecording';
import { useToast } from '../hooks/useToast';
import Timer from '../components/interview/Timer';
import RecordingIndicator from '../components/interview/RecordingIndicator';
import RecordButton from '../components/interview/RecordButton';
import QuestionDisplay from '../components/interview/QuestionDisplay';
import AudioPreview from '../components/interview/AudioPreview';
import TranscriptionDisplay from '../components/interview/TranscriptionDisplay';
import type { InterviewSession, Question, InterviewResponse, ProcessingStatus } from '../types';

const MAX_RETRY_ATTEMPTS = 3;
const RETRY_DELAY_MS = 1000;
const TRANSCRIPTION_POLL_INTERVAL = 3000; // Poll every 3 seconds

// Simplified response for transcription tracking
interface SubmittedResponse {
  id: string;
  questionIndex: number;
  processingStatus: ProcessingStatus;
  transcript?: string;
  processingError?: string;
}

export default function InterviewPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const toast = useToast();

  // Session state
  const [session, setSession] = useState<InterviewSession | null>(null);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [sessionStartTime, setSessionStartTime] = useState<number | null>(null);

  // Transcription state
  const [submittedResponses, setSubmittedResponses] = useState<SubmittedResponse[]>([]);
  const [showTranscriptionPanel, setShowTranscriptionPanel] = useState(false);
  const pollingIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // UI state
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitProgress, setSubmitProgress] = useState<'uploading' | 'processing' | null>(null);
  const [showExitModal, setShowExitModal] = useState(false);
  const [lastFailedUpload, setLastFailedUpload] = useState<{ blob: Blob; questionId: string } | null>(null);

  // Audio recording hook
  const {
    recordingState,
    duration,
    isRecording,
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
    confirmRecording,
    error: recordingError,
  } = useAudioRecording();

  // Warn user before leaving with unsaved progress
  useEffect(() => {
    const hasUnsavedProgress = isRecording || isPreviewMode || currentQuestionIndex > 0;

    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (hasUnsavedProgress) {
        e.preventDefault();
        // Modern browsers ignore custom messages, but we still need to set returnValue
        e.returnValue = '';
        return '';
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);

    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, [isRecording, isPreviewMode, currentQuestionIndex]);

  // Load interview session and questions
  useEffect(() => {
    if (!id) return;

    const loadInterview = async () => {
      try {
        setIsLoading(true);
        setError(null);

        // Fetch session details
        const sessionResponse = await interviewsAPI.getById(id);
        const sessionData = sessionResponse.data;
        setSession(sessionData);

        // Start the session if it's scheduled (this assigns questions on backend)
        if (sessionData.status === 'scheduled') {
          const startResponse = await interviewsAPI.start(id);
          setSession(startResponse.data);
        }

        // Set session start time
        setSessionStartTime(Date.now());

        // Fetch assigned questions from the backend
        const questionsResponse = await interviewsAPI.getQuestions(id);
        setQuestions(questionsResponse.data);
      } catch (err) {
        const error = err as { response?: { data?: { message?: string } } };
        setError(error.response?.data?.message || 'Failed to load interview');
      } finally {
        setIsLoading(false);
      }
    };

    loadInterview();
  }, [id]);

  // Poll for transcription status updates
  // Use a ref to track submitted responses to avoid re-triggering the effect
  const submittedResponsesRef = useRef<SubmittedResponse[]>([]);
  submittedResponsesRef.current = submittedResponses;

  useEffect(() => {
    if (!session) return;

    const pollTranscriptions = async () => {
      const currentResponses = submittedResponsesRef.current;

      // Skip polling if no responses yet or all are done
      if (currentResponses.length === 0) return;

      const processingResponses = currentResponses.filter(
        r => r.processingStatus !== 'completed' && r.processingStatus !== 'failed'
      );

      // Skip API call if nothing to poll, but keep interval running for future submissions
      if (processingResponses.length === 0) return;

      try {
        // Fetch all responses for the session
        const { data: responses } = await interviewsAPI.getResponses(session.id);

        // Update our tracked responses with new data
        setSubmittedResponses(prev => prev.map(tracked => {
          const updated = responses.find((r: InterviewResponse) => r.id === tracked.id);
          if (updated) {
            // Notify user when transcription completes
            if (tracked.processingStatus !== 'completed' && updated.processing_status === 'completed') {
              toast.success('Transcription ready', `Answer ${tracked.questionIndex + 1} has been transcribed`);
            }
            return {
              ...tracked,
              processingStatus: updated.processing_status,
              transcript: updated.transcript,
              processingError: updated.processing_error,
            };
          }
          return tracked;
        }));
      } catch (err) {
        // Silently handle polling errors
        console.error('Failed to poll transcription status:', err);
      }
    };

    // Start polling interval when session is available - runs for the duration of the interview
    pollingIntervalRef.current = setInterval(pollTranscriptions, TRANSCRIPTION_POLL_INTERVAL);

    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
    };
  }, [session, toast]);

  // Handle recording start
  const handleStartRecording = async () => {
    try {
      await startRecording();
    } catch (err) {
      const error = err as { message?: string };
      setError(error.message || 'Failed to start recording');
    }
  };

  // Handle recording stop (enters preview mode)
  const handleStopRecording = () => {
    stopRecording();
    // Note: preview mode is now handled by the hook
  };

  // Handle re-record
  const handleReRecord = () => {
    clearPreview();
    setError(null);
  };

  // Upload with retry logic
  const uploadWithRetry = useCallback(async (
    blob: Blob,
    sessionId: string,
    questionId: string,
    attempt: number = 1
  ): Promise<string> => {
    try {
      const audioFile = new File([blob], `answer-${currentQuestionIndex + 1}.webm`, {
        type: 'audio/webm',
      });

      const uploadResponse = await uploadAPI.uploadAudio(audioFile, sessionId, questionId);
      return uploadResponse.data.audio_url;
    } catch (err) {
      if (attempt < MAX_RETRY_ATTEMPTS) {
        toast.warning('Upload failed', `Retrying... (attempt ${attempt + 1}/${MAX_RETRY_ATTEMPTS})`);
        await new Promise(resolve => setTimeout(resolve, RETRY_DELAY_MS * attempt));
        return uploadWithRetry(blob, sessionId, questionId, attempt + 1);
      }
      throw err;
    }
  }, [currentQuestionIndex, toast]);

  // Handle retry failed upload
  const handleRetryUpload = async () => {
    if (!lastFailedUpload || !session) return;

    try {
      setIsSubmitting(true);
      setError(null);

      const audioUrl = await uploadWithRetry(
        lastFailedUpload.blob,
        session.id,
        lastFailedUpload.questionId
      );

      await responsesAPI.submit(session.id, {
        question_id: lastFailedUpload.questionId,
        audio_url: audioUrl,
        duration_seconds: duration,
      });

      toast.success('Answer submitted', 'Your response was uploaded successfully');
      setLastFailedUpload(null);

      if (currentQuestionIndex < questions.length - 1) {
        setCurrentQuestionIndex(currentQuestionIndex + 1);
        resetRecording();
      } else {
        await handleEndInterview();
      }
    } catch (err) {
      const error = err as { response?: { data?: { message?: string } } };
      toast.error('Upload failed', 'Please check your connection and try again');
      setError(error.response?.data?.message || 'Failed to upload. Click retry to try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle submit answer
  const handleSubmitAnswer = async () => {
    if (!session || !questions[currentQuestionIndex]) {
      return;
    }

    // Confirm recording and get the blob
    const blob = confirmRecording();
    if (!blob) {
      setError('No recording available to submit');
      return;
    }

    try {
      setIsSubmitting(true);
      setSubmitProgress('uploading');
      setError(null);
      setLastFailedUpload(null);

      const currentQuestion = questions[currentQuestionIndex];

      // Upload audio file with retry
      const audioUrl = await uploadWithRetry(blob, session.id, currentQuestion.id);

      // Submit response
      setSubmitProgress('processing');
      const submitResponse = await responsesAPI.submit(session.id, {
        question_id: currentQuestion.id,
        audio_url: audioUrl,
        duration_seconds: duration,
      });

      // Track this response for transcription polling
      const responseData = submitResponse.data;
      setSubmittedResponses(prev => [...prev, {
        id: responseData.id,
        questionIndex: currentQuestionIndex,
        processingStatus: responseData.processing_status || 'pending',
        transcript: responseData.transcript,
        processingError: responseData.processing_error,
      }]);

      // Auto-expand transcription panel when first answer is submitted
      if (submittedResponses.length === 0) {
        setShowTranscriptionPanel(true);
      }

      toast.success('Answer submitted', 'Your answer is being transcribed...');

      // Move to next question or finish
      if (currentQuestionIndex < questions.length - 1) {
        setCurrentQuestionIndex(currentQuestionIndex + 1);
        resetRecording();
      } else {
        // All questions answered, end the session
        await handleEndInterview();
      }
    } catch (err) {
      const error = err as { response?: { data?: { message?: string } } };
      setError(error.response?.data?.message || 'Failed to submit answer. Click retry to try again.');
      setLastFailedUpload({ blob, questionId: questions[currentQuestionIndex].id });
      toast.error('Upload failed', 'Your answer could not be uploaded. Please retry.');
    } finally {
      setIsSubmitting(false);
      setSubmitProgress(null);
    }
  };

  // Handle skip question
  const handleSkipQuestion = async () => {
    if (!session || !questions[currentQuestionIndex]) {
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);

      const currentQuestion = questions[currentQuestionIndex];

      // Submit empty response
      await responsesAPI.submit(session.id, {
        question_id: currentQuestion.id,
        audio_url: '',
        duration_seconds: 0,
      });

      // Move to next question or finish
      if (currentQuestionIndex < questions.length - 1) {
        setCurrentQuestionIndex(currentQuestionIndex + 1);
        resetRecording();
      } else {
        // All questions answered, end the session
        await handleEndInterview();
      }
    } catch (err) {
      const error = err as { response?: { data?: { message?: string } } };
      setError(error.response?.data?.message || 'Failed to skip question');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle end interview
  const handleEndInterview = async () => {
    if (!id) return;

    try {
      await interviewsAPI.end(id);
      navigate(`/interview/${id}/feedback`);
    } catch (err) {
      const error = err as { response?: { data?: { message?: string } } };
      setError(error.response?.data?.message || 'Failed to end interview');
    }
  };

  // Handle exit interview
  const handleExit = () => {
    setShowExitModal(true);
  };

  const confirmExit = async () => {
    if (!id) return;

    try {
      await interviewsAPI.end(id);
      navigate('/dashboard');
    } catch {
      // Navigate to dashboard even if ending the interview fails
      navigate('/dashboard');
    }
  };

  const cancelExit = () => {
    setShowExitModal(false);
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="min-h-screen bg-surface-primary flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-electric-blue border-t-transparent mb-4"></div>
          <p className="text-text-secondary">Loading interview...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error && !session) {
    return (
      <div className="min-h-screen bg-surface-primary flex items-center justify-center p-6">
        <div className="card p-8 max-w-md w-full border-status-error/20 bg-status-error/5">
          <div className="flex items-center gap-3 text-status-error mb-4">
            <AlertCircle size={24} />
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

  const currentQuestion = questions[currentQuestionIndex];
  const progress = ((currentQuestionIndex + 1) / questions.length) * 100;

  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-surface-primary">
      {/* Header */}
      <div className="bg-white border-b border-border-light">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            {/* Timer */}
            <div className="flex items-center gap-4">
              <div className="text-sm text-text-secondary">Elapsed Time</div>
              <Timer startTime={sessionStartTime || undefined} className="text-2xl" />
            </div>

            {/* Progress */}
            <div className="text-center">
              <div className="label text-text-tertiary mb-2">
                Question {currentQuestionIndex + 1} of {questions.length}
              </div>
              <div className="progress-bar w-48">
                <div
                  className="progress-bar-fill"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>

            {/* Exit Button */}
            <button
              onClick={handleExit}
              className="btn-ghost flex items-center gap-2 text-text-secondary hover:text-status-error"
            >
              <X size={20} />
              Exit Interview
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-6 py-8 max-w-4xl">
        {/* Error Alert */}
        {error && (
          <div className="card p-4 mb-6 border-status-error/20 bg-status-error/5">
            <div className="flex items-center gap-3 text-status-error">
              <AlertCircle size={20} />
              <p className="body-small">{error}</p>
            </div>
          </div>
        )}

        {/* Recording Error Alert */}
        {recordingError && (
          <div className="card p-4 mb-6 border-status-error/20 bg-status-error/5">
            <div className="flex items-center gap-3 text-status-error">
              <AlertCircle size={20} />
              <p className="body-small">{recordingError}</p>
            </div>
          </div>
        )}

        {/* Question Display */}
        {currentQuestion && (
          <QuestionDisplay
            question={currentQuestion}
            questionNumber={currentQuestionIndex + 1}
            totalQuestions={questions.length}
          />
        )}

        {/* Recording Section */}
        <div className="mt-8">
          <div className="card p-8">
            {isPreviewMode ? (
              /* Preview Mode */
              <AudioPreview
                isPlaying={isPlaying}
                currentTime={currentTime}
                duration={audioDuration}
                onPlay={playPreview}
                onPause={pausePreview}
                onReRecord={handleReRecord}
                onConfirm={handleSubmitAnswer}
                disabled={isSubmitting}
                isSubmitting={isSubmitting}
                submitProgress={submitProgress}
              />
            ) : (
              /* Recording Mode */
              <div className="flex flex-col items-center gap-6">
                {/* Recording Indicator */}
                <RecordingIndicator isRecording={isRecording} duration={duration} />

                {/* Record Button */}
                <RecordButton
                  recordingState={recordingState}
                  onStart={handleStartRecording}
                  onStop={handleStopRecording}
                  disabled={isSubmitting}
                />

                {/* Action Buttons */}
                <div className="flex gap-4 w-full max-w-md mt-4">
                  <button
                    onClick={handleSkipQuestion}
                    disabled={isSubmitting || isRecording}
                    className="btn-ghost flex-1 flex items-center justify-center gap-2"
                  >
                    <SkipForward size={20} />
                    Skip Question
                  </button>

                  {lastFailedUpload && (
                    <button
                      onClick={handleRetryUpload}
                      disabled={isSubmitting}
                      className="btn-primary flex-1 flex items-center justify-center gap-2 bg-amber-500 hover:bg-amber-600"
                    >
                      <RefreshCw size={20} className={isSubmitting ? 'animate-spin' : ''} />
                      {isSubmitting ? 'Retrying...' : 'Retry Upload'}
                    </button>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Transcription Panel - shows submitted answers being processed */}
        {submittedResponses.length > 0 && (
          <div className="mt-6">
            <button
              onClick={() => setShowTranscriptionPanel(!showTranscriptionPanel)}
              className="w-full flex items-center justify-between p-4 bg-surface-secondary rounded-lg hover:bg-surface-tertiary transition-colors"
            >
              <div className="flex items-center gap-3">
                <span className="text-sm font-medium text-text-primary">
                  Your Transcriptions ({submittedResponses.length})
                </span>
                {submittedResponses.some(r => r.processingStatus !== 'completed' && r.processingStatus !== 'failed') && (
                  <span className="text-xs bg-electric-blue/10 text-electric-blue px-2 py-0.5 rounded-full">
                    Processing...
                  </span>
                )}
              </div>
              {showTranscriptionPanel ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
            </button>

            {showTranscriptionPanel && (
              <div className="mt-2 space-y-3">
                {submittedResponses.map((response) => (
                  <TranscriptionDisplay
                    key={response.id}
                    processingStatus={response.processingStatus}
                    transcript={response.transcript}
                    processingError={response.processingError}
                    questionNumber={response.questionIndex + 1}
                  />
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Exit Confirmation Modal */}
      {showExitModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-6 z-50">
          <div className="card p-8 max-w-md w-full">
            <h3 className="heading-card mb-4">Exit Interview?</h3>
            <p className="text-text-secondary mb-6">
              Are you sure you want to exit? Your progress will be saved, but you won't be able to resume this session.
            </p>
            <div className="flex gap-4">
              <button onClick={cancelExit} className="btn-secondary flex-1">
                Continue Interview
              </button>
              <button onClick={confirmExit} className="btn-primary flex-1 bg-status-error hover:bg-red-600">
                Exit
              </button>
            </div>
          </div>
        </div>
      )}
      </div>
    </ErrorBoundary>
  );
}
