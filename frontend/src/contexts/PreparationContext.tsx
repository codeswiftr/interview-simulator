/* eslint-disable react-refresh/only-export-components */
import { createContext, useContext, useCallback, useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { preparationAPI, uploadAPI } from '../lib/api';
import { useToast } from '../hooks/useToast';
import { getExtensionForMimeType } from '../lib/audio-utils';
import type { AxiosError } from 'axios';

// Types
export type PreparationStage = 'detective' | 'draft' | 'practice' | 'complete';

export interface DetectiveQnA {
  question: string;
  answer: string;
  order: number;
}

export interface QuestionContext {
  id: string;
  content: string;
  category?: string;
  difficulty?: string;
  company_tags?: string[];
}

export interface Attempt {
  id: string;
  audio_url: string | null;
  transcript: string | null;
  delivery_score: number | null;
  comparison_feedback: string | null;
  strengths?: string[];
  improvements?: string[];
  created_at: string;
}

export interface ComparisonData {
  draft: string;
  delivery: string;
  delivery_score: number | null;
  comparison_feedback: string | null;
  strengths: string[];
  improvements: string[];
}

// Context interface
interface PreparationContextValue {
  // IDs
  preparationId: string | undefined;

  // Stage state
  stage: PreparationStage;
  setStage: (stage: PreparationStage) => void;

  // Question context
  questionContext: QuestionContext | null;

  // Detective stage state
  currentQuestion: string;
  currentAnswer: string;
  setCurrentAnswer: (answer: string) => void;
  qnaList: DetectiveQnA[];
  isComplete: boolean;

  // Draft state
  draft: string;
  setDraft: (draft: string) => void;

  // Practice state
  attempts: Attempt[];
  currentAttemptId: string | null;
  comparisonData: ComparisonData | null;
  selectedAttemptForComparison: string | null;
  setSelectedAttemptForComparison: (id: string | null) => void;

  // Loading states
  isLoading: boolean;
  isGenerating: boolean;
  isSubmitting: boolean;
  isRating: boolean;
  isSavingDraft: boolean;

  // Error state
  error: string | null;
  setError: (error: string | null) => void;

  // Actions
  handleSubmitAnswer: () => Promise<void>;
  handleGenerateDraft: () => Promise<void>;
  handleStartPractice: () => Promise<void>;
  handleSubmitPractice: (blob: Blob, mimeType: string | null) => Promise<void>;
  handleRateAttempt: (attemptId: string) => Promise<void>;
  handleViewComparison: (attemptId: string) => Promise<void>;
  handleSaveDraft: (newDraft: string) => Promise<void>;
  clearComparison: () => void;
  reloadAttempts: () => Promise<void>;
}

const PreparationContext = createContext<PreparationContextValue | null>(null);

export function usePreparation() {
  const context = useContext(PreparationContext);
  if (!context) {
    throw new Error('usePreparation must be used within PreparationProvider');
  }
  return context;
}

interface PreparationProviderProps {
  children: React.ReactNode;
}

export function PreparationProvider({ children }: PreparationProviderProps) {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const toast = useToast();

  // Core state
  const [stage, setStage] = useState<PreparationStage>('detective');
  const [questionContext, setQuestionContext] = useState<QuestionContext | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState<string>('');
  const [currentAnswer, setCurrentAnswer] = useState<string>('');
  const [qnaList, setQnaList] = useState<DetectiveQnA[]>([]);
  const [draft, setDraft] = useState<string>('');
  const [isComplete, setIsComplete] = useState(false);
  const [attempts, setAttempts] = useState<Attempt[]>([]);
  const [currentAttemptId, setCurrentAttemptId] = useState<string | null>(null);
  const [comparisonData, setComparisonData] = useState<ComparisonData | null>(null);
  const [selectedAttemptForComparison, setSelectedAttemptForComparison] = useState<string | null>(null);

  // Loading states
  const [isLoading, setIsLoading] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isRating, setIsRating] = useState(false);
  const [isSavingDraft, setIsSavingDraft] = useState(false);

  // Error state
  const [error, setError] = useState<string | null>(null);

  // Load preparation state on mount
  useEffect(() => {
    if (!id) {
      navigate('/questions');
      return;
    }

    const loadState = async () => {
      try {
        setIsLoading(true);
        setError(null);
        const response = await preparationAPI.getState(id);
        const data = response.data;

        setStage(data.stage as PreparationStage);
        setIsComplete(data.stage !== 'detective');
        setDraft(data.draft_answer || '');
        setQnaList(
          data.qna.map((qna) => ({
            question: qna.question,
            answer: qna.answer,
            order: qna.order,
          }))
        );
        setQuestionContext(data.question);
        setAttempts(data.attempts);

        if (data.current_question) {
          setCurrentQuestion(data.current_question);
          setCurrentAnswer('');
        } else if (data.stage === 'detective') {
          const questionResponse = await preparationAPI.getDetectiveQuestion(id);
          const questionData = questionResponse.data;
          if (questionData.is_complete) {
            setIsComplete(true);
            setStage('draft');
          } else {
            setCurrentQuestion(questionData.question);
            setCurrentAnswer('');
          }
        } else {
          setCurrentQuestion('');
        }
      } catch {
        // Fall back to fetching the next question
        setQuestionContext(null);
        try {
          const questionResponse = await preparationAPI.getDetectiveQuestion(id);
          const questionData = questionResponse.data;
          if (questionData.is_complete) {
            setIsComplete(true);
            setStage('draft');
          } else {
            setCurrentQuestion(questionData.question);
            setCurrentAnswer('');
          }
        } catch (questionErr) {
          const axiosError = questionErr as AxiosError<{ message?: string }>;
          const errorMsg = axiosError.response?.data?.message || 'Failed to load preparation';
          setError(errorMsg);
        }
      } finally {
        setIsLoading(false);
      }
    };

    loadState();
  }, [id, navigate]);

  // Load attempts when in practice stage
  useEffect(() => {
    if (!id || (stage !== 'practice' && stage !== 'complete')) return;

    const loadAttempts = async () => {
      try {
        const response = await preparationAPI.getAttempts(id);
        setAttempts(response.data.attempts);
      } catch {
        // Silently fail - attempts might not exist yet
      }
    };

    loadAttempts();
  }, [id, stage]);

  // Reload attempts function
  const reloadAttempts = useCallback(async () => {
    if (!id) return;
    try {
      const response = await preparationAPI.getAttempts(id);
      setAttempts(response.data.attempts);
    } catch {
      // Silently fail
    }
  }, [id]);

  // Submit detective answer
  const handleSubmitAnswer = useCallback(async () => {
    if (!id || !currentAnswer.trim()) {
      toast.error('Error', 'Please provide an answer');
      return;
    }

    try {
      setIsLoading(true);
      setError(null);

      const response = await preparationAPI.submitDetectiveAnswer(id, currentAnswer.trim());
      const data = response.data;

      setQnaList((prev) => [
        ...prev,
        { question: currentQuestion, answer: currentAnswer.trim(), order: prev.length + 1 },
      ]);

      if (data.is_complete) {
        setStage('draft');
        setIsComplete(true);
        setCurrentQuestion('');
        setCurrentAnswer('');
      } else if (data.next_question) {
        setCurrentQuestion(data.next_question);
        setCurrentAnswer('');
      }
    } catch (err) {
      const axiosError = err as AxiosError<{ message?: string }>;
      const errorMsg = axiosError.response?.data?.message || 'Failed to submit answer';
      setError(errorMsg);
      toast.error('Error', errorMsg);
    } finally {
      setIsLoading(false);
    }
  }, [id, currentQuestion, currentAnswer, toast]);

  // Generate draft
  const handleGenerateDraft = useCallback(async () => {
    if (!id) return;

    try {
      setIsGenerating(true);
      setError(null);

      const response = await preparationAPI.generateDraft(id);
      setDraft(response.data.draft_answer);
      setStage(response.data.stage as PreparationStage);
      toast.success('Draft generated', 'Review your personalized answer');
    } catch (err) {
      const axiosError = err as AxiosError<{ message?: string }>;
      const errorMsg = axiosError.response?.data?.message || 'Failed to generate draft';
      setError(errorMsg);
      toast.error('Error', errorMsg);
    } finally {
      setIsGenerating(false);
    }
  }, [id, toast]);

  // Start practice session
  const handleStartPractice = useCallback(async () => {
    if (!id) return;

    try {
      setIsLoading(true);
      setError(null);

      const response = await preparationAPI.startPractice(id);
      setCurrentAttemptId(response.data.attempt_id);
      setStage('practice');
      toast.success('Practice started', 'Record your delivery');
    } catch (err) {
      const axiosError = err as AxiosError<{ message?: string }>;
      setError(axiosError.response?.data?.message || 'Failed to start practice');
      toast.error('Error', 'Failed to start practice');
    } finally {
      setIsLoading(false);
    }
  }, [id, toast]);

  // Submit practice attempt
  const handleSubmitPractice = useCallback(async (blob: Blob, mimeType: string | null) => {
    if (!id) return;

    try {
      setIsSubmitting(true);
      setError(null);

      const extension = mimeType ? getExtensionForMimeType(mimeType) : 'webm';
      const type = mimeType || 'audio/webm';
      const audioFile = new File([blob], `practice-${Date.now()}.${extension}`, { type });

      const uploadResponse = await uploadAPI.uploadAudio(audioFile, null, null, id);
      const audioUrl = uploadResponse.data.audio_url;

      await preparationAPI.submitPractice(id, audioUrl);
      toast.success('Practice submitted', 'Your delivery has been transcribed');

      const attemptsResponse = await preparationAPI.getAttempts(id);
      setAttempts(attemptsResponse.data.attempts);
      setCurrentAttemptId(null);
    } catch (err) {
      const axiosError = err as AxiosError<{ message?: string }>;
      const errorMsg = axiosError.response?.data?.message || 'Failed to submit practice';
      setError(errorMsg);
      toast.error('Error', errorMsg);
    } finally {
      setIsSubmitting(false);
    }
  }, [id, toast]);

  // Load comparison data
  const loadComparison = useCallback(async (preparationId: string, attemptId: string) => {
    try {
      const response = await preparationAPI.getComparison(preparationId, attemptId);
      setComparisonData(response.data);
    } catch (err) {
      const axiosError = err as AxiosError<{ message?: string }>;
      setError(axiosError.response?.data?.message || 'Failed to load comparison');
    }
  }, []);

  // Rate delivery attempt
  const handleRateAttempt = useCallback(async (attemptId: string) => {
    if (!id) return;

    try {
      setIsRating(true);
      setError(null);

      const response = await preparationAPI.rateDelivery(id, attemptId);

      toast.success('Delivery rated', `Score: ${response.data.delivery_score.toFixed(1)}%`);
      setStage(response.data.stage as PreparationStage);
      setIsComplete(true);

      const attemptsResponse = await preparationAPI.getAttempts(id);
      setAttempts(attemptsResponse.data.attempts);

      setSelectedAttemptForComparison(attemptId);
      await loadComparison(id, attemptId);
    } catch (err) {
      const axiosError = err as AxiosError<{ message?: string }>;
      setError(axiosError.response?.data?.message || 'Failed to rate delivery');
      toast.error('Error', 'Failed to rate delivery');
    } finally {
      setIsRating(false);
    }
  }, [id, toast, loadComparison]);

  // View comparison
  const handleViewComparison = useCallback(async (attemptId: string) => {
    if (!id) return;
    setSelectedAttemptForComparison(attemptId);
    await loadComparison(id, attemptId);
  }, [id, loadComparison]);

  // Clear comparison
  const clearComparison = useCallback(() => {
    setSelectedAttemptForComparison(null);
    setComparisonData(null);
  }, []);

  // Save draft
  const handleSaveDraft = useCallback(async (newDraft: string) => {
    if (!id || !newDraft.trim()) {
      toast.error('Error', 'Draft cannot be empty');
      return;
    }

    try {
      setIsSavingDraft(true);
      setError(null);

      const response = await preparationAPI.updateDraft(id, newDraft.trim());
      setDraft(response.data.draft_answer);
      toast.success('Draft updated', 'Your changes have been saved');
    } catch (err) {
      const axiosError = err as AxiosError<{ message?: string }>;
      setError(axiosError.response?.data?.message || 'Failed to update draft');
      toast.error('Error', 'Failed to update draft');
    } finally {
      setIsSavingDraft(false);
    }
  }, [id, toast]);

  const value: PreparationContextValue = {
    preparationId: id,
    stage,
    setStage,
    questionContext,
    currentQuestion,
    currentAnswer,
    setCurrentAnswer,
    qnaList,
    isComplete,
    draft,
    setDraft,
    attempts,
    currentAttemptId,
    comparisonData,
    selectedAttemptForComparison,
    setSelectedAttemptForComparison,
    isLoading,
    isGenerating,
    isSubmitting,
    isRating,
    isSavingDraft,
    error,
    setError,
    handleSubmitAnswer,
    handleGenerateDraft,
    handleStartPractice,
    handleSubmitPractice,
    handleRateAttempt,
    handleViewComparison,
    handleSaveDraft,
    clearComparison,
    reloadAttempts,
  };

  return (
    <PreparationContext.Provider value={value}>
      {children}
    </PreparationContext.Provider>
  );
}
