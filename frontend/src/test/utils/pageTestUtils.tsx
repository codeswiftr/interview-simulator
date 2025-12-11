/* eslint-disable react-refresh/only-export-components */
/**
 * Test utilities for page component testing.
 * Provides helpers for rendering pages with proper context and mocking.
 */

import type { ReactElement, ReactNode } from 'react';
import { render, type RenderOptions, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AuthProvider } from '../../hooks/useAuth';
import { ToastProvider } from '../../hooks/useToast';
import { ThemeProvider } from '../../contexts/ThemeContext';
import type { User } from '../../types';
import { createMockUser } from '../utils';

interface PageTestProvidersProps {
  children: ReactNode;
  initialRoute?: string;
  user?: User | null;
}

/**
 * Providers wrapper for page component tests.
 * Includes Router, Auth, and Toast context.
 */
function PageTestProviders({ children, initialRoute = '/', user }: PageTestProvidersProps) {
  // Mock user in localStorage if provided
  if (user) {
    localStorage.setItem('access_token', 'mock-token');
    localStorage.setItem('refresh_token', 'mock-refresh-token');
  }

  return (
    <MemoryRouter initialEntries={[initialRoute]}>
      <ThemeProvider>
        <AuthProvider>
          <ToastProvider>
            {children}
          </ToastProvider>
        </AuthProvider>
      </ThemeProvider>
    </MemoryRouter>
  );
}

/**
 * Render a page component with all required providers.
 */
export const renderPage = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'> & {
    initialRoute?: string;
    user?: User | null;
  }
) => {
  const { initialRoute = '/', user = createMockUser(), ...renderOptions } = options || {};

  const Wrapper = ({ children }: { children: ReactNode }) => (
    <PageTestProviders initialRoute={initialRoute} user={user}>
      {children}
    </PageTestProviders>
  );

  return render(ui, { wrapper: Wrapper, ...renderOptions });
};

/**
 * Wait for page data to load (interviews, stats, etc.)
 */
export const waitForPageData = async (timeout = 5000) => {
  await waitFor(
    () => {
      // Wait for loading states to resolve
      const loadingElements = document.querySelectorAll('[data-testid*="loading"]');
      if (loadingElements.length === 0) {
        return true;
      }
      throw new Error('Page still loading');
    },
    { timeout }
  );
};

/**
 * Mock user factory with common overrides for page tests
 */
export const createPageTestUser = (overrides?: Partial<User>): User => ({
  ...createMockUser(),
  subscription_tier: 'pro',
  interviews_this_month: 5,
  total_interviews: 10,
  ...overrides,
});

/**
 * Common test data factories for pages
 */
export const createMockInterviewSession = (overrides?: Partial<any>) => ({
  id: 'test-interview-id',
  interview_type: 'behavioral',
  status: 'scheduled',
  question_count: 5,
  created_at: new Date().toISOString(),
  ...overrides,
});

export const createMockUserStats = (overrides?: Partial<any>) => ({
  total_sessions: 10,
  completed_sessions: 8,
  average_score: 82,
  total_practice_time_seconds: 3600,
  ...overrides,
});

export * from '@testing-library/react';
