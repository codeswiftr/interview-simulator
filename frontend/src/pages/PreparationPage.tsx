import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Sparkles, Loader2, CheckCircle, AlertCircle, History, TrendingUp, BarChart3 } from 'lucide-react';
import { preparationAPI, uploadAPI } from '../lib/api';
import { useToast } from '../hooks/useToast';
import { useAuth } from '../hooks/useAuth';
import { useAudioRecording } from '../hooks/useAudioRecording';
import RecordingDeck from '../components/interview/RecordingDeck';
import { getExtensionForMimeType } from '../lib/audio-utils';
import type { AxiosError } from 'axios';

type PreparationStage = 'detective' | 'draft' | 'practice' | 'complete';

interface DetectiveQnA {
  question: string;
  answer: string;
  order: number;
}

export default function PreparationPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const toast = useToast();
  const { user } = useAuth();

  const [stage, setStage] = useState<PreparationStage>('detective');
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
  const [liveTranscript, setLiveTranscript] = useState('');
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
    mimeType,
  } = useAudioRecording();

  // Load preparation state
  useEffect(() => {
    if (!id) {
      navigate('/questions');
      return;
    }

    // Check if we have a draft (stage = practice or complete)
    const loadDraft = async () => {
      try {
        const response = await preparationAPI.getDraft(id);
        if (response.data.draft_answer) {
          setDraft(response.data.draft_answer);
          setStage(response.data.stage as PreparationStage);
        } else {
          // Start detective stage
          getNextQuestion();
        }
      } catch (err) {
        // Draft not generated yet, continue with detective stage
        getNextQuestion();
      }
    };

    loadDraft();
  }, [id, navigate]);

  // Load attempts when in practice stage
  useEffect(() => {
    if (!id || stage !== 'practice') return;

    const loadAttempts = async () => {
      try {
        const response = await preparationAPI.getAttempts(id);
        setAttempts(response.data.attempts);
      } catch (err) {
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
      setError(axiosError.response?.data?.message || 'Failed to get question');
      toast.error('Error', 'Failed to get next question');
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
      setError(axiosError.response?.data?.message || 'Failed to submit answer');
      toast.error('Error', 'Failed to submit answer');
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
      setError(axiosError.response?.data?.message || 'Failed to generate draft');
      toast.error('Error', 'Failed to generate draft');
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
      const response = await preparationAPI.submitPractice(id, audioUrl);
      
      toast.success('Practice submitted', 'Your delivery has been transcribed');
      
      // Reload attempts
      const attemptsResponse = await preparationAPI.getAttempts(id);
      setAttempts(attemptsResponse.data.attempts);
      
      // Reset recording
      resetRecording();
      setCurrentAttemptId(null);
    } catch (err) {
      const axiosError = err as AxiosError<{ message?: string }>;
      setError(axiosError.response?.data?.message || 'Failed to submit practice');
      toast.error('Error', 'Failed to submit practice attempt');
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

  // Update live transcript
  const handleTranscriptChange = useCallback((transcript: string) => {
    setLiveTranscript(transcript);
  }, []);

  // Rate delivery attempt
  const handleRateAttempt = useCallback(async (attemptId: string) => {
    if (!id) return;

    try {
      setIsRating(true);
      setError(null);

      const response = await preparationAPI.rateDelivery(id, attemptId);
      
      toast.success('Delivery rated', `Score: ${response.data.delivery_score.toFixed(1)}%`);
      
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

        {/* Error Display */}
        {error && (
          <div className="card p-4 mb-6 border-status-error/20 bg-status-error/5">
            <div className="flex items-center gap-3 text-status-error">
              <AlertCircle size={20} />
              <p className="body-small">{error}</p>
            </div>
          </div>
        )}

        {/* Detective Stage */}
        {stage === 'detective' && !isComplete && (
          <div className="card p-8">
            <div className="mb-6">
              <h2 className="heading-card mb-2">Step 1: Answer Questions</h2>
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
                </div>

                <div className="mb-4">
                  <label className="block text-sm font-medium text-text-primary mb-2">
                    Your Answer
                  </label>
                  <textarea
                    value={currentAnswer}
                    onChange={(e) => setCurrentAnswer(e.target.value)}
                    placeholder="Type your answer here..."
                    className="w-full min-h-[120px] p-4 border border-border-light rounded-lg bg-surface-primary text-text-primary resize-none focus:outline-none focus:ring-2 focus:ring-electric-blue"
                    disabled={isLoading}
                  />
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
                <p className="text-text-secondary">Getting next question...</p>
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
                  Generating Draft...
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
            <div className="mb-6">
              <h2 className="heading-card mb-2">Your Personalized Draft</h2>
              <p className="text-text-secondary">
                Review and edit your draft answer. You can practice delivering it next.
              </p>
            </div>

            <div className="bg-surface-secondary p-6 rounded-lg mb-6">
              <div className="prose prose-sm max-w-none dark:prose-invert">
                <pre className="whitespace-pre-wrap font-sans text-text-primary">{draft}</pre>
              </div>
            </div>

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
              <h2 className="heading-card mb-4">Practice Your Delivery</h2>
              <p className="text-text-secondary mb-6">
                Record yourself delivering your prepared answer. You can practice multiple times.
              </p>

              {recordingError && (
                <div className="mb-4 p-4 bg-status-error/10 border border-status-error/20 rounded-lg">
                  <p className="text-status-error text-sm">{recordingError}</p>
                </div>
              )}

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

              {isSubmitting && (
                <div className="mt-4 text-center">
                  <Loader2 size={20} className="animate-spin text-electric-blue mx-auto mb-2" />
                  <p className="text-text-secondary text-sm">Submitting and transcribing...</p>
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
                                    Rating...
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
