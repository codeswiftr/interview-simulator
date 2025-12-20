/* eslint-disable react-refresh/only-export-components */
import { createContext, useContext, useCallback, useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { interviewsAPI, responsesAPI, uploadAPI } from '../lib/api';
import { useToast } from '../hooks/useToast';
import { getExtensionForMimeType } from '../lib/audio-utils';
import { analytics, Events } from '../lib/analytics';
import type { InterviewSession, Question, InterviewResponse, ProcessingStatus } from '../types';

// Constants
const MAX_RETRY_ATTEMPTS = 3;
const RETRY_DELAY_MS = 1000;
const TRANSCRIPTION_POLL_INTERVAL = 3000;

// Types
export interface SubmittedResponse {
  id: string;
  questionIndex: number;
  processingStatus: ProcessingStatus;
  transcript?: string;
  processingError?: string;
}

// Context interface
interface InterviewContextValue {
  // Session data
  session: InterviewSession | null;
  questions: Question[];
  currentQuestionIndex: number;
  currentQuestion: Question | undefined;
  sessionStartTime: number | null;
  progress: number;

  // Transcription state
  submittedResponses: SubmittedResponse[];
  showTranscriptionPanel: boolean;
  setShowTranscriptionPanel: (show: boolean) => void;

  // UI state
  isLoading: boolean;
  error: string | null;
  setError: (error: string | null) => void;
  isSubmitting: boolean;
  submitProgress: 'uploading' | 'processing' | null;
  showExitModal: boolean;
  setShowExitModal: (show: boolean) => void;
  showCoach: boolean;
  setShowCoach: (show: boolean) => void;
  lastFailedUpload: { blob: Blob; questionId: string; mimeType: string | null } | null;

  // Actions
  handleSubmitAnswer: (blob: Blob, mimeType: string | null, duration: number) => Promise<void>;
  handleSkipQuestion: () => Promise<void>;
  handleRetryUpload: (duration: number) => Promise<void>;
  handleExit: () => void;
  cancelExit: () => void;
  confirmExit: () => Promise<void>;
  resetRecordingState: () => void;
}

const InterviewContext = createContext<InterviewContextValue | null>(null);

export function useInterview() {
  const context = useContext(InterviewContext);
  if (!context) {
    throw new Error('useInterview must be used within InterviewProvider');
  }
  return context;
}

interface InterviewProviderProps {
  children: React.ReactNode;
}

export function InterviewProvider({ children }: InterviewProviderProps) {
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
  const [showCoach, setShowCoach] = useState(true);
  const [lastFailedUpload, setLastFailedUpload] = useState<{ blob: Blob; questionId: string; mimeType: string | null } | null>(null);

  // Computed values
  const currentQuestion = questions[currentQuestionIndex];
  const progress = questions.length > 0 ? ((currentQuestionIndex + 1) / questions.length) * 100 : 0;

  // Ref for polling to access latest state
  const submittedResponsesRef = useRef<SubmittedResponse[]>([]);
  submittedResponsesRef.current = submittedResponses;

  // Track consecutive polling failures
  const pollingFailureCountRef = useRef(0);

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

        // Track interview started
        analytics.track(Events.INTERVIEW_STARTED, {
          interview_id: sessionData.id,
          category: sessionData.category,
          question_count: questionsResponse.data.length,
        });
      } catch (err) {
        const error = err as { response?: { data?: { message?: string } } };
        setError(error.response?.data?.message || 'Failed to load interview');
      } finally {
        setIsLoading(false);
      }
    };

    loadInterview();
  }, [id]);

  // Track question viewed
  useEffect(() => {
    if (currentQuestion && session) {
      analytics.track(Events.QUESTION_VIEWED, {
        interview_id: session.id,
        question_id: currentQuestion.id,
        question_order: currentQuestionIndex + 1,
        category: currentQuestion.category,
      });
    }
  }, [currentQuestion, currentQuestionIndex, session]);

  // Poll for transcription status updates
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

        if (newCompletions) {
          toast.success('Transcription ready', `Answer ${completedIndex + 1} has been transcribed`);
        }

        setSubmittedResponses(nextResponses);
        pollingFailureCountRef.current = 0; // Reset on success
      } catch (err) {
        pollingFailureCountRef.current += 1;
        console.error('Failed to poll transcription status:', err);

        // Show warning after 3 consecutive failures
        if (pollingFailureCountRef.current === 3) {
          toast.warning('Connection issue', 'Having trouble checking transcription status. We\'ll keep trying.');
        }
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

  // Upload with retry
  const uploadWithRetry = useCallback(async (
    blob: Blob,
    sessionId: string,
    questionId: string,
    mimeType: string | null,
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
        return uploadWithRetry(blob, sessionId, questionId, mimeType, attempt + 1);
      }
      throw err;
    }
  }, [currentQuestionIndex, toast]);

  // End interview
  const handleEndInterview = useCallback(async () => {
    if (!id) return;
    try {
      await interviewsAPI.end(id);

      if (session && sessionStartTime) {
        analytics.track(Events.INTERVIEW_COMPLETED, {
          interview_id: session.id,
          total_duration_seconds: Math.round((Date.now() - sessionStartTime) / 1000),
          questions_answered: submittedResponses.length,
          total_questions: questions.length,
        });
      }

      navigate(`/interview/${id}/feedback`);
    } catch (err) {
      const error = err as { response?: { data?: { message?: string } } };
      setError(error.response?.data?.message || 'Failed to end interview');
    }
  }, [id, navigate, session, sessionStartTime, submittedResponses.length, questions.length]);

  // Submit answer
  const handleSubmitAnswer = useCallback(async (blob: Blob, mimeType: string | null, duration: number) => {
    if (!session || !questions[currentQuestionIndex]) return;

    try {
      setIsSubmitting(true);
      setSubmitProgress('uploading');
      setError(null);
      setLastFailedUpload(null);

      const question = questions[currentQuestionIndex];
      const audioUrl = await uploadWithRetry(blob, session.id, question.id, mimeType);

      setSubmitProgress('processing');
      const submitResponse = await responsesAPI.submit(session.id, {
        question_id: question.id,
        audio_url: audioUrl,
        duration_seconds: duration,
      });

      // Track recording completed
      analytics.track(Events.RECORDING_COMPLETED, {
        interview_id: session.id,
        question_id: question.id,
        duration_seconds: Math.round(duration),
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
      } else {
        await handleEndInterview();
      }
    } catch (err) {
      const error = err as { response?: { data?: { message?: string } } };
      setError(error.response?.data?.message || 'Failed to submit answer. Click retry to try again.');
      setLastFailedUpload({ blob, questionId: questions[currentQuestionIndex].id, mimeType });
      toast.error('Upload failed', 'Your answer could not be uploaded. Please retry.');
    } finally {
      setIsSubmitting(false);
      setSubmitProgress(null);
    }
  }, [session, questions, currentQuestionIndex, uploadWithRetry, toast, submittedResponses.length, handleEndInterview]);

  // Skip question
  const handleSkipQuestion = useCallback(async () => {
    if (!session || !questions[currentQuestionIndex]) return;

    try {
      setIsSubmitting(true);
      setError(null);

      const question = questions[currentQuestionIndex];
      await responsesAPI.submit(session.id, {
        question_id: question.id,
        audio_url: '',
        duration_seconds: 0,
      });

      if (currentQuestionIndex < questions.length - 1) {
        setCurrentQuestionIndex(currentQuestionIndex + 1);
      } else {
        await handleEndInterview();
      }
    } catch (err) {
      const error = err as { response?: { data?: { message?: string } } };
      setError(error.response?.data?.message || 'Failed to skip question');
    } finally {
      setIsSubmitting(false);
    }
  }, [session, questions, currentQuestionIndex, handleEndInterview]);

  // Retry failed upload
  const handleRetryUpload = useCallback(async (duration: number) => {
    if (!lastFailedUpload || !session) return;

    try {
      setIsSubmitting(true);
      setError(null);

      const audioUrl = await uploadWithRetry(
        lastFailedUpload.blob,
        session.id,
        lastFailedUpload.questionId,
        lastFailedUpload.mimeType
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
  }, [lastFailedUpload, session, uploadWithRetry, toast, currentQuestionIndex, questions.length, handleEndInterview]);

  // Exit handlers
  const handleExit = useCallback(() => setShowExitModal(true), []);
  const cancelExit = useCallback(() => setShowExitModal(false), []);

  const confirmExit = useCallback(async () => {
    if (!id) return;

    if (session && sessionStartTime) {
      analytics.track(Events.INTERVIEW_ABANDONED, {
        interview_id: session.id,
        questions_completed: currentQuestionIndex,
        total_questions: questions.length,
        duration_seconds: Math.round((Date.now() - sessionStartTime) / 1000),
      });
    }

    try {
      await interviewsAPI.end(id);
      navigate('/dashboard');
    } catch {
      navigate('/dashboard');
    }
  }, [id, session, sessionStartTime, currentQuestionIndex, questions.length, navigate]);

  // Reset recording state (for component cleanup)
  const resetRecordingState = useCallback(() => {
    setError(null);
    setLastFailedUpload(null);
  }, []);

  const value: InterviewContextValue = {
    session,
    questions,
    currentQuestionIndex,
    currentQuestion,
    sessionStartTime,
    progress,
    submittedResponses,
    showTranscriptionPanel,
    setShowTranscriptionPanel,
    isLoading,
    error,
    setError,
    isSubmitting,
    submitProgress,
    showExitModal,
    setShowExitModal,
    showCoach,
    setShowCoach,
    lastFailedUpload,
    handleSubmitAnswer,
    handleSkipQuestion,
    handleRetryUpload,
    handleExit,
    cancelExit,
    confirmExit,
    resetRecordingState,
  };

  return (
    <InterviewContext.Provider value={value}>
      {children}
    </InterviewContext.Provider>
  );
}
