import { render, act } from '@testing-library/react';
import { axe } from 'vitest-axe';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import FeedbackPage from '../pages/FeedbackPage';

// Mock hooks and API
vi.mock('../hooks/useAuth', () => ({
  useAuth: () => ({
    user: { full_name: 'Test User', experience_level: 'mid_level' },
  }),
}));

vi.mock('../hooks/useOnboarding', () => ({
  useOnboarding: () => ({
    shouldShowWelcome: false,
    markWelcomeSeen: vi.fn(),
  }),
}));

vi.mock('../lib/api', () => {
    const mockSession = {
        id: 'test-session-id',
        created_at: new Date().toISOString(),
        duration_seconds: 300,
        interview_type: 'behavioral',
        question_count: 2,
        status: 'completed',
    };
    
    const mockResponses = [
        {
            id: 'resp-1',
            question: { content: 'Tell me about yourself', sample_answer: 'Sample' },
            transcript: 'I am a software engineer.',
            audio_url: 'http://example.com/audio.wav',
        },
        {
            id: 'resp-2',
            question: { content: 'What is your weakness?', sample_answer: 'Sample' },
            transcript: 'I work too hard.',
            audio_url: 'http://example.com/audio2.wav',
        },
    ];

    const mockFeedback = {
        overall_score: 85,
        content_score: 90,
        audio_score: 80,
        top_strengths: ['Clear voice', 'Good structure'],
        top_improvements: ['More examples'],
        recommended_practice_areas: ['System Design'],
    };

    const mockContentFeedbacks = [
        { detailed_feedback: 'Good', overall_content_score: 90, improvements: ['None'] },
        { detailed_feedback: 'Okay', overall_content_score: 80, improvements: ['Be concise'] }
    ];

    const mockComparison = {
        improvement_percent: 10,
        sessions_compared: 5,
        average_score: 75
    };

    return {
        interviewsAPI: {
            get: vi.fn().mockResolvedValue({ data: mockSession }),
            getById: vi.fn().mockResolvedValue({ data: mockSession }),
            getResponses: vi.fn().mockResolvedValue({ data: mockResponses }),
            getBySessionId: vi.fn().mockResolvedValue({ data: mockResponses }),
            getFeedback: vi.fn().mockResolvedValue({ data: mockFeedback }),
            getAllBySessionId: vi.fn().mockResolvedValue({ data: mockContentFeedbacks }),
            getComparison: vi.fn().mockResolvedValue({ data: mockComparison }),
        },
        feedbackAPI: {
            getBySessionId: vi.fn().mockResolvedValue({ data: mockFeedback }),
            getAllBySessionId: vi.fn().mockResolvedValue({ data: mockContentFeedbacks }),
            getComparison: vi.fn().mockResolvedValue({ data: mockComparison }),
        },
        responsesAPI: {
            getBySessionId: vi.fn().mockResolvedValue({ data: mockResponses }),
        }
    };
});

// Mock child components to prevent import issues
vi.mock('../components/feedback/ScoreRing', () => ({ default: () => <div data-testid="score-ring">ScoreRing</div> }));
vi.mock('../components/feedback/MetricCard', () => ({ default: () => <div data-testid="metric-card">MetricCard</div> }));
vi.mock('../components/feedback/ResponseAccordion', () => ({ default: () => <div data-testid="response-accordion">ResponseAccordion</div> }));
vi.mock('../components/feedback/ProcessingStatus', () => ({ default: () => <div data-testid="processing-status">ProcessingStatus</div> }));

describe('FeedbackPage Accessibility', () => {
  it('should have no accessibility violations', async () => {
    let container;
    
    await act(async () => {
        const result = render(
            <MemoryRouter initialEntries={['/interview/test-session-id/feedback']}>
                <Routes>
                    <Route path="/interview/:id/feedback" element={<FeedbackPage />} />
                </Routes>
            </MemoryRouter>
        );
        container = result.container;
    });

    if (!container) throw new Error('Container not found');

    // Run axe check
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
