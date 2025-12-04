import { http, HttpResponse } from 'msw';
import type { User, InterviewSession, Question, InterviewResponse, Feedback } from '../../types';

const API_URL = 'http://localhost:8000/api/v1';

// Mock data factories
export const mockUser: User = {
  id: 'mock-user-id',
  email: 'test@example.com',
  full_name: 'Test User',
  experience_level: 'mid',
  subscription_tier: 'free',
  interviews_this_month: 0,
  total_interviews: 0,
  created_at: new Date().toISOString(),
};

export const mockInterview: InterviewSession = {
  id: 'mock-interview-id',
  interview_type: 'behavioral',
  company_style: 'Tech Corp',
  status: 'scheduled',
  question_count: 5,
  created_at: new Date().toISOString(),
};

export const mockQuestion: Question = {
  id: 'mock-question-id',
  category: 'behavioral',
  difficulty: 'medium',
  content: 'Tell me about a time when you faced a challenging situation at work.',
  expected_duration_seconds: 120,
  is_active: true,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
};

export const mockResponse: InterviewResponse = {
  id: 'mock-response-id',
  session_id: 'mock-interview-id',
  question_id: 'mock-question-id',
  audio_url: 'https://example.com/audio.mp3',
  transcript: 'This is a sample transcript.',
  duration_seconds: 90,
  word_count: 150,
  filler_word_count: 5,
  processing_status: 'completed',
  submitted_at: new Date().toISOString(),
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
};

export const mockFeedback: Feedback = {
  id: 'mock-feedback-id',
  response_id: 'mock-response-id',
  overall_score: 85,
  content_score: 80,
  delivery_score: 90,
  structure_score: 85,
  communication_clarity_score: 88,
  strengths: ['Clear communication', 'Good structure'],
  weaknesses: ['Could be more specific'],
  improvement_suggestions: ['Add more concrete examples'],
  detailed_analysis: 'Overall good response with room for improvement.',
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
};

export const handlers = [
  // Auth handlers
  http.post(`${API_URL}/users/login`, () => {
    return HttpResponse.json({
      access_token: 'mock-access-token',
      refresh_token: 'mock-refresh-token',
      token_type: 'bearer',
    });
  }),

  http.post(`${API_URL}/users/register`, () => {
    return HttpResponse.json(mockUser);
  }),

  http.post(`${API_URL}/users/logout`, () => {
    return HttpResponse.json({ message: 'Logged out successfully' });
  }),

  http.post(`${API_URL}/auth/refresh`, () => {
    return HttpResponse.json({
      access_token: 'new-mock-access-token',
      refresh_token: 'new-mock-refresh-token',
      token_type: 'bearer',
    });
  }),

  http.get(`${API_URL}/users/me`, () => {
    return HttpResponse.json(mockUser);
  }),

  http.post(`${API_URL}/auth/forgot-password`, () => {
    return HttpResponse.json({ message: 'Password reset email sent' });
  }),

  http.post(`${API_URL}/auth/reset-password`, () => {
    return HttpResponse.json({ message: 'Password reset successfully' });
  }),

  // User handlers
  http.patch(`${API_URL}/users/me`, () => {
    return HttpResponse.json(mockUser);
  }),

  http.post(`${API_URL}/users/me/change-password`, () => {
    return HttpResponse.json({ message: 'Password changed successfully' });
  }),

  http.delete(`${API_URL}/users/me`, () => {
    return HttpResponse.json({ message: 'Account deleted successfully' });
  }),

  http.get(`${API_URL}/users/me/stats`, () => {
    return HttpResponse.json({
      total_sessions: 10,
      completed_sessions: 8,
      average_score: 82,
      total_practice_time_seconds: 3600,
    });
  }),

  http.get(`${API_URL}/users/me/progress`, () => {
    return HttpResponse.json({
      score_trend: [
        { date: '2024-01-01', score: 75 },
        { date: '2024-01-02', score: 80 },
      ],
    });
  }),

  http.get(`${API_URL}/users/me/readiness-score`, () => {
    return HttpResponse.json({ score: 85 });
  }),

  // Interview handlers
  http.get(`${API_URL}/interviews`, () => {
    return HttpResponse.json([mockInterview]);
  }),

  http.get(`${API_URL}/interviews/:id`, () => {
    return HttpResponse.json(mockInterview);
  }),

  http.post(`${API_URL}/interviews`, () => {
    return HttpResponse.json(mockInterview);
  }),

  http.post(`${API_URL}/interviews/quick-practice`, () => {
    return HttpResponse.json(mockInterview);
  }),

  http.post(`${API_URL}/interviews/:id/start`, () => {
    return HttpResponse.json({ ...mockInterview, status: 'in_progress' });
  }),

  http.post(`${API_URL}/interviews/:id/end`, () => {
    return HttpResponse.json({ ...mockInterview, status: 'completed' });
  }),

  http.delete(`${API_URL}/interviews/:id`, () => {
    return HttpResponse.json({ message: 'Interview deleted successfully' });
  }),

  http.get(`${API_URL}/interviews/:id/questions`, () => {
    return HttpResponse.json([mockQuestion]);
  }),

  http.get(`${API_URL}/interviews/:id/responses`, () => {
    return HttpResponse.json([mockResponse]);
  }),

  // Questions handlers
  http.get(`${API_URL}/questions`, () => {
    return HttpResponse.json([mockQuestion]);
  }),

  http.get(`${API_URL}/questions/:id`, () => {
    return HttpResponse.json(mockQuestion);
  }),

  http.get(`${API_URL}/questions/random`, () => {
    return HttpResponse.json(mockQuestion);
  }),

  // Responses handlers
  http.post(`${API_URL}/interviews/:sessionId/responses`, () => {
    return HttpResponse.json(mockResponse);
  }),

  http.get(`${API_URL}/responses/:id`, () => {
    return HttpResponse.json(mockResponse);
  }),

  // Feedback handlers
  http.get(`${API_URL}/feedback/response/:responseId`, () => {
    return HttpResponse.json(mockFeedback);
  }),

  http.get(`${API_URL}/feedback/session/:sessionId`, () => {
    return HttpResponse.json({
      overall_score: 85,
      audio_score: 80,
      content_score: 88,
      top_strengths: ['Clear communication', 'Good structure'],
      top_improvements: ['Add more examples', 'Reduce filler words'],
      recommended_practice_areas: ['Technical questions', 'System design'],
    });
  }),

  http.get(`${API_URL}/feedback/session/:sessionId/all`, () => {
    return HttpResponse.json([mockFeedback]);
  }),

  http.get(`${API_URL}/feedback/session/:sessionId/status`, () => {
    return HttpResponse.json({
      total_responses: 5,
      analyzed_responses: 3,
      pending_responses: 2,
      is_complete: false,
    });
  }),

  http.get(`${API_URL}/feedback/session/:sessionId/comparison`, () => {
    return HttpResponse.json({
      session_score: 85,
      average_score: 80,
      improvement_percent: 6.25,
      sessions_compared: 10,
    });
  }),

  http.post(`${API_URL}/feedback/generate/session/:sessionId`, () => {
    return HttpResponse.json({ message: 'Feedback generation started' });
  }),

  http.post(`${API_URL}/feedback/generate/response/:responseId`, () => {
    return HttpResponse.json(mockFeedback);
  }),

  // Upload handlers
  http.post(`${API_URL}/upload/audio`, () => {
    return HttpResponse.json({
      url: 'https://example.com/uploaded-audio.mp3',
      duration_seconds: 120,
    });
  }),

  // Subscriptions handlers
  http.get(`${API_URL}/subscriptions/status`, () => {
    return HttpResponse.json({
      tier: 'free',
      status: 'active',
      expires_at: null,
      interviews_this_month: 0,
      interviews_limit: 3,
      can_create_interview: true,
    });
  }),

  http.get(`${API_URL}/subscriptions/pricing`, () => {
    return HttpResponse.json({
      pro_monthly_price_id: 'price_monthly',
      pro_annual_price_id: 'price_annual',
    });
  }),

  http.post(`${API_URL}/subscriptions/checkout`, () => {
    return HttpResponse.json({
      url: 'https://checkout.stripe.com/session/test',
    });
  }),

  http.post(`${API_URL}/subscriptions/portal`, () => {
    return HttpResponse.json({
      url: 'https://billing.stripe.com/portal/test',
    });
  }),

  http.post(`${API_URL}/subscriptions/cancel`, () => {
    return HttpResponse.json({ message: 'Subscription cancelled successfully' });
  }),
];
