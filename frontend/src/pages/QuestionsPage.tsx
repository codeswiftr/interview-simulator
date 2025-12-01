import { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { BookOpen, AlertCircle, Search } from 'lucide-react';
import { questionsAPI, interviewsAPI } from '../lib/api';
import { useToast } from '../hooks/useToast';
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

  return (
    <div className="min-h-screen bg-surface-primary">
      <div className="container mx-auto px-6 py-8 max-w-7xl">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <BookOpen className="w-8 h-8 text-electric-blue" />
            <h1 className="heading-page">Question Bank</h1>
          </div>
          <p className="text-text-secondary">
            Browse interview questions and practice any topic. Filter by category, difficulty, or company.
          </p>
        </div>

        {/* Filters */}
        <QuestionFilters
          filters={filters}
          onFilterChange={handleFilterChange}
          companyOptions={companyOptions}
        />

        {/* Results Count */}
        {!isLoading && !error && (
          <div className="flex items-center justify-between mb-4">
            <p className="text-sm text-text-secondary">
              Showing {filteredQuestions.length} of {questions.length} questions
            </p>
          </div>
        )}

        {/* Loading State */}
        {isLoading && (
          <div className="card p-12 text-center">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-electric-blue border-t-transparent mb-4"></div>
            <p className="text-text-secondary">Loading questions...</p>
          </div>
        )}

        {/* Error State */}
        {error && !isLoading && (
          <div className="card p-8 border-status-error/20 bg-status-error/5">
            <div className="flex items-center gap-3 text-status-error">
              <AlertCircle size={24} />
              <div>
                <p className="font-semibold mb-1">Failed to load questions</p>
                <p className="body-small">{error}</p>
              </div>
            </div>
            <button
              onClick={() => window.location.reload()}
              className="btn-secondary mt-4"
            >
              Try Again
            </button>
          </div>
        )}

        {/* Empty State */}
        {!isLoading && !error && filteredQuestions.length === 0 && (
          <div className="card p-12 text-center">
            <Search size={48} className="text-text-tertiary mx-auto mb-4" />
            <h3 className="heading-card mb-2">No questions found</h3>
            <p className="text-text-secondary mb-4">
              Try adjusting your filters or search terms.
            </p>
            <button
              onClick={() =>
                setFilters({ category: '', difficulty: '', search: '', company: '' })
              }
              className="btn-secondary"
            >
              Clear Filters
            </button>
          </div>
        )}

        {/* Questions Grid */}
        {!isLoading && !error && filteredQuestions.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredQuestions.map((question) => (
              <QuestionCard
                key={question.id}
                question={question}
                onPractice={handlePractice}
              />
            ))}
          </div>
        )}

        {/* Practice Loading Overlay */}
        {isPracticing && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="card p-8 text-center">
              <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-electric-blue border-t-transparent mb-4"></div>
              <p className="text-text-secondary">Creating practice session...</p>
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
