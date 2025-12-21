import { describe, expect, it, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';
import QuestionsPage from '../QuestionsPage';
import { AuthProvider } from '../../hooks/useAuth';
import { ToastProvider } from '../../hooks/useToast';
import type { Question } from '../../types';

// Mock data
const mockQuestions: Question[] = [
  {
    id: 'q1',
    category: 'behavioral',
    difficulty: 'easy',
    content: 'Tell me about a time you faced a challenging project',
    company_tags: ['Google', 'Amazon'],
    topic_tags: ['leadership', 'teamwork'],
    expected_duration_seconds: 180,
    is_active: true,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 'q2',
    category: 'technical',
    difficulty: 'medium',
    content: 'Explain the difference between let, const, and var in JavaScript',
    company_tags: ['Microsoft', 'Meta'],
    topic_tags: ['javascript', 'fundamentals'],
    expected_duration_seconds: 300,
    is_active: true,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 'q3',
    category: 'system_design',
    difficulty: 'hard',
    content: 'Design a URL shortening service like bit.ly',
    company_tags: ['Google', 'Meta'],
    topic_tags: ['system design', 'scalability'],
    expected_duration_seconds: 2700,
    is_active: true,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 'q4',
    category: 'behavioral',
    difficulty: 'medium',
    content: 'Describe a situation where you had to deal with a difficult stakeholder',
    company_tags: ['Amazon'],
    topic_tags: ['communication', 'conflict resolution'],
    expected_duration_seconds: 240,
    is_active: true,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
];

const mockUser = {
  id: 'user1',
  email: 'test@example.com',
  full_name: 'Test User',
  experience_level: 'mid' as const,
  subscription_tier: 'free' as const,
  interviews_this_month: 2,
  total_interviews: 10,
  created_at: '2024-01-01T00:00:00Z',
};

const mockProUser = {
  ...mockUser,
  subscription_tier: 'pro' as const,
};

// Setup MSW server
const API_BASE_URL = 'http://localhost:8000/api/v1';

const handlers = [
  // Get all questions
  http.get(`${API_BASE_URL}/questions`, ({ request }) => {
    const url = new URL(request.url);
    const category = url.searchParams.get('category');
    const difficulty = url.searchParams.get('difficulty');

    let filtered = [...mockQuestions];

    if (category) {
      filtered = filtered.filter((q) => q.category === category);
    }

    if (difficulty) {
      filtered = filtered.filter((q) => q.difficulty === difficulty);
    }

    return HttpResponse.json({ data: filtered });
  }),

  // Get current user
  http.get(`${API_BASE_URL}/users/me`, () => {
    return HttpResponse.json(mockUser);
  }),

  // Quick practice
  http.post(`${API_BASE_URL}/interviews/quick-practice`, () => {
    return HttpResponse.json({
      data: {
        id: 'session1',
        interview_type: 'behavioral',
        status: 'in_progress',
        question_count: 1,
        created_at: '2024-01-01T00:00:00Z',
      },
    });
  }),

  // Start preparation
  http.post(`${API_BASE_URL}/preparation/start`, () => {
    return HttpResponse.json({
      data: {
        preparation_id: 'prep1',
        stage: 'detective',
        message: 'Preparation started',
      },
    });
  }),
];

const server = setupServer(...handlers);

// Test wrapper component
function TestWrapper({ children }: { children: React.ReactNode }) {
  return (
    <MemoryRouter initialEntries={['/questions']}>
      <AuthProvider>
        <ToastProvider>
          <Routes>
            <Route path="/questions" element={children} />
            <Route path="/interview/:id" element={<div>Interview Page</div>} />
            <Route path="/preparation/:id" element={<div>Preparation Page</div>} />
          </Routes>
        </ToastProvider>
      </AuthProvider>
    </MemoryRouter>
  );
}

describe('QuestionsPage', () => {
  beforeEach(() => {
    server.listen({ onUnhandledRequest: 'error' });
    localStorage.clear();
    localStorage.setItem('access_token', 'mock-token');
  });

  afterEach(() => {
    server.resetHandlers();
    server.close();
  });

  describe('Basic Rendering', () => {
    it('renders page header correctly', async () => {
      render(
        <TestWrapper>
          <QuestionsPage />
        </TestWrapper>
      );

      expect(screen.getByText('Question Bank')).toBeInTheDocument();
      expect(
        screen.getByText(/Browse interview questions and practice any topic/)
      ).toBeInTheDocument();
    });

    it('renders filters component', async () => {
      render(
        <TestWrapper>
          <QuestionsPage />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByPlaceholderText('Search questions...')).toBeInTheDocument();
      });

      expect(screen.getByRole('combobox', { name: /category/i })).toBeInTheDocument();
      expect(screen.getByRole('combobox', { name: /difficulty/i })).toBeInTheDocument();
    });
  });

  describe('Loading State', () => {
    it('displays loading state initially', () => {
      render(
        <TestWrapper>
          <QuestionsPage />
        </TestWrapper>
      );

      expect(screen.getByText('Loading questions...')).toBeInTheDocument();
      const spinner = document.querySelector('.animate-spin');
      expect(spinner).toBeInTheDocument();
    });

    it('hides loading state after data loads', async () => {
      render(
        <TestWrapper>
          <QuestionsPage />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.queryByText('Loading questions...')).not.toBeInTheDocument();
      });
    });
  });

  describe('Question List Display', () => {
    it('displays all questions after loading', async () => {
      render(
        <TestWrapper>
          <QuestionsPage />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/Tell me about a time you faced a challenging project/)).toBeInTheDocument();
      });

      expect(screen.getByText(/Explain the difference between let, const, and var/)).toBeInTheDocument();
      expect(screen.getByText(/Design a URL shortening service/)).toBeInTheDocument();
      expect(screen.getByText(/Describe a situation where you had to deal with a difficult stakeholder/)).toBeInTheDocument();
    });

    it('displays question count', async () => {
      render(
        <TestWrapper>
          <QuestionsPage />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/Showing 4 of 4 questions/)).toBeInTheDocument();
      });
    });

    it('displays question metadata correctly', async () => {
      render(
        <TestWrapper>
          <QuestionsPage />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/Tell me about a time you faced a challenging project/)).toBeInTheDocument();
      });

      // Check for category badges
      expect(screen.getByText('Behavioral')).toBeInTheDocument();
      expect(screen.getByText('Technical')).toBeInTheDocument();
      expect(screen.getByText('System Design')).toBeInTheDocument();

      // Check for difficulty badges
      expect(screen.getByText('Easy')).toBeInTheDocument();
      expect(screen.getAllByText('Medium')).toHaveLength(2);
      expect(screen.getByText('Hard')).toBeInTheDocument();

      // Check for duration
      expect(screen.getByText(/3 min expected/)).toBeInTheDocument();
      expect(screen.getByText(/5 min expected/)).toBeInTheDocument();
      expect(screen.getByText(/45 min expected/)).toBeInTheDocument();
    });

    it('displays company tags', async () => {
      render(
        <TestWrapper>
          <QuestionsPage />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Google')).toBeInTheDocument();
      });

      expect(screen.getByText('Amazon')).toBeInTheDocument();
      expect(screen.getByText('Microsoft')).toBeInTheDocument();
      expect(screen.getByText('Meta')).toBeInTheDocument();
    });

    it('displays action buttons for each question', async () => {
      render(
        <TestWrapper>
          <QuestionsPage />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getAllByText('Practice')).toHaveLength(4);
      });

      expect(screen.getAllByText('Prepare')).toHaveLength(4);
    });
  });

  describe('Filter Functionality', () => {
    it('filters questions by category', async () => {
      const user = userEvent.setup();

      render(
        <TestWrapper>
          <QuestionsPage />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/Showing 4 of 4 questions/)).toBeInTheDocument();
      });

      // Select behavioral category
      const categorySelect = screen.getByRole('combobox', { name: /category/i });
      await user.selectOptions(categorySelect, 'behavioral');

      await waitFor(() => {
        expect(screen.getByText(/Showing 2 of 2 questions/)).toBeInTheDocument();
      });

      expect(screen.getByText(/Tell me about a time you faced a challenging project/)).toBeInTheDocument();
      expect(screen.getByText(/Describe a situation where you had to deal with a difficult stakeholder/)).toBeInTheDocument();
      expect(screen.queryByText(/Explain the difference between let, const, and var/)).not.toBeInTheDocument();
    });

    it('filters questions by difficulty', async () => {
      const user = userEvent.setup();

      render(
        <TestWrapper>
          <QuestionsPage />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/Showing 4 of 4 questions/)).toBeInTheDocument();
      });

      // Select medium difficulty
      const difficultySelect = screen.getByRole('combobox', { name: /difficulty/i });
      await user.selectOptions(difficultySelect, 'medium');

      await waitFor(() => {
        expect(screen.getByText(/Showing 2 of 2 questions/)).toBeInTheDocument();
      });

      expect(screen.getByText(/Explain the difference between let, const, and var/)).toBeInTheDocument();
      expect(screen.getByText(/Describe a situation where you had to deal with a difficult stakeholder/)).toBeInTheDocument();
      expect(screen.queryByText(/Tell me about a time you faced a challenging project/)).not.toBeInTheDocument();
    });

    it('filters questions by search term', async () => {
      const user = userEvent.setup();

      render(
        <TestWrapper>
          <QuestionsPage />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/Showing 4 of 4 questions/)).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText('Search questions...');
      await user.type(searchInput, 'javascript');

      // Wait for debounce
      await waitFor(
        () => {
          expect(screen.getByText(/Showing 1 of 4 questions/)).toBeInTheDocument();
        },
        { timeout: 500 }
      );

      expect(screen.getByText(/Explain the difference between let, const, and var/)).toBeInTheDocument();
      expect(screen.queryByText(/Tell me about a time you faced a challenging project/)).not.toBeInTheDocument();
    });

    it('filters questions by company tag', async () => {
      const user = userEvent.setup();

      render(
        <TestWrapper>
          <QuestionsPage />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/Showing 4 of 4 questions/)).toBeInTheDocument();
      });

      // Wait for company select to appear
      await waitFor(() => {
        expect(screen.getByRole('combobox', { name: /company/i })).toBeInTheDocument();
      });

      const companySelect = screen.getByRole('combobox', { name: /company/i });
      await user.selectOptions(companySelect, 'Google');

      await waitFor(() => {
        expect(screen.getByText(/Showing 2 of 4 questions/)).toBeInTheDocument();
      });

      expect(screen.getByText(/Tell me about a time you faced a challenging project/)).toBeInTheDocument();
      expect(screen.getByText(/Design a URL shortening service/)).toBeInTheDocument();
      expect(screen.queryByText(/Explain the difference between let, const, and var/)).not.toBeInTheDocument();
    });

    it('combines multiple filters correctly', async () => {
      const user = userEvent.setup();

      render(
        <TestWrapper>
          <QuestionsPage />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/Showing 4 of 4 questions/)).toBeInTheDocument();
      });

      // Select behavioral category
      const categorySelect = screen.getByRole('combobox', { name: /category/i });
      await user.selectOptions(categorySelect, 'behavioral');

      // Select medium difficulty
      const difficultySelect = screen.getByRole('combobox', { name: /difficulty/i });
      await user.selectOptions(difficultySelect, 'medium');

      await waitFor(() => {
        expect(screen.getByText(/Showing 1 of 1 questions/)).toBeInTheDocument();
      });

      expect(screen.getByText(/Describe a situation where you had to deal with a difficult stakeholder/)).toBeInTheDocument();
      expect(screen.queryByText(/Tell me about a time you faced a challenging project/)).not.toBeInTheDocument();
    });

    it('clears all filters when Clear button is clicked', async () => {
      const user = userEvent.setup();

      render(
        <TestWrapper>
          <QuestionsPage />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/Showing 4 of 4 questions/)).toBeInTheDocument();
      });

      // Apply filters
      const categorySelect = screen.getByRole('combobox', { name: /category/i });
      await user.selectOptions(categorySelect, 'behavioral');

      await waitFor(() => {
        expect(screen.getByText(/Showing 2 of 2 questions/)).toBeInTheDocument();
      });

      // Clear filters
      const clearButton = screen.getByRole('button', { name: /clear/i });
      await user.click(clearButton);

      await waitFor(() => {
        expect(screen.getByText(/Showing 4 of 4 questions/)).toBeInTheDocument();
      });
    });

    it('displays active filters badge', async () => {
      const user = userEvent.setup();

      render(
        <TestWrapper>
          <QuestionsPage />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.queryByText('Active filters:')).not.toBeInTheDocument();
      });

      // Apply filter
      const categorySelect = screen.getByRole('combobox', { name: /category/i });
      await user.selectOptions(categorySelect, 'behavioral');

      await waitFor(() => {
        expect(screen.getByText('Active filters:')).toBeInTheDocument();
      });

      expect(screen.getByText('Behavioral')).toBeInTheDocument();
    });
  });

  describe('Empty State', () => {
    it('displays empty state when no questions match filters', async () => {
      const user = userEvent.setup();

      render(
        <TestWrapper>
          <QuestionsPage />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/Showing 4 of 4 questions/)).toBeInTheDocument();
      });

      // Search for something that doesn't exist
      const searchInput = screen.getByPlaceholderText('Search questions...');
      await user.type(searchInput, 'xyz123nonexistent');

      await waitFor(
        () => {
          expect(screen.getByText('No questions found')).toBeInTheDocument();
        },
        { timeout: 500 }
      );

      expect(
        screen.getByText('Try adjusting your filters or search terms.')
      ).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /clear filters/i })).toBeInTheDocument();
    });

    it('clears filters from empty state', async () => {
      const user = userEvent.setup();

      render(
        <TestWrapper>
          <QuestionsPage />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/Showing 4 of 4 questions/)).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText('Search questions...');
      await user.type(searchInput, 'xyz123nonexistent');

      await waitFor(
        () => {
          expect(screen.getByText('No questions found')).toBeInTheDocument();
        },
        { timeout: 500 }
      );

      const clearButton = screen.getByRole('button', { name: /clear filters/i });
      await user.click(clearButton);

      await waitFor(() => {
        expect(screen.getByText(/Showing 4 of 4 questions/)).toBeInTheDocument();
      });
    });

    it('displays empty state when API returns no questions', async () => {
      server.use(
        http.get(`${API_BASE_URL}/questions`, () => {
          return HttpResponse.json({ data: [] });
        })
      );

      render(
        <TestWrapper>
          <QuestionsPage />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('No questions found')).toBeInTheDocument();
      });
    });
  });

  describe('Error State', () => {
    it('displays error state when API fails', async () => {
      server.use(
        http.get(`${API_BASE_URL}/questions`, () => {
          return HttpResponse.json(
            { message: 'Internal server error' },
            { status: 500 }
          );
        })
      );

      render(
        <TestWrapper>
          <QuestionsPage />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Failed to load questions')).toBeInTheDocument();
      });

      expect(screen.getByText('Internal server error')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument();
    });

    it('reloads page when Try Again is clicked', async () => {
      const reloadSpy = vi.fn();
      Object.defineProperty(window, 'location', {
        value: { reload: reloadSpy },
        writable: true,
      });

      server.use(
        http.get(`${API_BASE_URL}/questions`, () => {
          return HttpResponse.json(
            { message: 'Internal server error' },
            { status: 500 }
          );
        })
      );

      const user = userEvent.setup();

      render(
        <TestWrapper>
          <QuestionsPage />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument();
      });

      const tryAgainButton = screen.getByRole('button', { name: /try again/i });
      await user.click(tryAgainButton);

      expect(reloadSpy).toHaveBeenCalled();
    });
  });

  describe('Practice Functionality', () => {
    it('navigates to practice session when Practice button is clicked', async () => {
      const user = userEvent.setup();

      render(
        <TestWrapper>
          <QuestionsPage />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getAllByText('Practice')).toHaveLength(4);
      });

      const practiceButtons = screen.getAllByText('Practice');
      await user.click(practiceButtons[0]);

      await waitFor(() => {
        expect(screen.getByText('Interview Page')).toBeInTheDocument();
      });
    });

    it('displays practice loading overlay during session creation', async () => {
      const user = userEvent.setup();

      // Delay the response to see loading state
      server.use(
        http.post(`${API_BASE_URL}/interviews/quick-practice`, async () => {
          await new Promise((resolve) => setTimeout(resolve, 100));
          return HttpResponse.json({
            data: {
              id: 'session1',
              interview_type: 'behavioral',
              status: 'in_progress',
              question_count: 1,
              created_at: '2024-01-01T00:00:00Z',
            },
          });
        })
      );

      render(
        <TestWrapper>
          <QuestionsPage />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getAllByText('Practice')).toHaveLength(4);
      });

      const practiceButtons = screen.getAllByText('Practice');
      await user.click(practiceButtons[0]);

      expect(screen.getByText('Creating practice session...')).toBeInTheDocument();
    });

    it('shows upgrade modal when practice limit reached (402 error)', async () => {
      const user = userEvent.setup();

      server.use(
        http.post(`${API_BASE_URL}/interviews/quick-practice`, () => {
          return HttpResponse.json(
            { message: 'Practice limit reached' },
            { status: 402 }
          );
        })
      );

      render(
        <TestWrapper>
          <QuestionsPage />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getAllByText('Practice')).toHaveLength(4);
      });

      const practiceButtons = screen.getAllByText('Practice');
      await user.click(practiceButtons[0]);

      await waitFor(() => {
        expect(screen.getByText(/upgrade/i)).toBeInTheDocument();
      });
    });
  });

  describe('Prepare Functionality', () => {
    it('navigates to preparation page when Prepare button is clicked', async () => {
      const user = userEvent.setup();

      render(
        <TestWrapper>
          <QuestionsPage />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getAllByText('Prepare')).toHaveLength(4);
      });

      const prepareButtons = screen.getAllByText('Prepare');
      await user.click(prepareButtons[0]);

      await waitFor(() => {
        expect(screen.getByText('Preparation Page')).toBeInTheDocument();
      });
    });

    it('shows remaining preparations for free tier users', async () => {
      render(
        <TestWrapper>
          <QuestionsPage />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getAllByText('3')).toHaveLength(4); // 4 prepare buttons with "3" badge
      });
    });

    it('does not show remaining preparations for pro users', async () => {
      server.use(
        http.get(`${API_BASE_URL}/users/me`, () => {
          return HttpResponse.json(mockProUser);
        })
      );

      render(
        <TestWrapper>
          <QuestionsPage />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getAllByText('Prepare')).toHaveLength(4);
      });

      // Pro users shouldn't see the "3" badge
      const prepareButtons = screen.getAllByText('Prepare');
      prepareButtons.forEach((button) => {
        const badge = button.querySelector('.rounded-full');
        expect(badge).not.toBeInTheDocument();
      });
    });

    it('shows upgrade modal when preparation limit reached for free tier', async () => {
      const user = userEvent.setup();

      // Set prepUsage to limit
      localStorage.setItem(
        'prepUsage',
        JSON.stringify({
          count: 3,
          resetDate: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
        })
      );

      render(
        <TestWrapper>
          <QuestionsPage />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getAllByText('Prepare')).toHaveLength(4);
      });

      const prepareButtons = screen.getAllByText('Prepare');
      await user.click(prepareButtons[0]);

      await waitFor(() => {
        expect(screen.getByText(/upgrade/i)).toBeInTheDocument();
      });
    });

    it('shows upgrade modal when preparation returns 402 error', async () => {
      const user = userEvent.setup();

      server.use(
        http.post(`${API_BASE_URL}/preparation/start`, () => {
          return HttpResponse.json(
            { message: 'Upgrade required' },
            { status: 402 }
          );
        })
      );

      render(
        <TestWrapper>
          <QuestionsPage />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getAllByText('Prepare')).toHaveLength(4);
      });

      const prepareButtons = screen.getAllByText('Prepare');
      await user.click(prepareButtons[0]);

      await waitFor(() => {
        expect(screen.getByText(/upgrade/i)).toBeInTheDocument();
      });
    });
  });

  describe('Accessibility', () => {
    it('has proper heading hierarchy', async () => {
      render(
        <TestWrapper>
          <QuestionsPage />
        </TestWrapper>
      );

      await waitFor(() => {
        const heading = screen.getByRole('heading', { name: /question bank/i });
        expect(heading).toBeInTheDocument();
        expect(heading.tagName).toBe('H1');
      });
    });

    it('has accessible form controls', async () => {
      render(
        <TestWrapper>
          <QuestionsPage />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByPlaceholderText('Search questions...')).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText('Search questions...');
      expect(searchInput).toHaveAttribute('type', 'text');

      const categorySelect = screen.getByRole('combobox', { name: /category/i });
      expect(categorySelect).toBeInTheDocument();

      const difficultySelect = screen.getByRole('combobox', { name: /difficulty/i });
      expect(difficultySelect).toBeInTheDocument();
    });

    it('has accessible buttons', async () => {
      render(
        <TestWrapper>
          <QuestionsPage />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getAllByRole('button', { name: /practice/i })).toHaveLength(4);
      });

      expect(screen.getAllByRole('button', { name: /prepare/i })).toHaveLength(4);
    });
  });
});
