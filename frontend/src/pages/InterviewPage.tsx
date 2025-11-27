import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { X, AlertCircle, CheckCircle, SkipForward } from 'lucide-react';
import { interviewsAPI, responsesAPI, uploadAPI } from '../lib/api';
import { useAudioRecording } from '../hooks/useAudioRecording';
import Timer from '../components/interview/Timer';
import RecordingIndicator from '../components/interview/RecordingIndicator';
import RecordButton from '../components/interview/RecordButton';
import QuestionDisplay from '../components/interview/QuestionDisplay';
import type { InterviewSession, Question } from '../types';

export default function InterviewPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  // Session state
  const [session, setSession] = useState<InterviewSession | null>(null);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [sessionStartTime, setSessionStartTime] = useState<number | null>(null);

  // UI state
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showExitModal, setShowExitModal] = useState(false);
  const [hasRecorded, setHasRecorded] = useState(false);

  // Audio recording hook
  const {
    recordingState,
    audioBlob,
    duration,
    isRecording,
    startRecording,
    stopRecording,
    resetRecording,
    error: recordingError,
  } = useAudioRecording();

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

  // Handle recording start
  const handleStartRecording = async () => {
    try {
      await startRecording();
      setHasRecorded(false);
    } catch (err) {
      const error = err as { message?: string };
      setError(error.message || 'Failed to start recording');
    }
  };

  // Handle recording stop
  const handleStopRecording = () => {
    stopRecording();
    setHasRecorded(true);
  };

  // Handle submit answer
  const handleSubmitAnswer = async () => {
    if (!audioBlob || !session || !questions[currentQuestionIndex]) {
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);

      const currentQuestion = questions[currentQuestionIndex];

      // Upload audio file
      const audioFile = new File([audioBlob], `answer-${currentQuestionIndex + 1}.webm`, {
        type: 'audio/webm',
      });

      const uploadResponse = await uploadAPI.uploadAudio(
        audioFile,
        session.id,
        currentQuestion.id
      );

      const audioUrl = uploadResponse.data.audio_url;

      // Submit response
      await responsesAPI.submit(session.id, {
        question_id: currentQuestion.id,
        audio_url: audioUrl,
        duration_seconds: duration,
      });

      // Move to next question or finish
      if (currentQuestionIndex < questions.length - 1) {
        setCurrentQuestionIndex(currentQuestionIndex + 1);
        resetRecording();
        setHasRecorded(false);
      } else {
        // All questions answered, end the session
        await handleEndInterview();
      }
    } catch (err) {
      const error = err as { response?: { data?: { message?: string } } };
      setError(error.response?.data?.message || 'Failed to submit answer');
    } finally {
      setIsSubmitting(false);
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
        setHasRecorded(false);
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

              {/* Success Message */}
              {hasRecorded && !isRecording && (
                <div className="flex items-center gap-2 text-status-success">
                  <CheckCircle size={20} />
                  <span className="body-small font-medium">
                    Answer recorded ({Math.floor(duration / 60)}:{String(duration % 60).padStart(2, '0')})
                  </span>
                </div>
              )}

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

                <button
                  onClick={handleSubmitAnswer}
                  disabled={!hasRecorded || isSubmitting || isRecording}
                  className="btn-primary flex-1 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isSubmitting
                    ? 'Submitting...'
                    : currentQuestionIndex < questions.length - 1
                    ? 'Next Question'
                    : 'Finish Interview'}
                </button>
              </div>
            </div>
          </div>
        </div>
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
  );
}
