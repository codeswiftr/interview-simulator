import { describe, it, expect, beforeAll, afterAll, afterEach } from 'vitest';
import { http, HttpResponse } from 'msw';
import { server } from '../mocks/server';

// Start MSW server for these tests
beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('MSW Integration', () => {
  it('should mock API requests', async () => {
    // This test verifies that MSW is working
    const response = await fetch('http://localhost:8000/api/v1/users/me');
    const data = await response.json();

    expect(data).toEqual({
      id: 'mock-id',
      email: 'test@example.com',
      full_name: 'Test User',
      subscription_tier: 'free',
      interviews_this_month: 0,
      total_interviews: 0,
      created_at: expect.any(String),
    });
  });

  it('should allow overriding handlers', async () => {
    // Override the default handler for this specific test
    server.use(
      http.get('http://localhost:8000/api/v1/users/me', () => {
        return HttpResponse.json({
          id: 'custom-id',
          email: 'custom@example.com',
          full_name: 'Custom User',
          subscription_tier: 'premium',
          interviews_this_month: 5,
          total_interviews: 10,
          created_at: new Date().toISOString(),
        });
      })
    );

    const response = await fetch('http://localhost:8000/api/v1/users/me');
    const data = await response.json();

    expect(data.email).toBe('custom@example.com');
    expect(data.subscription_tier).toBe('premium');
  });

  it('should handle POST requests', async () => {
    const response = await fetch('http://localhost:8000/api/v1/users/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: 'test@example.com', password: 'password' }),
    });
    const data = await response.json();

    expect(data).toEqual({
      access_token: 'mock-token',
      token_type: 'bearer',
    });
  });
});
