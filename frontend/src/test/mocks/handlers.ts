import { http, HttpResponse } from 'msw';

const API_URL = 'http://localhost:8000/api/v1';

export const handlers = [
  // Auth handlers
  http.post(`${API_URL}/users/login`, () => {
    return HttpResponse.json({
      access_token: 'mock-token',
      token_type: 'bearer',
    });
  }),

  http.post(`${API_URL}/users/register`, () => {
    return HttpResponse.json({
      id: 'mock-id',
      email: 'test@example.com',
      full_name: 'Test User',
      subscription_tier: 'free',
      interviews_this_month: 0,
      total_interviews: 0,
      created_at: new Date().toISOString(),
    });
  }),

  http.get(`${API_URL}/users/me`, () => {
    return HttpResponse.json({
      id: 'mock-id',
      email: 'test@example.com',
      full_name: 'Test User',
      subscription_tier: 'free',
      interviews_this_month: 0,
      total_interviews: 0,
      created_at: new Date().toISOString(),
    });
  }),

  // Interview handlers
  http.get(`${API_URL}/interviews`, () => {
    return HttpResponse.json([
      {
        id: 'mock-interview-1',
        job_title: 'Software Engineer',
        company_name: 'Tech Corp',
        status: 'completed',
        created_at: new Date().toISOString(),
      },
    ]);
  }),

  http.post(`${API_URL}/interviews`, () => {
    return HttpResponse.json({
      id: 'new-interview-id',
      job_title: 'Product Manager',
      company_name: 'Startup Inc',
      status: 'pending',
      created_at: new Date().toISOString(),
    });
  }),
];
