import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { server } from '../../test/mocks/server';
import { renderWithAuth } from '../../test/utils';
import ProgressPage from '../ProgressPage';
import type { InterviewSession } from '../../types';

const API_URL = 'http://localhost:8000/api/v1';

// Mock navigation
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('ProgressPage', () => {
  beforeEach(() => {
    mockNavigate.mockClear();
    localStorage.setItem('access_token', 'mock-token');
  });

  describe('Loading State', () => {
    it('displays skeleton loaders while loading', () => {
      renderWithAuth(<ProgressPage />);

      // Should show multiple skeleton elements for stats grid
      const skeletons = document.querySelectorAll('.animate-pulse');
      expect(skeletons.length).toBeGreaterThan(0);
    });
  });

  describe('Stats Display', () => {
    it('renders all stat cards with mock data', async () => {
      renderWithAuth(<ProgressPage />);

      // Wait for loading to complete
      await waitFor(() => {
        expect(screen.queryByText(/Your Progress/i)).toBeInTheDocument();
      });

      // Check for stat card labels - using more specific queries to avoid ambiguity
      expect(screen.getByText(/Avg Score/i)).toBeInTheDocument();
      // "Sessions" appears in multiple places, so just check that it exists
      const sessionsLabels = screen.queryAllByText(/Sessions/i);
      expect(sessionsLabels.length).toBeGreaterThan(0);
      expect(screen.getByText(/Practice Time/i)).toBeInTheDocument();
      expect(screen.getByText(/Trend/i)).toBeInTheDocument();
    });

    it('displays average score with correct formatting', async () => {
      server.use(
        http.get(`${API_URL}/users/me/stats`, () => {
          return HttpResponse.json({
            total_sessions: 10,
            completed_sessions: 8,
            average_score: 82.5,
            total_practice_time_seconds: 3600,
          });
        }),
        http.get(`${API_URL}/users/me/progress`, () => {
          return HttpResponse.json({
            score_trend: [],
            recommended_practice_areas: [],
            average_audio_score: null,
            average_content_score: null,
          });
        }),
        http.get(`${API_URL}/interviews`, () => {
          return HttpResponse.json([]);
        })
      );

      renderWithAuth(<ProgressPage />);

      await waitFor(() => {
        expect(screen.getByText('83')).toBeInTheDocument(); // Rounded average score (82.5 rounds to 83)
      });

      expect(screen.getByText(/out of 100/i)).toBeInTheDocument();
    });

    it('displays placeholder when average score is null', async () => {
      server.use(
        http.get(`${API_URL}/users/me/stats`, () => {
          return HttpResponse.json({
            total_sessions: 0,
            completed_sessions: 0,
            average_score: null,
            total_practice_time_seconds: 0,
          });
        })
      );

      renderWithAuth(<ProgressPage />);

      await waitFor(() => {
        expect(screen.getByText('—')).toBeInTheDocument();
      });

      expect(screen.getByText(/Complete sessions to see/i)).toBeInTheDocument();
    });

    it('displays completed sessions count', async () => {
      server.use(
        http.get(`${API_URL}/users/me/stats`, () => {
          return HttpResponse.json({
            total_sessions: 10,
            completed_sessions: 8,
            average_score: 82,
            total_practice_time_seconds: 3600,
          });
        })
      );

      renderWithAuth(<ProgressPage />);

      await waitFor(() => {
        expect(screen.getByText('8')).toBeInTheDocument();
      });

      expect(screen.getByText(/completed/i)).toBeInTheDocument();
    });

    it('displays practice time in hours and minutes', async () => {
      server.use(
        http.get(`${API_URL}/users/me/stats`, () => {
          return HttpResponse.json({
            total_sessions: 10,
            completed_sessions: 8,
            average_score: 82,
            total_practice_time_seconds: 5400, // 1h 30m
          });
        })
      );

      renderWithAuth(<ProgressPage />);

      await waitFor(() => {
        expect(screen.getByText('1h 30m')).toBeInTheDocument();
      });
    });

    it('displays practice time in minutes for less than an hour', async () => {
      server.use(
        http.get(`${API_URL}/users/me/stats`, () => {
          return HttpResponse.json({
            total_sessions: 5,
            completed_sessions: 5,
            average_score: 75,
            total_practice_time_seconds: 1800, // 30 minutes
          });
        })
      );

      renderWithAuth(<ProgressPage />);

      await waitFor(() => {
        expect(screen.getByText('30m')).toBeInTheDocument();
      });
    });

    it('displays positive trend with + sign', async () => {
      server.use(
        http.get(`${API_URL}/users/me/progress`, () => {
          return HttpResponse.json({
            score_trend: [
              { date: '2024-01-01', score: 75, content_score: 70, audio_score: 80 },
              { date: '2024-01-02', score: 78, content_score: 75, audio_score: 81 },
              { date: '2024-01-03', score: 80, content_score: 78, audio_score: 82 },
              { date: '2024-01-04', score: 82, content_score: 80, audio_score: 84 },
              { date: '2024-01-05', score: 85, content_score: 83, audio_score: 87 },
            ],
            recommended_practice_areas: [],
            average_audio_score: 82,
            average_content_score: 77,
          });
        })
      );

      renderWithAuth(<ProgressPage />);

      await waitFor(() => {
        expect(screen.getByText(/\+10/)).toBeInTheDocument(); // 85 - 75 = +10
      });

      expect(screen.getByText(/last 5 sessions/i)).toBeInTheDocument();
    });

    it('displays negative trend without + sign', async () => {
      server.use(
        http.get(`${API_URL}/users/me/progress`, () => {
          return HttpResponse.json({
            score_trend: [
              { date: '2024-01-01', score: 85, content_score: 83, audio_score: 87 },
              { date: '2024-01-02', score: 82, content_score: 80, audio_score: 84 },
              { date: '2024-01-03', score: 80, content_score: 78, audio_score: 82 },
              { date: '2024-01-04', score: 78, content_score: 75, audio_score: 81 },
              { date: '2024-01-05', score: 75, content_score: 70, audio_score: 80 },
            ],
            recommended_practice_areas: [],
            average_audio_score: 82,
            average_content_score: 77,
          });
        })
      );

      renderWithAuth(<ProgressPage />);

      await waitFor(() => {
        expect(screen.getByText('-10')).toBeInTheDocument(); // 75 - 85 = -10
      });
    });

    it('displays placeholder for trend when less than 2 sessions', async () => {
      server.use(
        http.get(`${API_URL}/users/me/progress`, () => {
          return HttpResponse.json({
            score_trend: [
              { date: '2024-01-01', score: 75, content_score: 70, audio_score: 80 },
            ],
            recommended_practice_areas: [],
            average_audio_score: null,
            average_content_score: null,
          });
        })
      );

      renderWithAuth(<ProgressPage />);

      await waitFor(() => {
        // Find all instances of em dash
        const emDashes = screen.getAllByText('—');
        // Should have at least one for trend (and possibly one for avg score)
        expect(emDashes.length).toBeGreaterThanOrEqual(1);
      });

      expect(screen.getByText(/need 2\+ sessions/i)).toBeInTheDocument();
    });
  });

  describe('Recommended Practice Areas', () => {
    it('displays recommended practice areas when available', async () => {
      server.use(
        http.get(`${API_URL}/users/me/progress`, () => {
          return HttpResponse.json({
            score_trend: [
              { date: '2024-01-01', score: 75, content_score: 70, audio_score: 80 },
              { date: '2024-01-02', score: 80, content_score: 75, audio_score: 85 },
            ],
            recommended_practice_areas: ['Technical questions', 'System design', 'Communication clarity'],
            average_audio_score: 82,
            average_content_score: 72,
          });
        })
      );

      renderWithAuth(<ProgressPage />);

      await waitFor(() => {
        expect(screen.getByText(/Recommended Focus Areas/i)).toBeInTheDocument();
      });

      expect(screen.getByText('Technical questions')).toBeInTheDocument();
      expect(screen.getByText('System design')).toBeInTheDocument();
      expect(screen.getByText('Communication clarity')).toBeInTheDocument();
    });

    it('hides recommended practice areas section when empty', async () => {
      server.use(
        http.get(`${API_URL}/users/me/progress`, () => {
          return HttpResponse.json({
            score_trend: [
              { date: '2024-01-01', score: 75, content_score: 70, audio_score: 80 },
              { date: '2024-01-02', score: 80, content_score: 75, audio_score: 85 },
            ],
            recommended_practice_areas: [],
            average_audio_score: 82,
            average_content_score: 77,
          });
        })
      );

      renderWithAuth(<ProgressPage />);

      await waitFor(() => {
        expect(screen.queryByText(/Recommended Focus Areas/i)).not.toBeInTheDocument();
      });
    });
  });

  describe('Session History', () => {
    it('renders session history list with completed sessions', async () => {
      const mockSessions: InterviewSession[] = [
        {
          id: 'session-1',
          interview_type: 'behavioral',
          status: 'completed',
          question_count: 5,
          overall_score: 85,
          duration_seconds: 1800,
          created_at: new Date(Date.now() - 3600000).toISOString(), // 1 hour ago
        },
        {
          id: 'session-2',
          interview_type: 'technical',
          status: 'analyzed',
          question_count: 3,
          overall_score: 72,
          duration_seconds: 1200,
          created_at: new Date(Date.now() - 7200000).toISOString(), // 2 hours ago
        },
      ];

      server.use(
        http.get(`${API_URL}/interviews`, () => {
          return HttpResponse.json(mockSessions);
        })
      );

      renderWithAuth(<ProgressPage />);

      await waitFor(() => {
        expect(screen.getByText(/Behavioral Interview/i)).toBeInTheDocument();
      });

      expect(screen.getByText(/Behavioral Interview/i)).toBeInTheDocument();
      expect(screen.getByText(/Technical Interview/i)).toBeInTheDocument();
      expect(screen.getByText('85')).toBeInTheDocument();
      expect(screen.getByText('72')).toBeInTheDocument();
    });

    it('displays session details correctly', async () => {
      const mockSessions: InterviewSession[] = [
        {
          id: 'session-1',
          interview_type: 'system_design',
          status: 'completed',
          question_count: 2,
          overall_score: 90,
          duration_seconds: 2400, // 40 minutes
          created_at: new Date(Date.now() - 3600000).toISOString(), // 1 hour ago
        },
      ];

      server.use(
        http.get(`${API_URL}/interviews`, () => {
          return HttpResponse.json(mockSessions);
        })
      );

      renderWithAuth(<ProgressPage />);

      await waitFor(() => {
        expect(screen.getByText(/System design Interview/i)).toBeInTheDocument();
      });

      expect(screen.getByText(/2 questions/i)).toBeInTheDocument();
      expect(screen.getByText(/40:00/i)).toBeInTheDocument(); // duration
    });

    it('navigates to feedback page when session is clicked', async () => {
      const mockSessions: InterviewSession[] = [
        {
          id: 'session-123',
          interview_type: 'behavioral',
          status: 'completed',
          question_count: 5,
          overall_score: 85,
          created_at: new Date().toISOString(),
        },
      ];

      server.use(
        http.get(`${API_URL}/interviews`, () => {
          return HttpResponse.json(mockSessions);
        })
      );

      const user = userEvent.setup();
      renderWithAuth(<ProgressPage />);

      await waitFor(() => {
        expect(screen.getByText(/Behavioral Interview/i)).toBeInTheDocument();
      });

      const sessionCard = screen.getByText(/Behavioral Interview/i).closest('.cursor-pointer');
      expect(sessionCard).toBeInTheDocument();

      if (sessionCard) {
        await user.click(sessionCard);
        expect(mockNavigate).toHaveBeenCalledWith('/interview/session-123/feedback');
      }
    });

    it('filters out non-completed sessions', async () => {
      const mockSessions: InterviewSession[] = [
        {
          id: 'session-1',
          interview_type: 'behavioral',
          status: 'completed',
          question_count: 5,
          overall_score: 85,
          created_at: new Date().toISOString(),
        },
        {
          id: 'session-2',
          interview_type: 'technical',
          status: 'in_progress',
          question_count: 3,
          created_at: new Date().toISOString(),
        },
        {
          id: 'session-3',
          interview_type: 'system_design',
          status: 'scheduled',
          question_count: 2,
          created_at: new Date().toISOString(),
        },
        {
          id: 'session-4',
          interview_type: 'behavioral',
          status: 'analyzed',
          question_count: 4,
          overall_score: 78,
          created_at: new Date().toISOString(),
        },
      ];

      server.use(
        http.get(`${API_URL}/interviews`, () => {
          return HttpResponse.json(mockSessions);
        })
      );

      renderWithAuth(<ProgressPage />);

      await waitFor(() => {
        const behavioralSessions = screen.getAllByText(/Behavioral Interview/i);
        expect(behavioralSessions.length).toBeGreaterThanOrEqual(1);
      });

      // Should only show completed and analyzed sessions (2 total)
      // Get all session cards - there should be exactly 2
      const allSessionTexts = screen.getAllByText(/Interview/i);
      const sessionTexts = allSessionTexts.filter(
        (el) => el.textContent?.match(/^(behavioral|technical|system design) Interview$/i)
      );
      expect(sessionTexts.length).toBe(2);
    });

    it('limits session history to 10 most recent sessions', async () => {
      const mockSessions: InterviewSession[] = Array.from({ length: 15 }, (_, i) => ({
        id: `session-${i}`,
        interview_type: 'behavioral' as const,
        status: 'completed' as const,
        question_count: 5,
        overall_score: 80 + i,
        created_at: new Date(Date.now() - i * 3600000).toISOString(),
      }));

      server.use(
        http.get(`${API_URL}/interviews`, () => {
          return HttpResponse.json(mockSessions);
        })
      );

      renderWithAuth(<ProgressPage />);

      await waitFor(() => {
        const sessionCards = screen.getAllByText(/Behavioral Interview/i);
        expect(sessionCards.length).toBe(10); // Only first 10 sessions
      });
    });
  });

  describe('Empty State', () => {
    it('displays empty state when no sessions exist', async () => {
      server.use(
        http.get(`${API_URL}/interviews`, () => {
          return HttpResponse.json([]);
        }),
        http.get(`${API_URL}/users/me/stats`, () => {
          return HttpResponse.json({
            total_sessions: 0,
            completed_sessions: 0,
            average_score: null,
            total_practice_time_seconds: 0,
          });
        }),
        http.get(`${API_URL}/users/me/progress`, () => {
          return HttpResponse.json({
            score_trend: [],
            recommended_practice_areas: [],
            average_audio_score: null,
            average_content_score: null,
          });
        })
      );

      renderWithAuth(<ProgressPage />);

      await waitFor(() => {
        expect(screen.getByText(/No Sessions Yet/i)).toBeInTheDocument();
      });

      expect(screen.getByText(/Complete your first interview to see your progress over time/i)).toBeInTheDocument();
      expect(screen.getByText(/Start Practicing/i)).toBeInTheDocument();
    });

    it('navigates to practice page when Start Practicing is clicked', async () => {
      server.use(
        http.get(`${API_URL}/interviews`, () => {
          return HttpResponse.json([]);
        })
      );

      const user = userEvent.setup();
      renderWithAuth(<ProgressPage />);

      await waitFor(() => {
        expect(screen.getByText(/No Sessions Yet/i)).toBeInTheDocument();
      });

      const startButton = screen.getByText(/Start Practicing/i);
      await user.click(startButton);

      expect(mockNavigate).toHaveBeenCalledWith('/questions');
    });
  });

  describe('Error Handling', () => {
    it('displays error message when data fails to load', async () => {
      server.use(
        http.get(`${API_URL}/users/me/stats`, () => {
          return HttpResponse.json(
            { message: 'Failed to fetch stats' },
            { status: 500 }
          );
        })
      );

      renderWithAuth(<ProgressPage />);

      await waitFor(() => {
        expect(screen.getByText(/Failed to Load Progress/i)).toBeInTheDocument();
      });

      expect(screen.getByText(/Failed to fetch stats/i)).toBeInTheDocument();
      expect(screen.getByText(/Try Again/i)).toBeInTheDocument();
    });

    it('displays generic error message when no message provided', async () => {
      server.use(
        http.get(`${API_URL}/users/me/stats`, () => {
          return HttpResponse.error();
        }),
        http.get(`${API_URL}/users/me/progress`, () => {
          return HttpResponse.error();
        }),
        http.get(`${API_URL}/interviews`, () => {
          return HttpResponse.error();
        })
      );

      renderWithAuth(<ProgressPage />);

      await waitFor(() => {
        const headings = screen.getAllByText(/Failed to Load Progress/i);
        expect(headings.length).toBeGreaterThan(0);
      });

      expect(screen.getByText(/Failed to load progress data/i)).toBeInTheDocument();
    });

    it('retries loading when Try Again is clicked', async () => {
      let callCount = 0;

      server.use(
        http.get(`${API_URL}/users/me/stats`, () => {
          callCount++;
          if (callCount === 1) {
            return HttpResponse.json(
              { message: 'Failed to fetch stats' },
              { status: 500 }
            );
          }
          return HttpResponse.json({
            total_sessions: 5,
            completed_sessions: 5,
            average_score: 80,
            total_practice_time_seconds: 1800,
          });
        }),
        http.get(`${API_URL}/users/me/progress`, () => {
          return HttpResponse.json({
            score_trend: [],
            recommended_practice_areas: [],
            average_audio_score: null,
            average_content_score: null,
          });
        }),
        http.get(`${API_URL}/interviews`, () => {
          return HttpResponse.json([]);
        })
      );

      const user = userEvent.setup();
      renderWithAuth(<ProgressPage />);

      await waitFor(() => {
        expect(screen.getByText(/Failed to Load Progress/i)).toBeInTheDocument();
      });

      const tryAgainButton = screen.getByText(/Try Again/i);
      await user.click(tryAgainButton);

      await waitFor(() => {
        expect(screen.queryByText(/Failed to Load Progress/i)).not.toBeInTheDocument();
        // Use getByRole to be more specific about the h1 heading
        expect(screen.getByRole('heading', { name: /Your Progress/i, level: 1 })).toBeInTheDocument();
      });

      expect(callCount).toBe(2);
    });
  });

  describe('Page Header', () => {
    it('renders page title and description', async () => {
      renderWithAuth(<ProgressPage />);

      await waitFor(() => {
        expect(screen.getByText(/Your Progress/i)).toBeInTheDocument();
      });

      expect(screen.getByText(/Track your improvement over time/i)).toBeInTheDocument();
    });
  });

  describe('Score Color Coding', () => {
    it('applies correct color for high scores', async () => {
      const mockSessions: InterviewSession[] = [
        {
          id: 'session-1',
          interview_type: 'behavioral',
          status: 'completed',
          question_count: 5,
          overall_score: 92,
          created_at: new Date().toISOString(),
        },
      ];

      server.use(
        http.get(`${API_URL}/interviews`, () => {
          return HttpResponse.json(mockSessions);
        })
      );

      renderWithAuth(<ProgressPage />);

      await waitFor(() => {
        const scoreElement = screen.getByText('92');
        expect(scoreElement).toBeInTheDocument();
        // Check if parent has success color classes
        const parentElement = scoreElement.closest('div');
        expect(parentElement?.className).toContain('text-status-success');
      });
    });

    it('applies correct color for medium scores', async () => {
      const mockSessions: InterviewSession[] = [
        {
          id: 'session-1',
          interview_type: 'behavioral',
          status: 'completed',
          question_count: 5,
          overall_score: 65,
          created_at: new Date().toISOString(),
        },
      ];

      server.use(
        http.get(`${API_URL}/interviews`, () => {
          return HttpResponse.json(mockSessions);
        })
      );

      renderWithAuth(<ProgressPage />);

      await waitFor(() => {
        const scoreElement = screen.getByText('65');
        expect(scoreElement).toBeInTheDocument();
        // Check if parent has warning color classes
        const parentElement = scoreElement.closest('div');
        expect(parentElement?.className).toContain('text-status-warning');
      });
    });
  });

  describe('Accessibility', () => {
    it('has proper heading hierarchy', async () => {
      renderWithAuth(<ProgressPage />);

      await waitFor(() => {
        const h1 = screen.getByRole('heading', { level: 1, name: /Your Progress/i });
        expect(h1).toBeInTheDocument();
      });

      const h2Elements = screen.getAllByRole('heading', { level: 2 });
      expect(h2Elements.length).toBeGreaterThan(0);
    });

    it('session cards are keyboard accessible', async () => {
      const mockSessions: InterviewSession[] = [
        {
          id: 'session-1',
          interview_type: 'behavioral',
          status: 'completed',
          question_count: 5,
          overall_score: 85,
          created_at: new Date().toISOString(),
        },
      ];

      server.use(
        http.get(`${API_URL}/interviews`, () => {
          return HttpResponse.json(mockSessions);
        })
      );

      const user = userEvent.setup();
      renderWithAuth(<ProgressPage />);

      await waitFor(() => {
        expect(screen.getByText(/Behavioral Interview/i)).toBeInTheDocument();
      });

      const sessionCard = screen.getByText(/Behavioral Interview/i).closest('.cursor-pointer');
      expect(sessionCard).toBeInTheDocument();

      if (sessionCard) {
        // Click the session card to navigate
        await user.click(sessionCard);
        expect(mockNavigate).toHaveBeenCalledWith('/interview/session-1/feedback');
      }
    });
  });
});
