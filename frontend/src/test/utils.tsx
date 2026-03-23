/* eslint-disable react-refresh/only-export-components */
import type { ReactElement, ReactNode } from 'react';
import { render, type RenderOptions } from '@testing-library/react';
import { BrowserRouter, MemoryRouter } from 'react-router-dom';
import { AuthProvider } from '../hooks/useAuth';
import { ToastProvider } from '../hooks/useToast';
import type { User, ExperienceLevel } from '../types';

interface AllProvidersProps {
  children: ReactNode;
}

interface TestProvidersOptions {
  withAuth?: boolean;
  withToast?: boolean;
  initialRoute?: string;
}

// Mock user factory
export const createMockUser = (overrides?: Partial<User>): User => ({
  id: 'test-user-id',
  email: 'test@example.com',
  full_name: 'Test User',
  experience_level: 'mid' as ExperienceLevel,
  subscription_tier: 'free',
  interviews_this_month: 0,
  total_interviews: 0,
  created_at: new Date().toISOString(),
  ...overrides,
});

// Simple wrapper without AuthProvider to avoid navigation issues in tests
function AllProviders({ children }: AllProvidersProps) {
  return (
    <BrowserRouter>
      {children}
    </BrowserRouter>
  );
}

// Wrapper with all providers for testing hooks
function AllProvidersWithAuth({ children }: AllProvidersProps) {
  return (
    <MemoryRouter>
      <AuthProvider>
        <ToastProvider>
          {children}
        </ToastProvider>
      </AuthProvider>
    </MemoryRouter>
  );
}

// Wrapper with just ToastProvider
function ToastOnlyProvider({ children }: AllProvidersProps) {
  return (
    <BrowserRouter>
      <ToastProvider>
        {children}
      </ToastProvider>
    </BrowserRouter>
  );
}

// Default render function
const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => render(ui, { wrapper: AllProviders, ...options });

// Render with AuthProvider and ToastProvider
export const renderWithAuth = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => render(ui, { wrapper: AllProvidersWithAuth, ...options });

// Render with just ToastProvider
export const renderWithToast = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => render(ui, { wrapper: ToastOnlyProvider, ...options });

// Custom wrapper builder for flexible testing
export const createWrapper = (options: TestProvidersOptions = {}) => {
  const { withAuth = false, withToast = false, initialRoute = '/' } = options;

  return ({ children }: { children: ReactNode }) => {
    let content = children;

    if (withToast) {
      content = <ToastProvider>{content}</ToastProvider>;
    }

    if (withAuth) {
      content = <AuthProvider>{content}</AuthProvider>;
    }

    return (
      <MemoryRouter initialEntries={[initialRoute]}>
        {content}
      </MemoryRouter>
    );
  };
};

export * from '@testing-library/react';
export { customRender as render };
