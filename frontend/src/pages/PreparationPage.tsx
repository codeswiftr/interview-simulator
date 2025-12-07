import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Sparkles, Loader2, CheckCircle, AlertCircle } from 'lucide-react';
import { preparationAPI } from '../lib/api';
import { useToast } from '../hooks/useToast';
import { useAuth } from '../hooks/useAuth';
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
        {draft && (
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
                onClick={() => navigate(`/interview?practice_draft=${id}`)}
                className="btn-primary"
              >
                Practice Delivery
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
