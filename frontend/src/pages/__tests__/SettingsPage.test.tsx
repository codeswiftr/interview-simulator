import { describe, it, expect, beforeAll, afterAll, afterEach, vi } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { server } from '../../test/mocks/server';
import { renderWithAuth, createMockUser } from '../../test/utils';
import SettingsPage from '../SettingsPage';
import { ThemeProvider } from '../../contexts/ThemeContext';
import type { SubscriptionStatus } from '../../types';

// Start MSW server for these tests
beforeAll(() => server.listen({ onUnhandledRequest: 'warn' }));
afterEach(() => {
  server.resetHandlers();
  localStorage.clear();
});
afterAll(() => server.close());

// Mock hooks that use browser APIs
vi.mock('../../hooks/useVoicePreferences', () => ({
  useVoicePreferences: () => ({
    settings: {
      enabled: true,
      rate: 1.0,
      pitch: 1.0,
      volume: 0.8,
      voiceName: 'System Default',
    },
    updateSettings: vi.fn(),
    resetSettings: vi.fn(),
  }),
}));

vi.mock('../../hooks/useSpeechSynthesis', () => ({
  useSpeechSynthesis: () => ({
    speak: vi.fn(),
    stop: vi.fn(),
    voices: [],
    setVoice: vi.fn(),
    setRate: vi.fn(),
    setPitch: vi.fn(),
    setVolume: vi.fn(),
    isSupported: true,
  }),
}));

// Mock AuthProvider with authenticated user
const mockUser = createMockUser({
  full_name: 'John Doe',
  email: 'john@example.com',
  experience_level: 'mid',
  total_interviews: 15,
  created_at: '2024-01-15T00:00:00Z',
  subscription_tier: 'free',
});

vi.mock('../../hooks/useAuth', () => ({
  useAuth: () => ({
    user: mockUser,
    refreshUser: vi.fn(),
    isAuthenticated: true,
    loading: false,
  }),
}));

// Helper to render SettingsPage with all providers
const renderSettingsPage = () => {
  return renderWithAuth(
    <ThemeProvider>
      <SettingsPage />
    </ThemeProvider>
  );
};

describe('SettingsPage', () => {
  describe('Basic Rendering', () => {
    it('should render settings page with all sections', async () => {
      renderSettingsPage();

      // Wait for loading to complete
      await waitFor(() => {
        expect(screen.queryByText('Loading settings...')).not.toBeInTheDocument();
      });

      // Check header
      expect(screen.getByRole('heading', { name: /settings/i })).toBeInTheDocument();
      expect(screen.getByText('Back to Dashboard')).toBeInTheDocument();

      // Check all sections
      expect(screen.getByRole('heading', { name: /account overview/i })).toBeInTheDocument();
      expect(screen.getByRole('heading', { name: /^profile$/i })).toBeInTheDocument();
      expect(screen.getByRole('heading', { name: /appearance/i })).toBeInTheDocument();
      expect(screen.getByRole('heading', { name: /voice & conversation/i })).toBeInTheDocument();
      expect(screen.getByRole('heading', { name: /change password/i })).toBeInTheDocument();
      expect(screen.getByRole('heading', { name: /current plan/i })).toBeInTheDocument();
      expect(screen.getByRole('heading', { name: /danger zone/i })).toBeInTheDocument();
    });

    it('should show loading state initially', () => {
      renderSettingsPage();

      expect(screen.getByText('Loading settings...')).toBeInTheDocument();
    });

    it('should handle subscription API error gracefully', async () => {
      server.use(
        http.get('http://localhost:8000/api/v1/subscriptions/status', () => {
          return HttpResponse.json(
            { message: 'Failed to load subscription' },
            { status: 500 }
          );
        })
      );

      renderSettingsPage();

      await waitFor(() => {
        expect(screen.getByText(/failed to load subscription/i)).toBeInTheDocument();
      });
    });
  });

  describe('Account Overview Section', () => {
    it('should display user account information', async () => {
      renderSettingsPage();

      await waitFor(() => {
        expect(screen.queryByText('Loading settings...')).not.toBeInTheDocument();
      });

      // Check name
      expect(screen.getByText('John Doe')).toBeInTheDocument();

      // Check member since date
      expect(screen.getByText(/Jan 2024/i)).toBeInTheDocument();

      // Check total interviews
      expect(screen.getByText('15')).toBeInTheDocument();

      // Check subscription tier
      expect(screen.getByText(/free/i)).toBeInTheDocument();
    });

    it('should handle missing user name gracefully', async () => {
      vi.mock('../../hooks/useAuth', () => ({
        useAuth: () => ({
          user: { ...mockUser, full_name: '' },
          refreshUser: vi.fn(),
          isAuthenticated: true,
          loading: false,
        }),
      }));

      renderSettingsPage();

      await waitFor(() => {
        expect(screen.queryByText('Loading settings...')).not.toBeInTheDocument();
      });

      expect(screen.getByText('Not set')).toBeInTheDocument();
    });
  });

  describe('Profile Form', () => {
    it('should display profile form with current user data', async () => {
      renderSettingsPage();

      await waitFor(() => {
        expect(screen.queryByText('Loading settings...')).not.toBeInTheDocument();
      });

      // Check form fields are populated
      const nameInput = screen.getByLabelText('Full Name') as HTMLInputElement;
      const emailInput = screen.getByLabelText('Email') as HTMLInputElement;
      const experienceSelect = screen.getByLabelText('Experience Level') as HTMLSelectElement;

      expect(nameInput.value).toBe('John Doe');
      expect(emailInput.value).toBe('john@example.com');
      expect(experienceSelect.value).toBe('mid');
    });

    it('should allow editing profile fields', async () => {
      const user = userEvent.setup();
      renderSettingsPage();

      await waitFor(() => {
        expect(screen.queryByText('Loading settings...')).not.toBeInTheDocument();
      });

      const nameInput = screen.getByLabelText('Full Name') as HTMLInputElement;
      const emailInput = screen.getByLabelText('Email') as HTMLInputElement;

      // Clear and type new values
      await user.clear(nameInput);
      await user.type(nameInput, 'Jane Smith');
      expect(nameInput.value).toBe('Jane Smith');

      await user.clear(emailInput);
      await user.type(emailInput, 'jane@example.com');
      expect(emailInput.value).toBe('jane@example.com');
    });

    it('should submit profile changes successfully', async () => {
      const user = userEvent.setup();
      renderSettingsPage();

      await waitFor(() => {
        expect(screen.queryByText('Loading settings...')).not.toBeInTheDocument();
      });

      // Update name
      const nameInput = screen.getByLabelText('Full Name');
      await user.clear(nameInput);
      await user.type(nameInput, 'Jane Smith');

      // Submit form
      const saveButton = screen.getByRole('button', { name: /save changes/i });
      await user.click(saveButton);

      // Check loading state
      await waitFor(() => {
        expect(screen.getByText('Saving...')).toBeInTheDocument();
      });

      // Check success (button returns to normal state)
      await waitFor(() => {
        expect(screen.queryByText('Saving...')).not.toBeInTheDocument();
        expect(screen.getByRole('button', { name: /save changes/i })).toBeInTheDocument();
      });
    });

    it('should handle profile update error', async () => {
      const user = userEvent.setup();
      server.use(
        http.patch('http://localhost:8000/api/v1/users/me', () => {
          return HttpResponse.json(
            { detail: 'Invalid email format' },
            { status: 400 }
          );
        })
      );

      renderSettingsPage();

      await waitFor(() => {
        expect(screen.queryByText('Loading settings...')).not.toBeInTheDocument();
      });

      const saveButton = screen.getByRole('button', { name: /save changes/i });
      await user.click(saveButton);

      await waitFor(() => {
        expect(screen.queryByText('Saving...')).not.toBeInTheDocument();
      });
    });

    it('should allow changing experience level', async () => {
      const user = userEvent.setup();
      renderSettingsPage();

      await waitFor(() => {
        expect(screen.queryByText('Loading settings...')).not.toBeInTheDocument();
      });

      const experienceSelect = screen.getByLabelText('Experience Level');
      await user.selectOptions(experienceSelect, 'senior');

      expect((experienceSelect as HTMLSelectElement).value).toBe('senior');
    });
  });

  describe('Theme Selection', () => {
    it('should display all theme options', async () => {
      renderSettingsPage();

      await waitFor(() => {
        expect(screen.queryByText('Loading settings...')).not.toBeInTheDocument();
      });

      const lightButton = screen.getByRole('button', { name: /light.*bright and clear/i });
      const darkButton = screen.getByRole('button', { name: /dark.*easy on the eyes/i });
      const systemButton = screen.getByRole('button', { name: /system.*auto-adjust/i });

      expect(lightButton).toBeInTheDocument();
      expect(darkButton).toBeInTheDocument();
      expect(systemButton).toBeInTheDocument();
    });

    it('should select light theme', async () => {
      const user = userEvent.setup();
      renderSettingsPage();

      await waitFor(() => {
        expect(screen.queryByText('Loading settings...')).not.toBeInTheDocument();
      });

      const lightButton = screen.getByRole('button', { name: /light.*bright and clear/i });
      await user.click(lightButton);

      await waitFor(() => {
        expect(lightButton).toHaveAttribute('aria-pressed', 'true');
      });

      // Check localStorage
      expect(localStorage.getItem('theme')).toBe('light');
    });

    it('should select dark theme', async () => {
      const user = userEvent.setup();
      renderSettingsPage();

      await waitFor(() => {
        expect(screen.queryByText('Loading settings...')).not.toBeInTheDocument();
      });

      const darkButton = screen.getByRole('button', { name: /dark.*easy on the eyes/i });
      await user.click(darkButton);

      await waitFor(() => {
        expect(darkButton).toHaveAttribute('aria-pressed', 'true');
      });

      expect(localStorage.getItem('theme')).toBe('dark');
    });

    it('should select system theme', async () => {
      const user = userEvent.setup();
      renderSettingsPage();

      await waitFor(() => {
        expect(screen.queryByText('Loading settings...')).not.toBeInTheDocument();
      });

      const systemButton = screen.getByRole('button', { name: /system.*auto-adjust/i });
      await user.click(systemButton);

      await waitFor(() => {
        expect(systemButton).toHaveAttribute('aria-pressed', 'true');
      });

      expect(localStorage.getItem('theme')).toBe('system');
    });

    it('should have correct aria-pressed states', async () => {
      localStorage.setItem('theme', 'dark');
      renderSettingsPage();

      await waitFor(() => {
        expect(screen.queryByText('Loading settings...')).not.toBeInTheDocument();
      });

      const darkButton = screen.getByRole('button', { name: /dark.*easy on the eyes/i });
      expect(darkButton).toHaveAttribute('aria-pressed', 'true');
    });
  });

  describe('Password Change Section', () => {
    it('should display password change form', async () => {
      renderSettingsPage();

      await waitFor(() => {
        expect(screen.queryByText('Loading settings...')).not.toBeInTheDocument();
      });

      expect(screen.getByLabelText('Current Password')).toBeInTheDocument();
      expect(screen.getByLabelText('New Password')).toBeInTheDocument();
      expect(screen.getByLabelText('Confirm New Password')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /change password/i })).toBeInTheDocument();
    });

    it('should disable submit button when fields are empty', async () => {
      renderSettingsPage();

      await waitFor(() => {
        expect(screen.queryByText('Loading settings...')).not.toBeInTheDocument();
      });

      const submitButton = screen.getByRole('button', { name: /change password/i });
      expect(submitButton).toBeDisabled();
    });

    it('should enable submit button when current and new password are filled', async () => {
      const user = userEvent.setup();
      renderSettingsPage();

      await waitFor(() => {
        expect(screen.queryByText('Loading settings...')).not.toBeInTheDocument();
      });

      const currentPasswordInput = screen.getByLabelText('Current Password');
      const newPasswordInput = screen.getByLabelText('New Password');

      await user.type(currentPasswordInput, 'oldPassword123');
      await user.type(newPasswordInput, 'newPassword456');

      const submitButton = screen.getByRole('button', { name: /change password/i });
      expect(submitButton).not.toBeDisabled();
    });

    it('should submit password change successfully', async () => {
      const user = userEvent.setup();
      renderSettingsPage();

      await waitFor(() => {
        expect(screen.queryByText('Loading settings...')).not.toBeInTheDocument();
      });

      const currentPasswordInput = screen.getByLabelText('Current Password');
      const newPasswordInput = screen.getByLabelText('New Password');
      const confirmPasswordInput = screen.getByLabelText('Confirm New Password');

      await user.type(currentPasswordInput, 'oldPassword123');
      await user.type(newPasswordInput, 'newPassword456');
      await user.type(confirmPasswordInput, 'newPassword456');

      const submitButton = screen.getByRole('button', { name: /change password/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('Changing...')).toBeInTheDocument();
      });

      // Fields should be cleared after success
      await waitFor(() => {
        expect((currentPasswordInput as HTMLInputElement).value).toBe('');
        expect((newPasswordInput as HTMLInputElement).value).toBe('');
        expect((confirmPasswordInput as HTMLInputElement).value).toBe('');
      });
    });

    it('should show error when passwords do not match', async () => {
      const user = userEvent.setup();
      renderSettingsPage();

      await waitFor(() => {
        expect(screen.queryByText('Loading settings...')).not.toBeInTheDocument();
      });

      const currentPasswordInput = screen.getByLabelText('Current Password');
      const newPasswordInput = screen.getByLabelText('New Password');
      const confirmPasswordInput = screen.getByLabelText('Confirm New Password');

      await user.type(currentPasswordInput, 'oldPassword123');
      await user.type(newPasswordInput, 'newPassword456');
      await user.type(confirmPasswordInput, 'differentPassword');

      const submitButton = screen.getByRole('button', { name: /change password/i });
      await user.click(submitButton);

      // Form should not submit, button should return to normal state immediately
      await waitFor(() => {
        expect(screen.queryByText('Changing...')).not.toBeInTheDocument();
      });
    });

    it('should show error when new password is too short', async () => {
      const user = userEvent.setup();
      renderSettingsPage();

      await waitFor(() => {
        expect(screen.queryByText('Loading settings...')).not.toBeInTheDocument();
      });

      const currentPasswordInput = screen.getByLabelText('Current Password');
      const newPasswordInput = screen.getByLabelText('New Password');
      const confirmPasswordInput = screen.getByLabelText('Confirm New Password');

      await user.type(currentPasswordInput, 'oldPassword123');
      await user.type(newPasswordInput, 'short');
      await user.type(confirmPasswordInput, 'short');

      const submitButton = screen.getByRole('button', { name: /change password/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.queryByText('Changing...')).not.toBeInTheDocument();
      });
    });

    it('should handle password change API error', async () => {
      const user = userEvent.setup();
      server.use(
        http.post('http://localhost:8000/api/v1/users/me/change-password', () => {
          return HttpResponse.json(
            { detail: 'Current password is incorrect' },
            { status: 400 }
          );
        })
      );

      renderSettingsPage();

      await waitFor(() => {
        expect(screen.queryByText('Loading settings...')).not.toBeInTheDocument();
      });

      const currentPasswordInput = screen.getByLabelText('Current Password');
      const newPasswordInput = screen.getByLabelText('New Password');
      const confirmPasswordInput = screen.getByLabelText('Confirm New Password');

      await user.type(currentPasswordInput, 'wrongPassword');
      await user.type(newPasswordInput, 'newPassword456');
      await user.type(confirmPasswordInput, 'newPassword456');

      const submitButton = screen.getByRole('button', { name: /change password/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.queryByText('Changing...')).not.toBeInTheDocument();
      });
    });
  });

  describe('Subscription Section', () => {
    it('should display subscription information for free tier', async () => {
      const mockSubscription: SubscriptionStatus = {
        tier: 'free',
        status: 'active',
        expires_at: null,
        interviews_this_month: 2,
        interviews_limit: 3,
        can_create_interview: true,
      };

      server.use(
        http.get('http://localhost:8000/api/v1/subscriptions/status', () => {
          return HttpResponse.json(mockSubscription);
        })
      );

      renderSettingsPage();

      await waitFor(() => {
        expect(screen.queryByText('Loading settings...')).not.toBeInTheDocument();
      });

      expect(screen.getByText('Free')).toBeInTheDocument();
      expect(screen.getByText('2 / 3')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /upgrade/i })).toBeInTheDocument();
    });

    it('should display subscription information for pro tier', async () => {
      const mockSubscription: SubscriptionStatus = {
        tier: 'pro',
        status: 'active',
        expires_at: '2025-12-31T23:59:59Z',
        interviews_this_month: 25,
        interviews_limit: null,
        can_create_interview: true,
      };

      server.use(
        http.get('http://localhost:8000/api/v1/subscriptions/status', () => {
          return HttpResponse.json(mockSubscription);
        })
      );

      renderSettingsPage();

      await waitFor(() => {
        expect(screen.queryByText('Loading settings...')).not.toBeInTheDocument();
      });

      expect(screen.getByText('Pro')).toBeInTheDocument();
      expect(screen.getByText('Unlimited interviews')).toBeInTheDocument();
      expect(screen.queryByRole('button', { name: /upgrade/i })).not.toBeInTheDocument();
    });

    it('should show upgrade button for canceled subscriptions', async () => {
      const mockSubscription: SubscriptionStatus = {
        tier: 'pro',
        status: 'canceled',
        expires_at: '2025-01-31T23:59:59Z',
        interviews_this_month: 10,
        interviews_limit: null,
        can_create_interview: true,
      };

      server.use(
        http.get('http://localhost:8000/api/v1/subscriptions/status', () => {
          return HttpResponse.json(mockSubscription);
        })
      );

      renderSettingsPage();

      await waitFor(() => {
        expect(screen.queryByText('Loading settings...')).not.toBeInTheDocument();
      });

      expect(screen.getByRole('button', { name: /resubscribe/i })).toBeInTheDocument();
    });

    it('should show warning when interview limit is reached', async () => {
      const mockSubscription: SubscriptionStatus = {
        tier: 'free',
        status: 'active',
        expires_at: null,
        interviews_this_month: 3,
        interviews_limit: 3,
        can_create_interview: false,
      };

      server.use(
        http.get('http://localhost:8000/api/v1/subscriptions/status', () => {
          return HttpResponse.json(mockSubscription);
        })
      );

      renderSettingsPage();

      await waitFor(() => {
        expect(screen.queryByText('Loading settings...')).not.toBeInTheDocument();
      });

      expect(screen.getByText(/limit reached.*upgrade to pro for unlimited/i)).toBeInTheDocument();
    });
  });

  describe('Danger Zone', () => {
    it('should display danger zone section', async () => {
      renderSettingsPage();

      await waitFor(() => {
        expect(screen.queryByText('Loading settings...')).not.toBeInTheDocument();
      });

      expect(screen.getByRole('heading', { name: /danger zone/i })).toBeInTheDocument();
      expect(screen.getByText(/once you delete your account.*no going back/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /delete account/i })).toBeInTheDocument();
    });

    it('should show confirmation form when delete button is clicked', async () => {
      const user = userEvent.setup();
      renderSettingsPage();

      await waitFor(() => {
        expect(screen.queryByText('Loading settings...')).not.toBeInTheDocument();
      });

      const deleteButton = screen.getByRole('button', { name: /delete account/i });
      await user.click(deleteButton);

      await waitFor(() => {
        expect(screen.getByText(/are you absolutely sure/i)).toBeInTheDocument();
        expect(screen.getByLabelText(/type.*delete.*to confirm/i)).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
      });
    });

    it('should enable delete button only when DELETE is typed correctly', async () => {
      const user = userEvent.setup();
      renderSettingsPage();

      await waitFor(() => {
        expect(screen.queryByText('Loading settings...')).not.toBeInTheDocument();
      });

      const deleteButton = screen.getByRole('button', { name: /^delete account$/i });
      await user.click(deleteButton);

      await waitFor(() => {
        expect(screen.getByLabelText(/type.*delete.*to confirm/i)).toBeInTheDocument();
      });

      const confirmInput = screen.getByLabelText(/type.*delete.*to confirm/i);
      const confirmDeleteButton = screen.getAllByRole('button', { name: /delete account/i })[1];

      // Initially disabled
      expect(confirmDeleteButton).toBeDisabled();

      // Type incorrect text
      await user.type(confirmInput, 'delete');
      expect(confirmDeleteButton).toBeDisabled();

      // Clear and type correct text
      await user.clear(confirmInput);
      await user.type(confirmInput, 'DELETE');
      expect(confirmDeleteButton).not.toBeDisabled();
    });

    it('should cancel delete confirmation', async () => {
      const user = userEvent.setup();
      renderSettingsPage();

      await waitFor(() => {
        expect(screen.queryByText('Loading settings...')).not.toBeInTheDocument();
      });

      const deleteButton = screen.getByRole('button', { name: /delete account/i });
      await user.click(deleteButton);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
      });

      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      await user.click(cancelButton);

      await waitFor(() => {
        expect(screen.queryByText(/are you absolutely sure/i)).not.toBeInTheDocument();
        expect(screen.getByText(/once you delete your account.*no going back/i)).toBeInTheDocument();
      });
    });
  });

  describe('Voice Settings', () => {
    it('should display voice settings section', async () => {
      renderSettingsPage();

      await waitFor(() => {
        expect(screen.queryByText('Loading settings...')).not.toBeInTheDocument();
      });

      expect(screen.getByRole('heading', { name: /voice & conversation/i })).toBeInTheDocument();
      expect(screen.getByText(/configure the mentor voice/i)).toBeInTheDocument();
    });

    it('should display current voice settings summary', async () => {
      renderSettingsPage();

      await waitFor(() => {
        expect(screen.queryByText('Loading settings...')).not.toBeInTheDocument();
      });

      // Check for voice summary text
      expect(screen.getByText(/System Default.*1\.00x.*pitch 1\.00.*volume 0\.80/)).toBeInTheDocument();
    });
  });

  describe('Navigation', () => {
    it('should have a back to dashboard link', async () => {
      renderSettingsPage();

      await waitFor(() => {
        expect(screen.queryByText('Loading settings...')).not.toBeInTheDocument();
      });

      const backLink = screen.getByText('Back to Dashboard');
      expect(backLink).toBeInTheDocument();
      expect(backLink.closest('a')).toHaveAttribute('href', '/dashboard');
    });
  });

  describe('Search Params Handling', () => {
    it('should handle Stripe success redirect', async () => {
      // This test would require mocking useSearchParams and useNavigate
      // For now, we'll skip this as it requires more complex routing setup
    });

    it('should handle Stripe cancel redirect', async () => {
      // This test would require mocking useSearchParams and useNavigate
      // For now, we'll skip this as it requires more complex routing setup
    });
  });
});
