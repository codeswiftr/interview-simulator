import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderPage, screen, waitFor } from '../../test/utils/pageTestUtils';
import userEvent from '@testing-library/user-event';
import RegisterPage from '../RegisterPage';
import { server } from '../../test/mocks/server';
import { http, HttpResponse } from 'msw';

describe('RegisterPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    sessionStorage.clear();
  });

  describe('Rendering', () => {
    it('should render register page with all form elements', () => {
      renderPage(<RegisterPage />, { user: null });

      expect(screen.getByRole('heading', { name: /create your account/i })).toBeInTheDocument();
      expect(screen.getByText(/start practicing for your dream job/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/full name/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/^password$/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/experience level/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /create account/i })).toBeInTheDocument();
    });

    it('should render full name input with correct attributes', () => {
      renderPage(<RegisterPage />, { user: null });

      const nameInput = screen.getByLabelText(/full name/i);
      expect(nameInput).toHaveAttribute('type', 'text');
      expect(nameInput).toHaveAttribute('placeholder', 'John Doe');
      expect(nameInput).toHaveAttribute('required');
      expect(nameInput).toHaveAttribute('autoFocus');
    });

    it('should render email input with correct attributes', () => {
      renderPage(<RegisterPage />, { user: null });

      const emailInput = screen.getByLabelText(/email address/i);
      expect(emailInput).toHaveAttribute('type', 'email');
      expect(emailInput).toHaveAttribute('placeholder', 'you@example.com');
      expect(emailInput).toHaveAttribute('required');
    });

    it('should render password inputs with correct attributes', () => {
      renderPage(<RegisterPage />, { user: null });

      const passwordInput = screen.getByLabelText(/^password$/i);
      const confirmPasswordInput = screen.getByLabelText(/confirm password/i);

      expect(passwordInput).toHaveAttribute('type', 'password');
      expect(passwordInput).toHaveAttribute('placeholder', '••••••••');
      expect(passwordInput).toHaveAttribute('required');

      expect(confirmPasswordInput).toHaveAttribute('type', 'password');
      expect(confirmPasswordInput).toHaveAttribute('placeholder', '••••••••');
      expect(confirmPasswordInput).toHaveAttribute('required');
    });

    it('should render experience level dropdown with all options', () => {
      renderPage(<RegisterPage />, { user: null });

      const experienceSelect = screen.getByLabelText(/experience level/i) as HTMLSelectElement;
      expect(experienceSelect).toBeInTheDocument();

      const options = Array.from(experienceSelect.options).map((opt) => opt.value);
      expect(options).toEqual(['junior', 'mid', 'senior']);
    });

    it('should have "mid" as default experience level', () => {
      renderPage(<RegisterPage />, { user: null });

      const experienceSelect = screen.getByLabelText(/experience level/i) as HTMLSelectElement;
      expect(experienceSelect.value).toBe('mid');
    });

    it('should render sign in link', () => {
      renderPage(<RegisterPage />, { user: null });

      expect(screen.getByText(/already have an account\?/i)).toBeInTheDocument();
      const signInLink = screen.getByRole('link', { name: /sign in/i });
      expect(signInLink).toBeInTheDocument();
      expect(signInLink).toHaveAttribute('href', '/login');
    });

    it('should render experience level hint text', () => {
      renderPage(<RegisterPage />, { user: null });

      expect(
        screen.getByText(/this helps us tailor feedback to your experience level/i)
      ).toBeInTheDocument();
    });

    it('should not display error message initially', () => {
      renderPage(<RegisterPage />, { user: null });

      const errorAlert = screen.queryByRole('alert');
      expect(errorAlert).not.toBeInTheDocument();
    });

    it('should render password strength indicator', async () => {
      const user = userEvent.setup();
      renderPage(<RegisterPage />, { user: null });

      const passwordInput = screen.getByLabelText(/^password$/i);
      await user.type(passwordInput, 'Test123!');

      await waitFor(() => {
        expect(screen.getByText(/password strength:/i)).toBeInTheDocument();
      });
    });
  });

  describe('Form Validation', () => {
    it('should validate password mismatch', async () => {
      const user = userEvent.setup();
      renderPage(<RegisterPage />, { user: null });

      await user.type(screen.getByLabelText(/full name/i), 'John Doe');
      await user.type(screen.getByLabelText(/email address/i), 'john@example.com');
      await user.type(screen.getByLabelText(/^password$/i), 'Password123!');
      await user.type(screen.getByLabelText(/confirm password/i), 'DifferentPassword123!');
      await user.click(screen.getByRole('button', { name: /create account/i }));

      await waitFor(() => {
        const errorAlert = screen.getByRole('alert');
        expect(errorAlert).toHaveTextContent(/passwords do not match/i);
      });
    });

    it('should validate minimum password length', async () => {
      const user = userEvent.setup();
      renderPage(<RegisterPage />, { user: null });

      await user.type(screen.getByLabelText(/full name/i), 'John Doe');
      await user.type(screen.getByLabelText(/email address/i), 'john@example.com');
      await user.type(screen.getByLabelText(/^password$/i), 'short');
      await user.type(screen.getByLabelText(/confirm password/i), 'short');
      await user.click(screen.getByRole('button', { name: /create account/i }));

      await waitFor(() => {
        const errorAlert = screen.getByRole('alert');
        expect(errorAlert).toHaveTextContent(/password must be at least 8 characters/i);
      });
    });

    it('should require all fields to be filled', async () => {
      const user = userEvent.setup();
      renderPage(<RegisterPage />, { user: null });

      const submitButton = screen.getByRole('button', { name: /create account/i });
      await user.click(submitButton);

      // HTML5 validation should prevent submission
      expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    });

    it('should require valid email format', () => {
      renderPage(<RegisterPage />, { user: null });

      const emailInput = screen.getByLabelText(/email address/i) as HTMLInputElement;
      expect(emailInput.type).toBe('email');
    });
  });

  describe('Form Submission', () => {
    it('should handle successful registration', async () => {
      const user = userEvent.setup();
      renderPage(<RegisterPage />, { user: null });

      await user.type(screen.getByLabelText(/full name/i), 'John Doe');
      await user.type(screen.getByLabelText(/email address/i), 'john@example.com');
      await user.type(screen.getByLabelText(/^password$/i), 'Password123!');
      await user.type(screen.getByLabelText(/confirm password/i), 'Password123!');

      const experienceSelect = screen.getByLabelText(/experience level/i);
      await user.selectOptions(experienceSelect, 'senior');

      await user.click(screen.getByRole('button', { name: /create account/i }));

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /creating account\.\.\./i })).toBeInTheDocument();
      });

      await waitFor(
        () => {
          expect(localStorage.getItem('access_token')).toBe('mock-access-token');
        },
        { timeout: 3000 }
      );
    });

    it('should disable submit button during submission', async () => {
      const user = userEvent.setup();
      renderPage(<RegisterPage />, { user: null });

      await user.type(screen.getByLabelText(/full name/i), 'John Doe');
      await user.type(screen.getByLabelText(/email address/i), 'john@example.com');
      await user.type(screen.getByLabelText(/^password$/i), 'Password123!');
      await user.type(screen.getByLabelText(/confirm password/i), 'Password123!');
      await user.click(screen.getByRole('button', { name: /create account/i }));

      await waitFor(() => {
        const button = screen.getByRole('button', { name: /creating account\.\.\./i });
        expect(button).toBeDisabled();
      });
    });

    it('should display error message on registration failure', async () => {
      server.use(
        http.post('http://localhost:8000/api/v1/users/register', () => {
          return HttpResponse.json({ detail: 'Email already exists' }, { status: 400 });
        })
      );

      const user = userEvent.setup();
      renderPage(<RegisterPage />, { user: null });

      await user.type(screen.getByLabelText(/full name/i), 'John Doe');
      await user.type(screen.getByLabelText(/email address/i), 'existing@example.com');
      await user.type(screen.getByLabelText(/^password$/i), 'Password123!');
      await user.type(screen.getByLabelText(/confirm password/i), 'Password123!');
      await user.click(screen.getByRole('button', { name: /create account/i }));

      await waitFor(() => {
        const errorAlert = screen.getByRole('alert');
        expect(errorAlert).toBeInTheDocument();
        expect(errorAlert).toHaveTextContent(/email already exists/i);
      });
    });

    it('should display generic error on network failure', async () => {
      server.use(
        http.post('http://localhost:8000/api/v1/users/register', () => {
          return HttpResponse.json({ detail: 'Server error' }, { status: 500 });
        })
      );

      const user = userEvent.setup();
      renderPage(<RegisterPage />, { user: null });

      await user.type(screen.getByLabelText(/full name/i), 'John Doe');
      await user.type(screen.getByLabelText(/email address/i), 'john@example.com');
      await user.type(screen.getByLabelText(/^password$/i), 'Password123!');
      await user.type(screen.getByLabelText(/confirm password/i), 'Password123!');
      await user.click(screen.getByRole('button', { name: /create account/i }));

      await waitFor(() => {
        const errorAlert = screen.getByRole('alert');
        expect(errorAlert).toBeInTheDocument();
      });
    });

    it('should clear error message on new submission', async () => {
      server.use(
        http.post('http://localhost:8000/api/v1/users/register', () => {
          return HttpResponse.json({ detail: 'Email already exists' }, { status: 400 });
        })
      );

      const user = userEvent.setup();
      renderPage(<RegisterPage />, { user: null });

      // First submission with error
      await user.type(screen.getByLabelText(/full name/i), 'John Doe');
      await user.type(screen.getByLabelText(/email address/i), 'existing@example.com');
      await user.type(screen.getByLabelText(/^password$/i), 'Password123!');
      await user.type(screen.getByLabelText(/confirm password/i), 'Password123!');
      await user.click(screen.getByRole('button', { name: /create account/i }));

      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument();
      });

      // Clear and retry with valid data
      server.use(
        http.post('http://localhost:8000/api/v1/users/register', () => {
          return HttpResponse.json({
            id: 'new-user-id',
            email: 'john@example.com',
            full_name: 'John Doe',
            experience_level: 'mid',
          });
        })
      );

      await user.clear(screen.getByLabelText(/email address/i));
      await user.type(screen.getByLabelText(/email address/i), 'john@example.com');
      await user.click(screen.getByRole('button', { name: /create account/i }));

      // Error should be cleared
      await waitFor(() => {
        expect(screen.queryByRole('alert')).not.toBeInTheDocument();
      });
    });

    it('should send experience level with registration', async () => {
      let capturedRequestBody: any;

      server.use(
        http.post('http://localhost:8000/api/v1/users/register', async ({ request }) => {
          capturedRequestBody = await request.json();
          return HttpResponse.json({
            id: 'new-user-id',
            email: 'john@example.com',
            full_name: 'John Doe',
            experience_level: 'senior',
          });
        })
      );

      const user = userEvent.setup();
      renderPage(<RegisterPage />, { user: null });

      await user.type(screen.getByLabelText(/full name/i), 'John Doe');
      await user.type(screen.getByLabelText(/email address/i), 'john@example.com');
      await user.type(screen.getByLabelText(/^password$/i), 'Password123!');
      await user.type(screen.getByLabelText(/confirm password/i), 'Password123!');

      const experienceSelect = screen.getByLabelText(/experience level/i);
      await user.selectOptions(experienceSelect, 'senior');

      await user.click(screen.getByRole('button', { name: /create account/i }));

      await waitFor(
        () => {
          expect(capturedRequestBody?.experience_level).toBe('senior');
        },
        { timeout: 3000 }
      );
    });
  });

  describe('Password Strength Indicator', () => {
    it('should show password strength when typing password', async () => {
      const user = userEvent.setup();
      renderPage(<RegisterPage />, { user: null });

      const passwordInput = screen.getByLabelText(/^password$/i);
      await user.type(passwordInput, 'weak');

      await waitFor(() => {
        expect(screen.getByText(/password strength:/i)).toBeInTheDocument();
      });
    });

    it('should not show password strength when password is empty', () => {
      renderPage(<RegisterPage />, { user: null });

      expect(screen.queryByText(/password strength:/i)).not.toBeInTheDocument();
    });

    it('should update strength as password changes', async () => {
      const user = userEvent.setup();
      renderPage(<RegisterPage />, { user: null });

      const passwordInput = screen.getByLabelText(/^password$/i);

      // Weak password
      await user.type(passwordInput, 'weak');
      await waitFor(() => {
        expect(screen.getByText(/password strength:/i)).toBeInTheDocument();
      });

      // Strong password
      await user.clear(passwordInput);
      await user.type(passwordInput, 'StrongP@ssw0rd!');
      await waitFor(() => {
        expect(screen.getByText(/password strength:/i)).toBeInTheDocument();
      });
    });
  });

  describe('Error Display', () => {
    it('should display error with proper ARIA attributes', async () => {
      const user = userEvent.setup();
      renderPage(<RegisterPage />, { user: null });

      await user.type(screen.getByLabelText(/full name/i), 'John Doe');
      await user.type(screen.getByLabelText(/email address/i), 'john@example.com');
      await user.type(screen.getByLabelText(/^password$/i), 'Password123!');
      await user.type(screen.getByLabelText(/confirm password/i), 'WrongPassword!');
      await user.click(screen.getByRole('button', { name: /create account/i }));

      await waitFor(() => {
        const errorAlert = screen.getByRole('alert');
        expect(errorAlert).toHaveAttribute('id', 'register-error');
        expect(errorAlert).toHaveAttribute('aria-live', 'assertive');
      });
    });

    it('should link error to form fields via aria-describedby', async () => {
      server.use(
        http.post('http://localhost:8000/api/v1/users/register', () => {
          return HttpResponse.json({ detail: 'Registration failed' }, { status: 400 });
        })
      );

      const user = userEvent.setup();
      renderPage(<RegisterPage />, { user: null });

      await user.type(screen.getByLabelText(/full name/i), 'John Doe');
      await user.type(screen.getByLabelText(/email address/i), 'john@example.com');
      await user.type(screen.getByLabelText(/^password$/i), 'Password123!');
      await user.type(screen.getByLabelText(/confirm password/i), 'Password123!');
      await user.click(screen.getByRole('button', { name: /create account/i }));

      await waitFor(() => {
        const nameInput = screen.getByLabelText(/full name/i);
        const emailInput = screen.getByLabelText(/email address/i);
        expect(nameInput).toHaveAttribute('aria-invalid', 'true');
        expect(nameInput).toHaveAttribute('aria-describedby', 'register-error');
        expect(emailInput).toHaveAttribute('aria-invalid', 'true');
        expect(emailInput).toHaveAttribute('aria-describedby', 'register-error');
      });
    });

    it('should mark password field as invalid for password-related errors', async () => {
      const user = userEvent.setup();
      renderPage(<RegisterPage />, { user: null });

      await user.type(screen.getByLabelText(/full name/i), 'John Doe');
      await user.type(screen.getByLabelText(/email address/i), 'john@example.com');
      await user.type(screen.getByLabelText(/^password$/i), 'short');
      await user.type(screen.getByLabelText(/confirm password/i), 'short');
      await user.click(screen.getByRole('button', { name: /create account/i }));

      await waitFor(() => {
        const passwordInput = screen.getByLabelText(/^password$/i);
        expect(passwordInput).toHaveAttribute('aria-invalid', 'true');
      });
    });

    it('should mark confirm password as invalid for mismatch errors', async () => {
      const user = userEvent.setup();
      renderPage(<RegisterPage />, { user: null });

      await user.type(screen.getByLabelText(/full name/i), 'John Doe');
      await user.type(screen.getByLabelText(/email address/i), 'john@example.com');
      await user.type(screen.getByLabelText(/^password$/i), 'Password123!');
      await user.type(screen.getByLabelText(/confirm password/i), 'Different!');
      await user.click(screen.getByRole('button', { name: /create account/i }));

      await waitFor(() => {
        const confirmPasswordInput = screen.getByLabelText(/confirm password/i);
        expect(confirmPasswordInput).toHaveAttribute('aria-invalid', 'true');
      });
    });
  });

  describe('Navigation Links', () => {
    it('should navigate to login page', () => {
      renderPage(<RegisterPage />, { user: null });

      const signInLink = screen.getByRole('link', { name: /sign in/i });
      expect(signInLink).toHaveAttribute('href', '/login');
    });
  });

  describe('Accessibility', () => {
    it('should have proper heading hierarchy', () => {
      renderPage(<RegisterPage />, { user: null });

      const heading = screen.getByRole('heading', { name: /create your account/i });
      expect(heading).toBeInTheDocument();
      expect(heading.tagName).toBe('H1');
    });

    it('should have labels for all form inputs', () => {
      renderPage(<RegisterPage />, { user: null });

      expect(screen.getByLabelText(/full name/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/^password$/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/experience level/i)).toBeInTheDocument();
    });

    it('should have proper button role', () => {
      renderPage(<RegisterPage />, { user: null });

      const submitButton = screen.getByRole('button', { name: /create account/i });
      expect(submitButton).toHaveAttribute('type', 'submit');
    });

    it('should have hint text for experience level', () => {
      renderPage(<RegisterPage />, { user: null });

      const hintText = screen.getByText(/this helps us tailor feedback to your experience level/i);
      expect(hintText).toHaveAttribute('id', 'experience-hint');

      const experienceSelect = screen.getByLabelText(/experience level/i);
      expect(experienceSelect).toHaveAttribute('aria-describedby', 'experience-hint');
    });
  });

  describe('Button States', () => {
    it('should show "Create Account" text when not loading', () => {
      renderPage(<RegisterPage />, { user: null });

      expect(screen.getByRole('button', { name: /^create account$/i })).toBeInTheDocument();
    });

    it('should show "Creating account..." text when loading', async () => {
      const user = userEvent.setup();
      renderPage(<RegisterPage />, { user: null });

      await user.type(screen.getByLabelText(/full name/i), 'John Doe');
      await user.type(screen.getByLabelText(/email address/i), 'john@example.com');
      await user.type(screen.getByLabelText(/^password$/i), 'Password123!');
      await user.type(screen.getByLabelText(/confirm password/i), 'Password123!');
      await user.click(screen.getByRole('button', { name: /create account/i }));

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /creating account\.\.\./i })).toBeInTheDocument();
      });
    });

    it('should have enabled submit button when not loading', () => {
      renderPage(<RegisterPage />, { user: null });

      const submitButton = screen.getByRole('button', { name: /create account/i });
      expect(submitButton).not.toBeDisabled();
    });
  });

  describe('URL Parameters', () => {
    it('should preserve plan parameter in sessionStorage', () => {
      renderPage(<RegisterPage />, {
        user: null,
        initialRoute: '/register?plan=pro',
      });

      expect(sessionStorage.getItem('pending_plan')).toBe('pro');
    });

    it('should not set pending_plan if no plan parameter', () => {
      renderPage(<RegisterPage />, {
        user: null,
        initialRoute: '/register',
      });

      expect(sessionStorage.getItem('pending_plan')).toBeNull();
    });
  });

  describe('Integration', () => {
    it('should handle full registration flow from input to success', async () => {
      const user = userEvent.setup();
      renderPage(<RegisterPage />, { user: null });

      // Fill form
      await user.type(screen.getByLabelText(/full name/i), 'John Doe');
      await user.type(screen.getByLabelText(/email address/i), 'john@example.com');
      await user.type(screen.getByLabelText(/^password$/i), 'Password123!');
      await user.type(screen.getByLabelText(/confirm password/i), 'Password123!');

      const experienceSelect = screen.getByLabelText(/experience level/i);
      await user.selectOptions(experienceSelect, 'senior');

      // Submit
      await user.click(screen.getByRole('button', { name: /create account/i }));

      // Verify loading state
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /creating account\.\.\./i })).toBeDisabled();
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

    it('should validate before making API call', async () => {
      const user = userEvent.setup();
      renderPage(<RegisterPage />, { user: null });

      await user.type(screen.getByLabelText(/full name/i), 'John Doe');
      await user.type(screen.getByLabelText(/email address/i), 'john@example.com');
      await user.type(screen.getByLabelText(/^password$/i), 'short');
      await user.type(screen.getByLabelText(/confirm password/i), 'short');
      await user.click(screen.getByRole('button', { name: /create account/i }));

      // Should show client-side validation error immediately
      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent(
          /password must be at least 8 characters/i
        );
      });
    });
  });
});
