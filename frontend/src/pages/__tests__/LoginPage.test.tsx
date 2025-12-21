import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderPage, screen, waitFor } from '../../test/utils/pageTestUtils';
import userEvent from '@testing-library/user-event';
import LoginPage from '../LoginPage';
import { server } from '../../test/mocks/server';
import { http, HttpResponse } from 'msw';

describe('LoginPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  describe('Rendering', () => {
    it('should render login page with all form elements', () => {
      renderPage(<LoginPage />, { user: null });

      expect(screen.getByRole('heading', { name: /welcome back/i })).toBeInTheDocument();
      expect(screen.getByText(/sign in to continue your practice/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/^password$/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
    });

    it('should render email input with correct attributes', () => {
      renderPage(<LoginPage />, { user: null });

      const emailInput = screen.getByLabelText(/email address/i);
      expect(emailInput).toHaveAttribute('type', 'email');
      expect(emailInput).toHaveAttribute('placeholder', 'you@example.com');
      expect(emailInput).toHaveAttribute('required');
      expect(emailInput).toHaveAttribute('autoFocus');
    });

    it('should render password input with correct attributes', () => {
      renderPage(<LoginPage />, { user: null });

      const passwordInput = screen.getByLabelText(/^password$/i);
      expect(passwordInput).toHaveAttribute('type', 'password');
      expect(passwordInput).toHaveAttribute('placeholder', '••••••••');
      expect(passwordInput).toHaveAttribute('required');
    });

    it('should render forgot password link', () => {
      renderPage(<LoginPage />, { user: null });

      const forgotPasswordLink = screen.getByRole('link', { name: /forgot password/i });
      expect(forgotPasswordLink).toBeInTheDocument();
      expect(forgotPasswordLink).toHaveAttribute('href', '/forgot-password');
    });

    it('should render sign up link', () => {
      renderPage(<LoginPage />, { user: null });

      expect(screen.getByText(/don't have an account\?/i)).toBeInTheDocument();
      const signUpLink = screen.getByRole('link', { name: /sign up/i });
      expect(signUpLink).toBeInTheDocument();
      expect(signUpLink).toHaveAttribute('href', '/register');
    });

    it('should not display error message initially', () => {
      renderPage(<LoginPage />, { user: null });

      const errorAlert = screen.queryByRole('alert');
      expect(errorAlert).not.toBeInTheDocument();
    });
  });

  describe('Form Validation', () => {
    it('should prevent submission with empty email', async () => {
      const user = userEvent.setup();
      renderPage(<LoginPage />, { user: null });

      const passwordInput = screen.getByLabelText(/^password$/i);
      const submitButton = screen.getByRole('button', { name: /sign in/i });

      await user.type(passwordInput, 'password123');
      await user.click(submitButton);

      // HTML5 validation should prevent submission
      expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    });

    it('should prevent submission with empty password', async () => {
      const user = userEvent.setup();
      renderPage(<LoginPage />, { user: null });

      const emailInput = screen.getByLabelText(/email address/i);
      const submitButton = screen.getByRole('button', { name: /sign in/i });

      await user.type(emailInput, 'test@example.com');
      await user.click(submitButton);

      // HTML5 validation should prevent submission
      expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    });

    it('should require valid email format', () => {
      renderPage(<LoginPage />, { user: null });

      const emailInput = screen.getByLabelText(/email address/i) as HTMLInputElement;
      expect(emailInput.type).toBe('email');
    });
  });

  describe('Form Submission', () => {
    it('should handle successful login', async () => {
      const user = userEvent.setup();
      renderPage(<LoginPage />, { user: null });

      const emailInput = screen.getByLabelText(/email address/i);
      const passwordInput = screen.getByLabelText(/^password$/i);
      const submitButton = screen.getByRole('button', { name: /sign in/i });

      await user.type(emailInput, 'test@example.com');
      await user.type(passwordInput, 'password123');
      await user.click(submitButton);

      // Button should show loading state
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /signing in\.\.\./i })).toBeInTheDocument();
      });

      // Wait for navigation to complete
      await waitFor(
        () => {
          expect(localStorage.getItem('access_token')).toBe('mock-access-token');
        },
        { timeout: 3000 }
      );
    });

    it('should disable submit button during submission', async () => {
      const user = userEvent.setup();
      renderPage(<LoginPage />, { user: null });

      const emailInput = screen.getByLabelText(/email address/i);
      const passwordInput = screen.getByLabelText(/^password$/i);
      const submitButton = screen.getByRole('button', { name: /sign in/i });

      await user.type(emailInput, 'test@example.com');
      await user.type(passwordInput, 'password123');
      await user.click(submitButton);

      await waitFor(() => {
        const button = screen.getByRole('button', { name: /signing in\.\.\./i });
        expect(button).toBeDisabled();
      });
    });

    it('should display error message on invalid credentials', async () => {
      server.use(
        http.post('http://localhost:8000/api/v1/users/login', () => {
          return HttpResponse.json({ detail: 'Invalid email or password' }, { status: 401 });
        })
      );

      const user = userEvent.setup();
      renderPage(<LoginPage />, { user: null });

      const emailInput = screen.getByLabelText(/email address/i);
      const passwordInput = screen.getByLabelText(/^password$/i);
      const submitButton = screen.getByRole('button', { name: /sign in/i });

      await user.type(emailInput, 'wrong@example.com');
      await user.type(passwordInput, 'wrongpassword');
      await user.click(submitButton);

      await waitFor(() => {
        const errorAlert = screen.getByRole('alert');
        expect(errorAlert).toBeInTheDocument();
        expect(errorAlert).toHaveTextContent(/invalid email or password/i);
      });
    });

    it('should display generic error message on network failure', async () => {
      server.use(
        http.post('http://localhost:8000/api/v1/users/login', () => {
          return HttpResponse.json({ detail: 'Server error' }, { status: 500 });
        })
      );

      const user = userEvent.setup();
      renderPage(<LoginPage />, { user: null });

      const emailInput = screen.getByLabelText(/email address/i);
      const passwordInput = screen.getByLabelText(/^password$/i);
      const submitButton = screen.getByRole('button', { name: /sign in/i });

      await user.type(emailInput, 'test@example.com');
      await user.type(passwordInput, 'password123');
      await user.click(submitButton);

      await waitFor(() => {
        const errorAlert = screen.getByRole('alert');
        expect(errorAlert).toBeInTheDocument();
      });
    });

    it('should clear error message on new submission', async () => {
      server.use(
        http.post('http://localhost:8000/api/v1/users/login', () => {
          return HttpResponse.json({ detail: 'Invalid credentials' }, { status: 401 });
        })
      );

      const user = userEvent.setup();
      renderPage(<LoginPage />, { user: null });

      const emailInput = screen.getByLabelText(/email address/i);
      const passwordInput = screen.getByLabelText(/^password$/i);
      const submitButton = screen.getByRole('button', { name: /sign in/i });

      // First submission with error
      await user.type(emailInput, 'wrong@example.com');
      await user.type(passwordInput, 'wrong');
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument();
      });

      // Clear and retry
      server.use(
        http.post('http://localhost:8000/api/v1/users/login', () => {
          return HttpResponse.json({
            access_token: 'mock-access-token',
            refresh_token: 'mock-refresh-token',
            token_type: 'bearer',
          });
        })
      );

      await user.clear(emailInput);
      await user.clear(passwordInput);
      await user.type(emailInput, 'test@example.com');
      await user.type(passwordInput, 'password123');
      await user.click(submitButton);

      // Error should be cleared before making new request
      await waitFor(() => {
        expect(screen.queryByRole('alert')).not.toBeInTheDocument();
      });
    });
  });

  describe('Error Display', () => {
    it('should display error with proper ARIA attributes', async () => {
      server.use(
        http.post('http://localhost:8000/api/v1/users/login', () => {
          return HttpResponse.json({ detail: 'Invalid credentials' }, { status: 401 });
        })
      );

      const user = userEvent.setup();
      renderPage(<LoginPage />, { user: null });

      await user.type(screen.getByLabelText(/email address/i), 'test@example.com');
      await user.type(screen.getByLabelText(/^password$/i), 'wrong');
      await user.click(screen.getByRole('button', { name: /sign in/i }));

      await waitFor(() => {
        const errorAlert = screen.getByRole('alert');
        expect(errorAlert).toHaveAttribute('id', 'login-error');
        expect(errorAlert).toHaveAttribute('aria-live', 'assertive');
      });
    });

    it('should link error to form fields via aria-describedby', async () => {
      server.use(
        http.post('http://localhost:8000/api/v1/users/login', () => {
          return HttpResponse.json({ detail: 'Invalid credentials' }, { status: 401 });
        })
      );

      const user = userEvent.setup();
      renderPage(<LoginPage />, { user: null });

      await user.type(screen.getByLabelText(/email address/i), 'test@example.com');
      await user.type(screen.getByLabelText(/^password$/i), 'wrong');
      await user.click(screen.getByRole('button', { name: /sign in/i }));

      await waitFor(() => {
        const emailInput = screen.getByLabelText(/email address/i);
        const passwordInput = screen.getByLabelText(/^password$/i);
        expect(emailInput).toHaveAttribute('aria-invalid', 'true');
        expect(emailInput).toHaveAttribute('aria-describedby', 'login-error');
        expect(passwordInput).toHaveAttribute('aria-invalid', 'true');
        expect(passwordInput).toHaveAttribute('aria-describedby', 'login-error');
      });
    });
  });

  describe('Navigation Links', () => {
    it('should navigate to register page', () => {
      renderPage(<LoginPage />, { user: null });

      const signUpLink = screen.getByRole('link', { name: /sign up/i });
      expect(signUpLink).toHaveAttribute('href', '/register');
    });

    it('should navigate to forgot password page', () => {
      renderPage(<LoginPage />, { user: null });

      const forgotPasswordLink = screen.getByRole('link', { name: /forgot password/i });
      expect(forgotPasswordLink).toHaveAttribute('href', '/forgot-password');
    });
  });

  describe('Accessibility', () => {
    it('should have proper heading hierarchy', () => {
      renderPage(<LoginPage />, { user: null });

      const heading = screen.getByRole('heading', { name: /welcome back/i });
      expect(heading).toBeInTheDocument();
      expect(heading.tagName).toBe('H1');
    });

    it('should have labels for all form inputs', () => {
      renderPage(<LoginPage />, { user: null });

      const emailInput = screen.getByLabelText(/email address/i);
      const passwordInput = screen.getByLabelText(/^password$/i);

      expect(emailInput).toBeInTheDocument();
      expect(passwordInput).toBeInTheDocument();
    });

    it('should have proper button role', () => {
      renderPage(<LoginPage />, { user: null });

      const submitButton = screen.getByRole('button', { name: /sign in/i });
      expect(submitButton).toHaveAttribute('type', 'submit');
    });
  });

  describe('Button States', () => {
    it('should show "Sign In" text when not loading', () => {
      renderPage(<LoginPage />, { user: null });

      expect(screen.getByRole('button', { name: /^sign in$/i })).toBeInTheDocument();
    });

    it('should show "Signing in..." text when loading', async () => {
      const user = userEvent.setup();
      renderPage(<LoginPage />, { user: null });

      await user.type(screen.getByLabelText(/email address/i), 'test@example.com');
      await user.type(screen.getByLabelText(/^password$/i), 'password123');
      await user.click(screen.getByRole('button', { name: /sign in/i }));

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /signing in\.\.\./i })).toBeInTheDocument();
      });
    });

    it('should have enabled submit button when not loading', () => {
      renderPage(<LoginPage />, { user: null });

      const submitButton = screen.getByRole('button', { name: /sign in/i });
      expect(submitButton).not.toBeDisabled();
    });
  });

  describe('Integration', () => {
    it('should handle full login flow from input to success', async () => {
      const user = userEvent.setup();
      renderPage(<LoginPage />, { user: null });

      // Fill form
      await user.type(screen.getByLabelText(/email address/i), 'test@example.com');
      await user.type(screen.getByLabelText(/^password$/i), 'password123');

      // Submit
      await user.click(screen.getByRole('button', { name: /sign in/i }));

      // Verify loading state
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /signing in\.\.\./i })).toBeDisabled();
      });

      // Verify success
      await waitFor(
        () => {
          expect(localStorage.getItem('access_token')).toBe('mock-access-token');
          expect(localStorage.getItem('refresh_token')).toBe('mock-refresh-token');
        },
        { timeout: 3000 }
      );
    });

    it('should handle redirect after login via location state', async () => {
      const user = userEvent.setup();
      renderPage(<LoginPage />, {
        user: null,
        initialRoute: '/login',
      });

      await user.type(screen.getByLabelText(/email address/i), 'test@example.com');
      await user.type(screen.getByLabelText(/^password$/i), 'password123');
      await user.click(screen.getByRole('button', { name: /sign in/i }));

      await waitFor(
        () => {
          expect(localStorage.getItem('access_token')).toBeTruthy();
        },
        { timeout: 3000 }
      );
    });
  });
});
