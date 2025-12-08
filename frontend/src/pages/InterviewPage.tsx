import { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { X, AlertCircle, SkipForward, RefreshCw, ChevronDown, ChevronUp, Lightbulb } from 'lucide-react';
import { ErrorBoundary } from '../components/ErrorBoundary';
import { interviewsAPI, responsesAPI, uploadAPI } from '../lib/api';
import { useAudioRecording } from '../hooks/useAudioRecording';
import { useToast } from '../hooks/useToast';
import { useCoachingHint } from '../hooks/useCoachingHint';
import { getExtensionForMimeType } from '../lib/audio-utils';
import Timer from '../components/interview/Timer';
import QuestionDisplay from '../components/interview/QuestionDisplay';
import AudioPreview from '../components/interview/AudioPreview';
import RecordingDeck from '../components/interview/RecordingDeck';
import TranscriptionDisplay from '../components/interview/TranscriptionDisplay';
import CoachOverlay from '../components/interview/CoachOverlay';
import { SkeletonQuestion } from '../components/ui/Skeleton';
import type { InterviewSession, Question, InterviewResponse, ProcessingStatus } from '../types';

const MAX_RETRY_ATTEMPTS = 3;
const RETRY_DELAY_MS = 1000;
const TRANSCRIPTION_POLL_INTERVAL = 3000;

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
  const [showCoach, setShowCoach] = useState(true);
  const [liveTranscript, setLiveTranscript] = useState('');

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

  // Warn user before leaving with unsaved progress
  useEffect(() => {
    const hasUnsavedProgress = isRecording || isPreviewMode || currentQuestionIndex > 0;

    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (hasUnsavedProgress) {
        e.preventDefault();
        e.returnValue = '';
        return '';
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [isRecording, isPreviewMode, currentQuestionIndex]);

  // Load interview session and questions
  useEffect(() => {
    if (!id) return;

    const loadInterview = async () => {
      try {
        setIsLoading(true);
        setError(null);

        const sessionResponse = await interviewsAPI.getById(id);
        const sessionData = sessionResponse.data;
        setSession(sessionData);

        if (sessionData.status === 'scheduled') {
          const startResponse = await interviewsAPI.start(id);
          setSession(startResponse.data);
        }

        setSessionStartTime(Date.now());

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
  const submittedResponsesRef = useRef<SubmittedResponse[]>([]);
  submittedResponsesRef.current = submittedResponses;

  useEffect(() => {
    if (!session) return;

    const pollTranscriptions = async () => {
      const currentResponses = submittedResponsesRef.current;
      if (currentResponses.length === 0) return;

      const processingResponses = currentResponses.filter(
        r => r.processingStatus !== 'completed' && r.processingStatus !== 'failed'
      );

      if (processingResponses.length === 0) return;

      try {
        const { data: responses } = await interviewsAPI.getResponses(session.id);

        let newCompletions = false;
        let completedIndex = -1;

        // Calculate updates first
        const nextResponses = currentResponses.map(tracked => {
          const updated = responses.find((r: InterviewResponse) => r.id === tracked.id);
          if (updated && tracked.processingStatus !== 'completed' && updated.processing_status === 'completed') {
            newCompletions = true;
            completedIndex = tracked.questionIndex;
          }

          if (updated) {
            return {
              ...tracked,
              processingStatus: updated.processing_status,
              transcript: updated.transcript,
              processingError: updated.processing_error,
            };
          }
          return tracked;
        });

        // Effect THEN Update
        if (newCompletions) {
          toast.success('Transcription ready', `Answer ${completedIndex + 1} has been transcribed`);
        }

        // Only update state if something changed (JSON comparison is cheap enough here for deep check, or just rely on map identity if strictly immutable)
        // For simplicity, we just set it as we built a new array
        setSubmittedResponses(nextResponses);

      } catch (err) {
        console.error('Failed to poll transcription status:', err);
      }
    };

    pollingIntervalRef.current = setInterval(pollTranscriptions, TRANSCRIPTION_POLL_INTERVAL);
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
    };
  }, [session, toast]);

  const handleStartRecording = async () => {
    try {
      await startRecording();
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

  const uploadWithRetry = useCallback(async (
    blob: Blob,
    sessionId: string,
    questionId: string,
    attempt: number = 1
  ): Promise<string> => {
    try {
      const extension = mimeType ? getExtensionForMimeType(mimeType) : 'webm';
      const type = mimeType || 'audio/webm';

      const audioFile = new File([blob], `answer-${currentQuestionIndex + 1}.${extension}`, {
        type: type,
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
  }, [currentQuestionIndex, toast, mimeType]);

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

  const handleSubmitAnswer = async () => {
    if (!session || !questions[currentQuestionIndex]) return;

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
      const audioUrl = await uploadWithRetry(blob, session.id, currentQuestion.id);

      setSubmitProgress('processing');
      const submitResponse = await responsesAPI.submit(session.id, {
        question_id: currentQuestion.id,
        audio_url: audioUrl,
        duration_seconds: duration,
      });

      const responseData = submitResponse.data;
      setSubmittedResponses(prev => [...prev, {
        id: responseData.id,
        questionIndex: currentQuestionIndex,
        processingStatus: responseData.processing_status || 'pending',
        transcript: responseData.transcript,
        processingError: responseData.processing_error,
      }]);

      if (submittedResponses.length === 0) {
        setShowTranscriptionPanel(true);
      }

      toast.success('Answer submitted', 'Your answer is being transcribed...');

      if (currentQuestionIndex < questions.length - 1) {
        setCurrentQuestionIndex(currentQuestionIndex + 1);
        resetRecording();
      } else {
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

  const handleSkipQuestion = async () => {
    if (!session || !questions[currentQuestionIndex]) return;

    try {
      setIsSubmitting(true);
      setError(null);

      const currentQuestion = questions[currentQuestionIndex];
      await responsesAPI.submit(session.id, {
        question_id: currentQuestion.id,
        audio_url: '',
        duration_seconds: 0,
      });

      if (currentQuestionIndex < questions.length - 1) {
        setCurrentQuestionIndex(currentQuestionIndex + 1);
        resetRecording();
      } else {
        await handleEndInterview();
      }
    } catch (err) {
      const error = err as { response?: { data?: { message?: string } } };
      setError(error.response?.data?.message || 'Failed to skip question');
    } finally {
      setIsSubmitting(false);
    }
  };

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

  const handleExit = () => setShowExitModal(true);
  const cancelExit = () => setShowExitModal(false);
  const confirmExit = async () => {
    if (!id) return;
    try {
      await interviewsAPI.end(id);
      navigate('/dashboard');
    } catch {
      navigate('/dashboard');
    }
  };

  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <SkeletonQuestion />
      </div>
    );
  }

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

  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-surface-primary flex flex-col">
        {/* Header */}
        <div className="bg-white/80 dark:bg-surface-dark/80 backdrop-blur-md border-b border-border-light dark:border-border-light/10 sticky top-0 z-50">
          <div className="container mx-auto px-6 py-4">
            <div className="flex items-center justify-between">
              {/* Timer */}
              <div className="flex items-center gap-4">
                <div className="text-sm font-medium text-text-secondary uppercase tracking-wider">Elapsed Time</div>
                <Timer startTime={sessionStartTime || undefined} className="text-2xl font-mono font-bold text-text-primary" />
              </div>

              {/* Progress */}
              <div className="hidden md:block text-center flex-1 max-w-md mx-8">
                <div className="flex justify-between text-xs font-medium text-text-tertiary mb-2 uppercase tracking-wider">
                  <span>Progress</span>
                  <span>{Math.round(progress)}%</span>
                </div>
                <div className="h-2 bg-surface-tertiary rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-electric-blue to-indigo-500 transition-all duration-500 ease-out"
                    style={{ width: `${progress}%` }}
                  />
                </div>
              </div>

              {/* Controls */}
              <div className="flex items-center gap-4">
                {/* Coach Toggle */}
                <button
                  onClick={() => setShowCoach(!showCoach)}
                  className={`p-2 rounded-lg transition-colors ${showCoach ? 'bg-electric-blue/10 text-electric-blue' : 'text-text-tertiary hover:text-text-secondary'}`}
                  title="Toggle AI Coach"
                >
                  <Lightbulb size={20} />
                </button>

                {/* Exit Button */}
                <button
                  onClick={handleExit}
                  className="btn-ghost flex items-center gap-2 text-text-secondary hover:text-status-error hover:bg-status-error/10"
                >
                  <X size={20} />
                  <span className="hidden sm:inline">Exit</span>
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 container mx-auto px-6 py-8 max-w-4xl flex flex-col justify-center min-h-[calc(100vh-80px)] relative">
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

          {/* Error Alert */}
          {(error || recordingError) && (
            <div className="card p-4 mb-6 border-status-error/20 bg-status-error/5 animate-fade-in">
              <div className="flex items-center gap-3 text-status-error">
                <AlertCircle size={20} />
                <p className="body-small">{error || recordingError}</p>
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
          <div className="relative z-20">
            <div className="card-glass p-8 shadow-xl border-white/50 bg-white/80 backdrop-blur-xl">
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
                <RecordingDeck
                  isRecording={isRecording}
                  recordingState={recordingState}
                  duration={duration}
                  mediaStream={mediaStream}
                  onStart={handleStartRecording}
                  onStop={handleStopRecording}
                  onPause={pauseRecording}
                  onResume={resumeRecording}
                  onCancel={handleExit} /* Using exit as cancel for now, or could be a specific reset */
                  onConfirm={handleSubmitAnswer}
                  disabled={isSubmitting}
                  onTranscriptChange={handleTranscriptChange}
                />
              )}
            </div>

            {/* Secondary Actions - Outside the deck for cleaner UI */}
            {!isPreviewMode && (
              <div className="mt-6 flex justify-center gap-4">
                <button
                  onClick={handleSkipQuestion}
                  disabled={isSubmitting || isRecording}
                  className="btn-ghost flex items-center justify-center gap-2 text-text-tertiary hover:text-text-secondary"
                >
                  <SkipForward size={20} />
                  Skip Question
                </button>

                {lastFailedUpload && (
                  <button
                    onClick={handleRetryUpload}
                    disabled={isSubmitting}
                    className="btn-primary flex items-center justify-center gap-2 bg-amber-500 hover:bg-amber-600 border-none"
                  >
                    <RefreshCw size={20} className={isSubmitting ? 'animate-spin' : ''} />
                    {isSubmitting ? 'Retrying...' : 'Retry Upload'}
                  </button>
                )}
              </div>
            )}
          </div>

          {/* Transcription Panel */}
          {submittedResponses.length > 0 && (
            <div className="mt-8 mb-12">
              <button
                onClick={() => setShowTranscriptionPanel(!showTranscriptionPanel)}
                className="w-full flex items-center justify-between p-4 bg-white/60 backdrop-blur-sm rounded-xl border border-white/50 hover:bg-white/80 transition-all shadow-sm"
              >
                <div className="flex items-center gap-3">
                  <span className="text-sm font-semibold text-text-primary">
                    Your Transcriptions ({submittedResponses.length})
                  </span>
                  {submittedResponses.some(r => r.processingStatus !== 'completed' && r.processingStatus !== 'failed') && (
                    <span className="flex items-center gap-1.5 text-xs bg-electric-blue/10 text-electric-blue px-2.5 py-1 rounded-full font-medium">
                      <span className="w-1.5 h-1.5 rounded-full bg-electric-blue animate-pulse"></span>
                      Processing
                    </span>
                  )}
                </div>
                {showTranscriptionPanel ? <ChevronUp size={20} className="text-text-tertiary" /> : <ChevronDown size={20} className="text-text-tertiary" />}
              </button>

              {showTranscriptionPanel && (
                <div className="mt-4 space-y-4 animate-slide-up">
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
          <div className="fixed inset-0 bg-charcoal/60 backdrop-blur-sm flex items-center justify-center p-6 z-[100] animate-fade-in">
            <div className="card p-8 max-w-md w-full shadow-2xl animate-scale-in">
              <h3 className="heading-card mb-4 text-text-primary">Exit Interview?</h3>
              <p className="text-text-secondary mb-8 leading-relaxed">
                Are you sure you want to exit? Your progress will be saved, but you won't be able to resume this session.
              </p>
              <div className="flex gap-4">
                <button onClick={cancelExit} className="btn-secondary flex-1 justify-center">
                  Continue
                </button>
                <button onClick={confirmExit} className="btn-primary flex-1 justify-center bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 shadow-red-500/20">
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
