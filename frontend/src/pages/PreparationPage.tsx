import { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Sparkles, Loader2, CheckCircle, AlertCircle, History, TrendingUp, BarChart3, Edit2, Save, X, RefreshCw, Wand2, MessageCircle, Mic } from 'lucide-react';
import { preparationAPI, uploadAPI } from '../lib/api';
import { useToast } from '../hooks/useToast';
import { useAudioRecording } from '../hooks/useAudioRecording';
import { useCoachingHint } from '../hooks/useCoachingHint';
import { useSpeechSynthesis } from '../hooks/useSpeechSynthesis';
import { useSpeechRecognition } from '../hooks/useSpeechRecognition';
import { useVoicePreferences } from '../hooks/useVoicePreferences';
import { useConversationMode } from '../hooks/useConversationMode';
import RecordingDeck from '../components/interview/RecordingDeck';
import CoachOverlay from '../components/interview/CoachOverlay';
import HintHistoryPanel from '../components/interview/HintHistoryPanel';
import ConversationIndicator from '../components/interview/ConversationIndicator';
import { VoiceInputButton } from '../components/common/VoiceInputButton';
import ContextualTooltip from '../components/common/ContextualTooltip';
import { getExtensionForMimeType } from '../lib/audio-utils';
import type { AxiosError } from 'axios';

type PreparationStage = 'detective' | 'draft' | 'practice' | 'complete';

interface DetectiveQnA {
  question: string;
  answer: string;
  order: number;
}

interface QuestionContext {
  id: string;
  content: string;
  category?: string;
  difficulty?: string;
  company_tags?: string[];
}

export default function PreparationPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const toast = useToast();

  const [stage, setStage] = useState<PreparationStage>('detective');
  const [questionContext, setQuestionContext] = useState<QuestionContext | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState<string>('');
  const [currentAnswer, setCurrentAnswer] = useState<string>('');
  const [qnaList, setQnaList] = useState<DetectiveQnA[]>([]);
  const [draft, setDraft] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isComplete, setIsComplete] = useState(false);
  const [attempts, setAttempts] = useState<Array<{
    id: string;
    audio_url: string | null;
    transcript: string | null;
    delivery_score: number | null;
    comparison_feedback: string | null;
    created_at: string;
  }>>([]);
  const [currentAttemptId, setCurrentAttemptId] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [selectedAttemptForComparison, setSelectedAttemptForComparison] = useState<string | null>(null);
  const [comparisonData, setComparisonData] = useState<{
    draft: string;
    delivery: string;
    delivery_score: number | null;
    comparison_feedback: string | null;
    strengths: string[];
    improvements: string[];
  } | null>(null);
  const [isRating, setIsRating] = useState(false);
  const [isEditingDraft, setIsEditingDraft] = useState(false);
  const [editedDraft, setEditedDraft] = useState<string>('');
  const [isSavingDraft, setIsSavingDraft] = useState(false);
  const [interimTranscript, setInterimTranscript] = useState<string>('');
  const [draftInterimTranscript, setDraftInterimTranscript] = useState<string>('');
  const [liveTranscript, setLiveTranscript] = useState<string>('');
  const [showCoach, setShowCoach] = useState(true);
  const [hintHistory, setHintHistory] = useState<Array<{ timestamp: Date; hint: string; stage: 'detective' | 'practice' }>>([]);
  const [isHintHistoryExpanded, setIsHintHistoryExpanded] = useState(false);
  const draftTextareaRef = useRef<HTMLTextAreaElement>(null);
  const { settings: voiceSettings, updateSettings: updateVoiceSettings } = useVoicePreferences();
  const [voiceEnabled, setVoiceEnabled] = useState(voiceSettings.enabled);

  const tts = useSpeechSynthesis();
  const {
    speak,
    stop: stopSpeaking,
    isSpeaking,
    isSupported: isSpeechSupported,
    error: speechError,
    setVoice,
    setRate,
    setPitch,
    setVolume,
    voices,
  } = tts;

  // Speech recognition for conversation mode
  const stt = useSpeechRecognition({
    onResult: (transcript, isFinal) => {
      if (isFinal && conversationModeEnabled && stage === 'detective') {
        // Auto-submit answer when user finishes speaking in conversation mode
        setCurrentAnswer(transcript);
      }
    },
  });

  // Conversation mode state
  const [conversationModeEnabled, setConversationModeEnabled] = useState(false);

  // Conversation mode hook for phone-like experience
  const conversation = useConversationMode({
    tts,
    stt,
    autoListen: voiceSettings.autoListen,
    enabled: conversationModeEnabled && voiceEnabled && stage === 'detective',
    onUserFinish: (transcript) => {
      // When user finishes speaking, set their answer
      if (transcript.trim()) {
        setCurrentAnswer(transcript);
      }
    },
  });

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

  // Load preparation state (resume support)
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
          // Fetch the next question if none pending
          // Don't set loading here - we're already loading
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
        // Fall back to fetching the next question to keep flow alive
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
          // If we can't even fetch a question, show error
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

  // Get next detective question
  const getNextQuestion = useCallback(async () => {
    if (!id) return;

    try {
      setIsLoading(true);
      setError(null);
      const response = await preparationAPI.getDetectiveQuestion(id);
      const data = response.data;

      if (data.is_complete) {
        setIsComplete(true);
        setStage('draft');
      } else {
        setCurrentQuestion(data.question);
        setCurrentAnswer('');
      }
    } catch (err) {
      const axiosError = err as AxiosError<{ message?: string }>;
      const errorMsg = axiosError.response?.data?.message || 'Failed to get question';
      setError(errorMsg);
      toast.error('Error', errorMsg);

      // Auto-retry on network errors
      if (errorMsg.includes('network') || errorMsg.includes('connection') || axiosError.code === 'ECONNREFUSED') {
        setTimeout(() => {
          if (id) {
            getNextQuestion();
          }
        }, 2000);
      }
    } finally {
      setIsLoading(false);
    }
  }, [id, toast]);

  // Submit answer
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

      // Add to Q&A list
      setQnaList((prev) => [
        ...prev,
        { question: currentQuestion, answer: currentAnswer.trim(), order: prev.length + 1 },
      ]);

      // Reset transcript for next question (conversation mode)
      stt.resetTranscript();

      if (data.is_complete) {
        // Move to draft stage
        setStage('draft');
        setIsComplete(true);
        setCurrentQuestion('');
        setCurrentAnswer('');
      } else if (data.next_question) {
        // Get next question
        setCurrentQuestion(data.next_question);
        setCurrentAnswer('');
      }
    } catch (err) {
      const axiosError = err as AxiosError<{ message?: string }>;
      const errorMsg = axiosError.response?.data?.message || 'Failed to submit answer';
      setError(errorMsg);
      toast.error('Error', errorMsg);

      // Retry suggestion for network errors
      if (errorMsg.includes('network') || errorMsg.includes('connection')) {
        toast.warning('Retry', 'Check your connection and try submitting again');
      }
    } finally {
      setIsLoading(false);
    }
  }, [id, currentQuestion, currentAnswer, toast, stt]);

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

      // Retry suggestion
      if (errorMsg.includes('network') || errorMsg.includes('timeout')) {
        toast.warning('Retry', 'AI service may be slow. Try again in a moment.');
      }
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

  // Upload audio and submit practice attempt
  const handleSubmitPractice = useCallback(async () => {
    if (!id) return;

    const blob = confirmRecording();
    if (!blob) {
      toast.error('Error', 'No recording available');
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);

      // Create a temporary file for upload
      // Note: For practice, we need a preparation-specific upload endpoint
      // For now, we'll use a workaround with a dummy session/question
      const extension = mimeType ? getExtensionForMimeType(mimeType) : 'webm';
      const type = mimeType || 'audio/webm';
      const audioFile = new File([blob], `practice-${Date.now()}.${extension}`, { type });

      // Upload audio for practice
      const uploadResponse = await uploadAPI.uploadAudio(audioFile, null, null, id);
      const audioUrl = uploadResponse.data.audio_url;

      // Submit practice attempt
      await preparationAPI.submitPractice(id, audioUrl);

      toast.success('Practice submitted', 'Your delivery has been transcribed');

      // Reload attempts
      const attemptsResponse = await preparationAPI.getAttempts(id);
      setAttempts(attemptsResponse.data.attempts);

      // Reset recording
      resetRecording();
      setCurrentAttemptId(null);
    } catch (err) {
      const axiosError = err as AxiosError<{ message?: string }>;
      const errorMsg = axiosError.response?.data?.message || 'Failed to submit practice';
      setError(errorMsg);
      toast.error('Error', errorMsg);

      // Recovery suggestions
      if (errorMsg.includes('transcription') || errorMsg.includes('audio')) {
        toast.warning('Retry', 'Audio processing failed. Please try recording again.');
      } else if (errorMsg.includes('network') || errorMsg.includes('connection')) {
        toast.warning('Retry', 'Connection issue. Your recording is saved locally - try again.');
      }
    } finally {
      setIsSubmitting(false);
    }
  }, [id, confirmRecording, mimeType, toast, resetRecording]);

  // Recording handlers
  const handleStartRecording = async () => {
    try {
      if (!currentAttemptId && id) {
        // Start practice session if not started
        await handleStartPractice();
      }
      await startRecording();
    } catch (err) {
      const error = err as { message?: string };
      setError(error.message || 'Failed to start recording');
      toast.error('Error', 'Failed to start recording');
    }
  };

  const handleStopRecording = () => {
    stopRecording();
  };

  const handleCancelRecording = () => {
    clearPreview();
    resetRecording();
    setError(null);
  };

  // Auto-speak detective questions when enabled and supported
  useEffect(() => {
    if (stage !== 'detective' || !currentQuestion || !voiceEnabled || !isSpeechSupported) {
      stopSpeaking();
      return;
    }

    // Use conversation mode if enabled, otherwise use regular speak
    if (conversationModeEnabled) {
      conversation.startConversation();
      conversation.mentorSay(currentQuestion);
    } else {
      speak(currentQuestion);
    }
  }, [stage, currentQuestion, voiceEnabled, isSpeechSupported, speak, stopSpeaking, conversationModeEnabled, conversation]);

  // Cleanup TTS on unmount
  useEffect(() => () => stopSpeaking(), [stopSpeaking]);

  // Sync speech hook with saved preferences
  useEffect(() => {
    setVoiceEnabled(voiceSettings.enabled);
    setRate(voiceSettings.rate);
    setPitch(voiceSettings.pitch);
    setVolume(voiceSettings.volume);

    if (voiceSettings.voiceName && voices.length > 0) {
      const match = voices.find((v) => v.name === voiceSettings.voiceName);
      if (match) {
        setVoice(match);
      }
    }
  }, [setPitch, setRate, setVoice, setVolume, voiceSettings, voices]);

  // Update live transcript (not currently used but kept for future use)
  // Get question for coaching (use first detective question or generic)
  const practiceQuestion = qnaList.length > 0
    ? qnaList[0].question
    : 'Practice your prepared answer';

  // AI Coaching Hint hook for practice stage
  const {
    hint: coachingHint,
    isLoading: isHintLoading,
    isStreaming: isHintStreaming,
    error: hintError
  } = useCoachingHint({
    question: practiceQuestion,
    questionType: 'behavioral', // Default to behavioral for practice
    transcript: liveTranscript,
    enabled: isRecording && showCoach && stage === 'practice' && !!draft
  });

  // Track hints in history when they're received
  useEffect(() => {
    if (coachingHint && !isHintStreaming && !isHintLoading) {
      // Only add if it's a new hint (not already in history)
      setHintHistory((prev) => {
        const lastHint = prev[prev.length - 1];
        // Avoid duplicates - check if last hint is the same
        if (lastHint && lastHint.hint === coachingHint) {
          return prev;
        }
        const hintStage: 'detective' | 'practice' = stage === 'practice' ? 'practice' : 'detective';
        return [
          ...prev,
          {
            timestamp: new Date(),
            hint: coachingHint,
            stage: hintStage,
          },
        ].slice(-20); // Keep last 20 hints
      });
    }
  }, [coachingHint, isHintStreaming, isHintLoading, stage]);

  const handleTranscriptChange = useCallback((transcript: string) => {
    setLiveTranscript(transcript);
    // Transcript handling can be added here if needed in future
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

      // Reload attempts to get updated scores
      const attemptsResponse = await preparationAPI.getAttempts(id);
      setAttempts(attemptsResponse.data.attempts);

      // Show comparison
      setSelectedAttemptForComparison(attemptId);
      await loadComparison(id, attemptId);
    } catch (err) {
      const axiosError = err as AxiosError<{ message?: string }>;
      setError(axiosError.response?.data?.message || 'Failed to rate delivery');
      toast.error('Error', 'Failed to rate delivery');
    } finally {
      setIsRating(false);
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

  // View comparison for an attempt
  const handleViewComparison = useCallback(async (attemptId: string) => {
    if (!id) return;
    setSelectedAttemptForComparison(attemptId);
    await loadComparison(id, attemptId);
  }, [id, loadComparison]);

  // Start editing draft
  const handleStartEditDraft = useCallback(() => {
    setEditedDraft(draft);
    setIsEditingDraft(true);
  }, [draft]);

  // Cancel editing
  const handleCancelEditDraft = useCallback(() => {
    setIsEditingDraft(false);
    setEditedDraft('');
  }, []);

  // Save edited draft
  const handleSaveDraft = useCallback(async () => {
    if (!id || !editedDraft.trim()) {
      toast.error('Error', 'Draft cannot be empty');
      return;
    }

    try {
      setIsSavingDraft(true);
      setError(null);

      const response = await preparationAPI.updateDraft(id, editedDraft.trim());
      setDraft(response.data.draft_answer);
      setIsEditingDraft(false);
      setEditedDraft('');
      toast.success('Draft updated', 'Your changes have been saved');
    } catch (err) {
      const axiosError = err as AxiosError<{ message?: string }>;
      setError(axiosError.response?.data?.message || 'Failed to update draft');
      toast.error('Error', 'Failed to update draft');
    } finally {
      setIsSavingDraft(false);
    }
  }, [id, editedDraft, toast]);

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

        {/* Error Display with Recovery */}
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
            {/* Error recovery suggestions */}
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

        {/* Detective Stage */}
        {stage === 'detective' && !isComplete && (
          <div className="card p-8">
            <div className="mb-6">
              <div className="flex items-center gap-2 mb-2">
                <h2 className="heading-card">Step 1: Answer Questions</h2>
                <ContextualTooltip
                  content="Our AI coach will ask you 3-5 clarifying questions to understand your experience. Answer honestly and with specific examples - this helps us create a personalized, authentic draft answer for you."
                  position="right"
                  trigger="click"
                  title="How it works"
                />
              </div>
              <p className="text-text-secondary">
                Help us understand your experience so we can create a personalized answer.
              </p>
            </div>

            {/* Q&A History */}
            {qnaList.length > 0 && (
              <div className="mb-6 space-y-4">
                {qnaList.map((qna) => (
                  <div key={qna.order} className="bg-surface-secondary p-4 rounded-lg">
                    <p className="font-semibold text-text-primary mb-2">Q{qna.order}: {qna.question}</p>
                    <p className="text-text-secondary">{qna.answer}</p>
                  </div>
                ))}
              </div>
            )}

            {/* Current Question */}
            {currentQuestion && (
              <div className="mb-6">
                <div className="bg-electric-blue/10 border border-electric-blue/20 p-6 rounded-lg mb-4">
                  <p className="font-semibold text-text-primary mb-2">
                    Question {qnaList.length + 1}:
                  </p>
                  <p className="text-lg text-text-primary">{currentQuestion}</p>
                  <div className="flex flex-wrap items-center gap-3 mt-3">
                    <button
                      type="button"
                      onClick={() => {
                        if (!isSpeechSupported) return;
                        setVoiceEnabled((prev) => {
                          const next = !prev;
                          updateVoiceSettings({ enabled: next });
                          if (!next) {
                            stopSpeaking();
                            conversation.endConversation();
                          } else if (currentQuestion) {
                            speak(currentQuestion);
                          }
                          return next;
                        });
                      }}
                      className="btn-ghost flex items-center gap-2 text-sm"
                      disabled={!isSpeechSupported}
                    >
                      {voiceEnabled ? 'Mute mentor voice' : 'Enable mentor voice'}
                    </button>
                    {voiceEnabled && stt.isSupported && (
                      <button
                        type="button"
                        onClick={() => {
                          setConversationModeEnabled((prev) => {
                            const next = !prev;
                            if (!next) {
                              conversation.endConversation();
                            }
                            return next;
                          });
                        }}
                        className={`btn-ghost flex items-center gap-2 text-sm ${conversationModeEnabled ? 'text-electric-blue' : ''}`}
                      >
                        <MessageCircle size={14} />
                        {conversationModeEnabled ? 'Conversation mode ON' : 'Conversation mode'}
                      </button>
                    )}
                    {!conversationModeEnabled && isSpeaking && (
                      <span className="flex items-center gap-1 text-electric-blue text-sm">
                        <Loader2 size={14} className="animate-spin" />
                        Mentor is speaking
                      </span>
                    )}
                    {!isSpeechSupported && (
                      <span className="text-xs text-text-secondary">
                        Voice not supported in this browser
                      </span>
                    )}
                    {speechError && (
                      <span className="text-xs text-status-error">
                        TTS error: {speechError}
                      </span>
                    )}
                  </div>
                </div>

                {/* Conversation Mode Indicator */}
                {conversationModeEnabled && voiceEnabled && (
                  <ConversationIndicator
                    mode={conversation.mode}
                    mentorName="AI Mentor"
                    onInterrupt={conversation.interrupt}
                    isListening={stt.isListening}
                    className="mt-4"
                  />
                )}

                <div className="mb-4">
                  <div className="flex items-center justify-between mb-2">
                    <label className="block text-sm font-medium text-text-primary">
                      Your Answer
                    </label>
                    {/* Only show VoiceInputButton when NOT in conversation mode */}
                    {!conversationModeEnabled && (
                      <VoiceInputButton
                        onTranscript={(text) => {
                          // Append to existing answer or replace if empty
                          setCurrentAnswer((prev) =>
                            prev.trim() ? `${prev} ${text}`.trim() : text
                          );
                          setInterimTranscript('');
                        }}
                        onInterim={(text) => {
                          setInterimTranscript(text);
                        }}
                        disabled={isLoading}
                        placeholder="Listening..."
                        size="sm"
                      />
                    )}
                    {/* Show conversation mode listening status */}
                    {conversationModeEnabled && voiceEnabled && (
                      <div className="flex items-center gap-2">
                        {stt.isListening ? (
                          <>
                            <span className="relative flex h-3 w-3">
                              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-status-error opacity-75"></span>
                              <span className="relative inline-flex rounded-full h-3 w-3 bg-status-error"></span>
                            </span>
                            <span className="text-sm text-status-error font-medium">Listening...</span>
                            <button
                              type="button"
                              onClick={() => {
                                // Capture any in-progress transcript before stopping
                                if (stt.transcript) {
                                  setCurrentAnswer(stt.transcript);
                                }
                                stt.stopListening();
                                conversation.transitionTo('processing');
                              }}
                              className="btn-ghost text-xs text-status-error"
                            >
                              Done speaking
                            </button>
                          </>
                        ) : conversation.mode === 'user_turn' ? (
                          <button
                            type="button"
                            onClick={() => {
                              stt.startListening();
                            }}
                            className="btn-secondary text-xs flex items-center gap-1"
                          >
                            <Mic size={12} />
                            Start speaking
                          </button>
                        ) : (
                          <span className="text-sm text-text-tertiary">
                            {conversation.mode === 'mentor_speaking' ? 'Mentor speaking...' : 'Waiting...'}
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                  <textarea
                    value={currentAnswer}
                    onChange={(e) => setCurrentAnswer(e.target.value)}
                    placeholder={conversationModeEnabled ? "Your spoken answer will appear here..." : "Type your answer here or use voice input..."}
                    className="w-full min-h-[120px] p-4 border border-border-light rounded-lg bg-surface-primary text-text-primary resize-none focus:outline-none focus:ring-2 focus:ring-electric-blue"
                    disabled={isLoading}
                  />
                  {/* Interim transcript preview - for VoiceInputButton */}
                  {!conversationModeEnabled && interimTranscript && (
                    <div className="mt-2 p-2 bg-electric-blue/10 border border-electric-blue/20 rounded text-sm text-text-secondary italic">
                      <span className="text-electric-blue">Preview:</span> {interimTranscript}
                    </div>
                  )}
                  {/* Live transcript preview - for conversation mode */}
                  {conversationModeEnabled && stt.isListening && stt.transcript && (
                    <div className="mt-2 p-2 bg-electric-blue/10 border border-electric-blue/20 rounded text-sm text-text-secondary italic">
                      <span className="text-electric-blue">Hearing:</span> {stt.transcript}
                    </div>
                  )}
                </div>

                <button
                  onClick={handleSubmitAnswer}
                  disabled={isLoading || !currentAnswer.trim()}
                  className="btn-primary w-full"
                >
                  {isLoading ? (
                    <>
                      <Loader2 size={16} className="animate-spin" />
                      Submitting...
                    </>
                  ) : (
                    'Submit Answer'
                  )}
                </button>
              </div>
            )}

            {/* Loading Next Question */}
            {isLoading && !currentQuestion && (
              <div className="text-center py-8">
                <Loader2 size={32} className="animate-spin text-electric-blue mx-auto mb-4" />
                <p className="text-text-secondary">Generating your personalized question...</p>
                <p className="text-xs text-text-tertiary mt-2">This usually takes 2-3 seconds</p>
              </div>
            )}
          </div>
        )}

        {/* Draft Stage */}
        {stage === 'draft' && isComplete && !draft && (
          <div className="card p-8 text-center">
            <CheckCircle size={48} className="text-electric-blue mx-auto mb-4" />
            <h2 className="heading-card mb-2">Questions Complete!</h2>
            <p className="text-text-secondary mb-6">
              We have enough information. Ready to generate your personalized draft?
            </p>
            <button
              onClick={handleGenerateDraft}
              disabled={isGenerating}
              className="btn-primary"
            >
              {isGenerating ? (
                <>
                  <Loader2 size={16} className="animate-spin" />
                  <span className="flex items-center gap-2">
                    Generating Draft...
                    <span className="text-xs opacity-75">(10-15 seconds)</span>
                  </span>
                </>
              ) : (
                <>
                  <Sparkles size={16} />
                  Generate Draft
                </>
              )}
            </button>
          </div>
        )}

        {/* Draft Review */}
        {draft && stage !== 'practice' && (
          <div className="card p-8">
            <div className="mb-6 flex items-center justify-between">
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <h2 className="heading-card">Your Personalized Draft</h2>
                  <ContextualTooltip
                    content="This draft was generated using your answers from the questions above. It follows the STAR method (Situation, Task, Action, Result) and is tailored to your experience level. You can edit it before practicing."
                    position="right"
                    trigger="click"
                    title="AI-Generated Draft"
                  />
                </div>
                <p className="text-text-secondary">
                  Review and edit your draft answer. You can practice delivering it next.
                </p>
              </div>
              {!isEditingDraft && (
                <button
                  onClick={handleStartEditDraft}
                  className="btn-ghost flex items-center gap-2"
                >
                  <Edit2 size={16} />
                  Edit
                </button>
              )}
            </div>

            {isEditingDraft ? (
              <div className="mb-6">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <label className="block text-sm font-medium text-text-primary">
                      Edit Draft
                    </label>
                    <span className="text-xs text-text-tertiary">
                      (Select text to replace, or click to append)
                    </span>
                  </div>
                  <VoiceInputButton
                    onTranscript={(text) => {
                      const textarea = draftTextareaRef.current;
                      if (!textarea) return;

                      const start = textarea.selectionStart;
                      const end = textarea.selectionEnd;
                      const currentValue = editedDraft;

                      if (start !== end) {
                        // Replace selection mode
                        const newValue =
                          currentValue.substring(0, start) +
                          text +
                          currentValue.substring(end);
                        setEditedDraft(newValue);
                        // Restore cursor position after the inserted text
                        setTimeout(() => {
                          textarea.focus();
                          textarea.setSelectionRange(start + text.length, start + text.length);
                        }, 0);
                      } else {
                        // Append mode - add to end or at cursor with space
                        const insertText = start === currentValue.length || currentValue[start - 1] === ' ' || currentValue[start - 1] === '\n'
                          ? text
                          : ` ${text}`;
                        const newValue =
                          currentValue.substring(0, start) +
                          insertText +
                          currentValue.substring(end);
                        setEditedDraft(newValue);
                        // Restore cursor position after the inserted text
                        setTimeout(() => {
                          textarea.focus();
                          textarea.setSelectionRange(start + insertText.length, start + insertText.length);
                        }, 0);
                      }
                      setDraftInterimTranscript('');
                    }}
                    onInterim={(text) => {
                      setDraftInterimTranscript(text);
                    }}
                    disabled={isSavingDraft}
                    placeholder="Listening..."
                    size="sm"
                  />
                </div>
                <textarea
                  ref={draftTextareaRef}
                  value={editedDraft}
                  onChange={(e) => setEditedDraft(e.target.value)}
                  className="w-full min-h-[300px] p-4 border border-border-light rounded-lg bg-surface-primary text-text-primary font-mono text-sm resize-none focus:outline-none focus:ring-2 focus:ring-electric-blue"
                  placeholder="Edit your draft answer..."
                />
                {/* Interim transcript preview for draft */}
                {draftInterimTranscript && (
                  <div className="mt-2 p-2 bg-electric-blue/10 border border-electric-blue/20 rounded text-sm text-text-secondary italic">
                    <span className="text-electric-blue">Preview:</span> {draftInterimTranscript}
                  </div>
                )}
                <div className="flex items-center gap-4 mt-4">
                  <button
                    onClick={handleSaveDraft}
                    disabled={isSavingDraft || !editedDraft.trim()}
                    className="btn-primary flex items-center gap-2"
                  >
                    {isSavingDraft ? (
                      <>
                        <Loader2 size={16} className="animate-spin" />
                        Saving...
                      </>
                    ) : (
                      <>
                        <Save size={16} />
                        Save Changes
                      </>
                    )}
                  </button>
                  <button
                    onClick={handleCancelEditDraft}
                    disabled={isSavingDraft}
                    className="btn-secondary flex items-center gap-2"
                  >
                    <X size={16} />
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <div className="bg-surface-secondary p-6 rounded-lg mb-6">
                <div className="prose prose-sm max-w-none dark:prose-invert">
                  <pre className="whitespace-pre-wrap font-sans text-text-primary">{draft}</pre>
                </div>
              </div>
            )}

            {!isEditingDraft && (
              <div className="flex items-center gap-4">
                <button
                  onClick={() => navigate('/questions')}
                  className="btn-secondary"
                >
                  Done
                </button>
                <button
                  onClick={handleStartPractice}
                  disabled={isLoading}
                  className="btn-primary"
                >
                  {isLoading ? (
                    <>
                      <Loader2 size={16} className="animate-spin" />
                      Starting...
                    </>
                  ) : (
                    'Start Practice'
                  )}
                </button>
              </div>
            )}
          </div>
        )}

        {/* Practice Stage */}
        {stage === 'practice' && draft && (
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
                  onConfirm={handleSubmitPractice}
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
                    onClick={() => {
                      setSelectedAttemptForComparison(null);
                      setComparisonData(null);
                    }}
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
                  {/* Draft Column */}
                  <div className="bg-surface-secondary p-4 rounded-lg">
                    <h3 className="text-sm font-semibold text-text-primary mb-2">Your Draft (Planned)</h3>
                    <div className="prose prose-sm max-w-none dark:prose-invert">
                      <pre className="whitespace-pre-wrap font-sans text-text-primary text-sm bg-surface-primary p-3 rounded">
                        {comparisonData.draft}
                      </pre>
                    </div>
                  </div>

                  {/* Delivery Column */}
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

                {/* Iteration Actions */}
                <div className="mt-6 flex items-center gap-4 pt-4 border-t border-border-light">
                  <button
                    onClick={() => {
                      setSelectedAttemptForComparison(null);
                      setComparisonData(null);
                      resetRecording();
                      handleStartPractice();
                    }}
                    className="btn-secondary flex items-center gap-2"
                  >
                    <RefreshCw size={16} />
                    Try Again
                  </button>
                  <button
                    onClick={() => {
                      setSelectedAttemptForComparison(null);
                      setComparisonData(null);
                      handleStartEditDraft();
                    }}
                    className="btn-secondary flex items-center gap-2"
                  >
                    <Wand2 size={16} />
                    Refine Draft
                  </button>
                  <button
                    onClick={() => {
                      setSelectedAttemptForComparison(null);
                      setComparisonData(null);
                    }}
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
        )}
      </div>
    </div>
  );
}
