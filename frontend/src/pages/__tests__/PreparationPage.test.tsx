import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderPage, waitFor, screen } from '../../test/utils/pageTestUtils';
import PreparationPage from '../PreparationPage';
import { server } from '../../test/mocks/server';
import { http, HttpResponse } from 'msw';
import type { VoiceInputButtonProps } from '../../components/common/VoiceInputButton';

// Mock VoiceInputButton to avoid speech recognition API in tests
vi.mock('../../components/common/VoiceInputButton', () => ({
  VoiceInputButton: ({ onTranscript, disabled }: VoiceInputButtonProps) => (
    <button
      onClick={() => onTranscript && onTranscript('Mocked transcript')}
      disabled={disabled}
      data-testid="voice-input-button"
    >
      🎤
    </button>
  ),
}));

describe('PreparationPage', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  describe('Detective Stage', () => {
    it('should display detective question when stage is active', async () => {
      renderPage(<PreparationPage />, { initialRoute: '/preparation/test-id' });

      await waitFor(() => {
        // Detective question should be displayed
        expect(screen.getByText(/can you tell me|specific project/i)).toBeInTheDocument();
      });
    });

    it('should allow submitting answers to detective questions', async () => {
      renderPage(<PreparationPage />, { initialRoute: '/preparation/test-id' });

      await waitFor(() => {
        // Answer input and submit button should be available
        const submitButtons = screen.queryAllByRole('button', { name: /submit|answer/i });
        expect(submitButtons.length).toBeGreaterThan(0);
      });
    });
  });

  describe('Draft Stage', () => {
    it('should display generated draft', async () => {
      server.use(
        http.get('http://localhost:8000/api/v1/preparation/:id/draft', () => {
          return HttpResponse.json({
            draft_answer: '**Situation**: I worked on a project...\n**Task**: My responsibility...',
            stage: 'draft',
          });
        })
      );

      renderPage(<PreparationPage />, { initialRoute: '/preparation/test-id' });

      await waitFor(() => {
        // Draft should be displayed
        expect(screen.getByText(/situation|task|action|result/i)).toBeInTheDocument();
      });
    });

    it('should allow editing draft', async () => {
      server.use(
        http.get('http://localhost:8000/api/v1/preparation/:id/draft', () => {
          return HttpResponse.json({
            draft_answer: 'Original draft...',
            stage: 'draft',
          });
        })
      );

      renderPage(<PreparationPage />, { initialRoute: '/preparation/test-id' });

      await waitFor(() => {
        // Edit button should be available
        const editButtons = screen.queryAllByRole('button', { name: /edit/i });
        expect(editButtons.length).toBeGreaterThan(0);
      });
    });
  });

  describe('Practice Stage', () => {
    it('should display practice recording interface', async () => {
      server.use(
        http.get('http://localhost:8000/api/v1/preparation/:id/draft', () => {
          return HttpResponse.json({
            draft_answer: 'Practice draft...',
            stage: 'practice',
          });
        })
      );

      renderPage(<PreparationPage />, { initialRoute: '/preparation/test-id' });

      await waitFor(() => {
        // Recording deck should be visible in practice stage
        const recordingElements = screen.queryAllByText(/practice|record|recording/i);
        expect(recordingElements.length).toBeGreaterThan(0);
      });
    });

    it('should display attempt history', async () => {
      server.use(
        http.get('http://localhost:8000/api/v1/preparation/:id/attempts', () => {
          return HttpResponse.json({
            attempts: [
              {
                id: 'attempt-1',
                preparation_id: 'prep-test-id',
                audio_url: 'https://example.com/audio.mp3',
                transcript: 'Practice attempt transcript',
                delivery_score: 85,
                comparison_feedback: 'Good delivery',
                created_at: new Date().toISOString(),
              },
            ],
          });
        })
      );

      renderPage(<PreparationPage />, { initialRoute: '/preparation/test-id' });

      await waitFor(() => {
        // Attempt history should be displayed
        const attemptElements = screen.queryAllByText(/attempt|history|score/i);
        expect(attemptElements.length).toBeGreaterThan(0);
      });
    });
  });

  describe('Rating and Comparison', () => {
    it('should allow rating delivery attempts', async () => {
      server.use(
        http.get('http://localhost:8000/api/v1/preparation/:id/attempts', () => {
          return HttpResponse.json({
            attempts: [
              {
                id: 'attempt-1',
                preparation_id: 'prep-test-id',
                transcript: 'Practice transcript',
                delivery_score: null,
                created_at: new Date().toISOString(),
              },
            ],
          });
        })
      );

      renderPage(<PreparationPage />, { initialRoute: '/preparation/test-id' });

      await waitFor(() => {
        // Rate delivery button should be available
        const rateButtons = screen.queryAllByRole('button', { name: /rate|delivery/i });
        expect(rateButtons.length).toBeGreaterThan(0);
      });
    });

    it('should display comparison view when attempt is rated', async () => {
      server.use(
        http.get('http://localhost:8000/api/v1/preparation/:id/comparison', () => {
          return HttpResponse.json({
            draft: 'Original draft...',
            delivery: 'Actual delivery transcript...',
            delivery_score: 85,
            comparison_feedback: 'Good coverage of main points.',
            strengths: ['Clear communication'],
            improvements: ['Add more metrics'],
          });
        })
      );

      renderPage(<PreparationPage />, { initialRoute: '/preparation/test-id' });

      await waitFor(() => {
        // Comparison view elements should be available
        const comparisonElements = screen.queryAllByText(/comparison|strength|improvement/i);
        expect(comparisonElements.length).toBeGreaterThan(0);
      });
    });
  });

  describe('Error Handling', () => {
    it('should display error when preparation not found', async () => {
      server.use(
        http.get('http://localhost:8000/api/v1/preparation/:id/draft', () => {
          return HttpResponse.json({ message: 'Not found' }, { status: 404 });
        })
      );

      renderPage(<PreparationPage />, { initialRoute: '/preparation/invalid-id' });

      await waitFor(() => {
        expect(screen.getByText(/error|not found|failed/i)).toBeInTheDocument();
      });
    });
  });
});
