import { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { BookOpen, AlertCircle, Search, X, Play } from 'lucide-react';
import { questionsAPI, interviewsAPI, preparationAPI } from '../lib/api';
import { useAuth } from '../hooks/useAuth';
import { useToast } from '../hooks/useToast';
import { usePrepUsage } from '../hooks/usePrepUsage';
import { useScrollDirection } from '../hooks/useScrollDirection';
import { analytics, Events } from '../lib/analytics';
import QuestionCard from '../components/questions/QuestionCard';
import QuestionFilters, { type QuestionFiltersState } from '../components/questions/QuestionFilters';
import UpgradeModal from '../components/subscription/UpgradeModal';
import type { Question } from '../types';

export default function QuestionsPage() {
  const navigate = useNavigate();
  const toast = useToast();

  const [questions, setQuestions] = useState<Question[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showUpgradeModal, setShowUpgradeModal] = useState(false);
  const [isPracticing, setIsPracticing] = useState(false);
  const { user } = useAuth();
  const { isLimitReached, remaining, prepLimit, incrementUsage } = usePrepUsage();

  // Scroll-aware filter behavior
  const scrollDirection = useScrollDirection({ threshold: 15 });
  const [isFilterExpanded, setIsFilterExpanded] = useState(false);
  const prevScrollDirection = useRef(scrollDirection);

  // Auto-collapse filter panel when scrolling down
  useEffect(() => {
    if (scrollDirection === 'down' && prevScrollDirection.current !== 'down' && isFilterExpanded) {
      setIsFilterExpanded(false);
    }
    prevScrollDirection.current = scrollDirection;
  }, [scrollDirection, isFilterExpanded]);

  // Header hides on scroll down, so filter should move up
  const headerHidden = scrollDirection === 'down';

  const [filters, setFilters] = useState<QuestionFiltersState>({
    category: '',
    difficulty: '',
    search: '',
    company: '',
  });

  // Load questions
  useEffect(() => {
    const loadQuestions = async () => {
      try {
        setIsLoading(true);
        setError(null);

        const params: { category?: string; difficulty?: string } = {};
        if (filters.category) params.category = filters.category;
        if (filters.difficulty) params.difficulty = filters.difficulty;

        const response = await questionsAPI.getAll(params);
        setQuestions(response.data);
      } catch (err: unknown) {
        const error = err as { response?: { data?: { message?: string } } };
        setError(error.response?.data?.message || 'Failed to load questions');
      } finally {
        setIsLoading(false);
      }
    };

    loadQuestions();
  }, [filters.category, filters.difficulty]);

  // Extract unique company tags from questions
  const companyOptions = useMemo(() => {
    const companies = new Set<string>();
    questions.forEach((q) => {
      q.company_tags?.forEach((tag) => companies.add(tag));
    });
    return Array.from(companies).sort();
  }, [questions]);

  // Client-side filtering for search and company
  const filteredQuestions = useMemo(() => {
    return questions.filter((q) => {
      // Search filter
      if (filters.search) {
        const searchLower = filters.search.toLowerCase();
        const matchesContent = q.content.toLowerCase().includes(searchLower);
        const matchesTopic = q.topic_tags?.some((t) =>
          t.toLowerCase().includes(searchLower)
        );
        if (!matchesContent && !matchesTopic) return false;
      }

      // Company filter
      if (filters.company) {
        if (!q.company_tags?.includes(filters.company)) return false;
      }

      return true;
    });
  }, [questions, filters.search, filters.company]);

  // Handle quick practice
  const handlePractice = useCallback(
    async (question: Question) => {
      try {
        setIsPracticing(true);

        // Create a quick practice session with specific question
        const response = await interviewsAPI.quickPractice(question.id);

        const session = response.data;
        toast.success('Practice session created', 'Starting your practice...');
        navigate(`/interview/${session.id}`);
      } catch (err: unknown) {
        const error = err as { response?: { status?: number; data?: { message?: string } } };
        if (error.response?.status === 402) {
          analytics.track(Events.LIMIT_REACHED, {
            limit_type: 'interview_sessions',
            trigger: 'quick_practice',
          });
          setShowUpgradeModal(true);
          toast.error('Limit reached', 'Upgrade to Pro for unlimited practice');
        } else {
          toast.error('Error', error.response?.data?.message || 'Failed to start practice');
        }
      } finally {
        setIsPracticing(false);
      }
    },
    [navigate, toast]
  );

  const handleFilterChange = useCallback((newFilters: QuestionFiltersState) => {
    setFilters(newFilters);
  }, []);

  // Listen for header contextual action to start random practice
  useEffect(() => {
    const handleRandomPractice = () => {
      if (filteredQuestions.length > 0 && !isPracticing) {
        const randomIndex = Math.floor(Math.random() * filteredQuestions.length);
        handlePractice(filteredQuestions[randomIndex]);
      }
    };
    window.addEventListener('random-practice', handleRandomPractice);
    return () => window.removeEventListener('random-practice', handleRandomPractice);
  }, [filteredQuestions, isPracticing, handlePractice]);

  // Handle prepare answer
  const handlePrepare = useCallback(
    async (question: Question) => {
      // Check free tier limits (Pro/Team users bypass)
      const isPaidUser = user?.subscription_tier === 'pro' || user?.subscription_tier === 'team';
      if (!isPaidUser && isLimitReached) {
        analytics.track(Events.LIMIT_REACHED, {
          limit_type: 'preparations',
          trigger: 'prepare_answer',
          current_usage: prepLimit - remaining,
          limit: prepLimit,
        });
        setShowUpgradeModal(true);
        toast.error('Limit reached', `Free tier allows ${prepLimit} preparations per month. Upgrade for unlimited.`);
        return;
      }

      try {
        const response = await preparationAPI.start(question.id);
        const { preparation_id } = response.data;

        // Track usage for free tier
        if (!isPaidUser) {
          incrementUsage();
        }

        toast.success('Preparation started', 'Answer the questions to get a personalized draft');
        navigate(`/preparation/${preparation_id}`);
      } catch (err: unknown) {
        const error = err as { response?: { status?: number; data?: { message?: string } } };
        if (error.response?.status === 402) {
          analytics.track(Events.LIMIT_REACHED, {
            limit_type: 'preparations',
            trigger: 'prepare_answer_api',
          });
          setShowUpgradeModal(true);
          toast.error('Upgrade required', 'Answer preparation is available for Pro and Premium subscribers');
        } else {
          toast.error('Error', error.response?.data?.message || 'Failed to start preparation');
        }
      }
    },
    [navigate, toast, user?.subscription_tier, isLimitReached, prepLimit, incrementUsage]
  );

  // All users can now access prepare (with usage limits for free tier)
  const isPaidUser = user?.subscription_tier === 'pro' || user?.subscription_tier === 'team';

  return (
    <div className="min-h-screen bg-surface-primary">
      <div className="container mx-auto px-4 sm:px-6 py-6 sm:py-8 max-w-7xl">
        {/* Header */}
        <div className="mb-8 sm:mb-10">
          <div className="flex items-start sm:items-center gap-4 mb-3">
            <div className="p-3 rounded-2xl bg-gradient-to-br from-electric-blue/10 to-electric-blue/5 border border-electric-blue/20">
              <BookOpen className="w-7 h-7 sm:w-8 sm:h-8 text-electric-blue" />
            </div>
            <div className="flex-1">
              <h1 className="heading-page mb-1">Question Bank</h1>
              <p className="text-sm sm:text-base text-text-secondary max-w-2xl">
                Browse {questions.length > 0 ? `${questions.length} ` : ''}interview questions and practice any topic.
                Filter by category, difficulty, or company.
              </p>
            </div>
          </div>
        </div>

        {/* Filters - Sticky on mobile, moves up when header hides */}
        <div
          className={`sticky z-10 -mx-4 sm:-mx-6 px-4 sm:px-6 py-2 bg-[hsl(var(--background)/0.95)] backdrop-blur-md border-b border-border-light transition-all duration-300 ease-out md:relative md:top-0 md:mx-0 md:px-0 md:py-0 md:bg-transparent md:backdrop-blur-none md:border-b-0 ${
            headerHidden ? 'top-0' : 'top-[52px] sm:top-[60px]'
          }`}
        >
          <QuestionFilters
            filters={filters}
            onFilterChange={handleFilterChange}
            companyOptions={companyOptions}
            isExpanded={isFilterExpanded}
            onExpandedChange={setIsFilterExpanded}
          />
        </div>

        {/* Results Count */}
        {!isLoading && !error && (
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-2">
              <div className="h-1.5 w-1.5 rounded-full bg-electric-blue animate-pulse" />
              <p className="text-sm font-medium text-text-secondary">
                Showing <span className="text-electric-blue font-semibold">{filteredQuestions.length}</span> of{' '}
                <span className="text-text-primary font-semibold">{questions.length}</span> questions
              </p>
            </div>
            {filteredQuestions.length > 0 && (
              <p className="text-xs text-text-tertiary">
                Click any card to start practicing
              </p>
            )}
          </div>
        )}

        {/* Loading State */}
        {isLoading && (
          <div className="card p-16 text-center">
            <div className="relative inline-flex items-center justify-center mb-6">
              <div className="absolute animate-spin rounded-full h-16 w-16 border-4 border-electric-blue/20 border-t-electric-blue"></div>
              <BookOpen className="w-8 h-8 text-electric-blue/60 animate-pulse" />
            </div>
            <p className="text-lg font-medium text-text-primary mb-2">Loading questions...</p>
            <p className="text-sm text-text-secondary">Preparing your question bank</p>
          </div>
        )}

        {/* Error State */}
        {error && !isLoading && (
          <div className="card p-10 border-2 border-status-error/30 bg-gradient-to-br from-status-error/5 to-status-error/10">
            <div className="flex flex-col items-center text-center">
              <div className="p-4 rounded-full bg-status-error/10 mb-4">
                <AlertCircle size={32} className="text-status-error" />
              </div>
              <h3 className="heading-card text-status-error mb-2">Failed to load questions</h3>
              <p className="text-text-secondary mb-6 max-w-md">{error}</p>
              <button
                onClick={() => window.location.reload()}
                className="btn-primary bg-status-error hover:bg-status-error/90"
              >
                Try Again
              </button>
            </div>
          </div>
        )}

        {/* Empty State */}
        {!isLoading && !error && filteredQuestions.length === 0 && (
          <div className="card p-16 text-center">
            <div className="relative inline-flex items-center justify-center mb-6">
              <div className="absolute w-20 h-20 rounded-full bg-electric-blue/10 blur-xl" />
              <div className="relative p-5 rounded-2xl bg-gradient-to-br from-surface-secondary to-surface-tertiary border border-border-light">
                <Search size={40} className="text-text-tertiary" />
              </div>
            </div>
            <h3 className="heading-section mb-3">No questions found</h3>
            <p className="text-text-secondary mb-6 max-w-md mx-auto">
              We couldn't find any questions matching your criteria. Try adjusting your filters or search terms.
            </p>
            <button
              onClick={() =>
                setFilters({ category: '', difficulty: '', search: '', company: '' })
              }
              className="btn-secondary inline-flex items-center gap-2"
            >
              <X size={18} />
              Clear All Filters
            </button>
          </div>
        )}

        {/* Questions Grid */}
        {!isLoading && !error && filteredQuestions.length > 0 && (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5 md:gap-6">
              {filteredQuestions.map((question) => (
                <QuestionCard
                  key={question.id}
                  question={question}
                  onPractice={handlePractice}
                  onPrepare={handlePrepare}
                  prepRemaining={isPaidUser ? undefined : remaining}
                />
              ))}
            </div>

            {/* Pagination hint for large result sets */}
            {filteredQuestions.length > 20 && (
              <div className="mt-8 pt-6 border-t border-border-light text-center">
                <p className="text-sm text-text-tertiary">
                  Showing all {filteredQuestions.length} questions. Use filters to narrow down results.
                </p>
              </div>
            )}
          </>
        )}

        {/* Practice Loading Overlay */}
        {isPracticing && (
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 animate-in fade-in duration-200">
            <div className="card p-10 text-center shadow-2xl max-w-sm mx-4">
              <div className="relative inline-flex items-center justify-center mb-6">
                <div className="absolute animate-spin rounded-full h-16 w-16 border-4 border-electric-blue/20 border-t-electric-blue"></div>
                <Play className="w-7 h-7 text-electric-blue animate-pulse" />
              </div>
              <p className="text-lg font-semibold text-text-primary mb-2">Creating practice session...</p>
              <p className="text-sm text-text-secondary">This will only take a moment</p>
            </div>
          </div>
        )}
      </div>

      {/* Upgrade Modal */}
      <UpgradeModal
        isOpen={showUpgradeModal}
        onClose={() => setShowUpgradeModal(false)}
        currentTier="free"
        onSuccess={() => setShowUpgradeModal(false)}
      />
    </div>
  );
}
