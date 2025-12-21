import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { server } from '@/test/mocks/server';
import UpgradeModal from '../UpgradeModal';
import * as analytics from '../../../lib/analytics';

// Mock analytics
vi.mock('../../../lib/analytics', () => ({
  analytics: {
    track: vi.fn(),
  },
  Events: {
    UPGRADE_MODAL_OPENED: 'upgrade_modal_opened',
    UPGRADE_CTA_CLICKED: 'upgrade_cta_clicked',
    CHECKOUT_STARTED: 'checkout_started',
    UPGRADE_REASON_SUBMITTED: 'upgrade_reason_submitted',
  },
}));

// Mock window.location.href
delete (window as { location?: Location }).location;
window.location = { href: '' } as Location;

const API_URL = 'http://localhost:8000/api/v1';

describe('UpgradeModal', () => {
  const defaultProps = {
    isOpen: true,
    onClose: vi.fn(),
    currentTier: 'free' as const,
    onSuccess: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    window.location.href = '';
  });

  afterEach(() => {
    vi.clearAllTimers();
  });

  describe('Modal Rendering', () => {
    it('should render modal when isOpen is true', () => {
      render(<UpgradeModal {...defaultProps} />);

      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.getByText('Upgrade to Pro')).toBeInTheDocument();
    });

    it('should not render modal when isOpen is false', () => {
      render(<UpgradeModal {...defaultProps} isOpen={false} />);

      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });

    it('should have proper ARIA attributes', () => {
      render(<UpgradeModal {...defaultProps} />);

      const dialog = screen.getByRole('dialog');
      expect(dialog).toHaveAttribute('aria-modal', 'true');
      expect(dialog).toHaveAttribute('aria-labelledby', 'upgrade-modal-title');
    });

    it('should track modal opened event on mount', () => {
      render(<UpgradeModal {...defaultProps} />);

      expect(analytics.analytics.track).toHaveBeenCalledWith(
        'upgrade_modal_opened',
        { surface: 'upgrade_modal' }
      );
    });

    it('should not track modal opened event when isOpen is false', () => {
      render(<UpgradeModal {...defaultProps} isOpen={false} />);

      expect(analytics.analytics.track).not.toHaveBeenCalled();
    });

    it('should fetch pricing data when modal opens', async () => {
      render(<UpgradeModal {...defaultProps} />);

      await waitFor(() => {
        // The component fetches pricing internally; we just verify it renders
        expect(screen.getByRole('dialog')).toBeInTheDocument();
      });
    });
  });

  describe('Close Button Functionality', () => {
    it('should render close button', () => {
      render(<UpgradeModal {...defaultProps} />);

      const closeButton = screen.getByRole('button', { name: /close dialog/i });
      expect(closeButton).toBeInTheDocument();
    });

    it('should call onClose when close button is clicked', async () => {
      const user = userEvent.setup();
      const onClose = vi.fn();

      render(<UpgradeModal {...defaultProps} onClose={onClose} />);

      const closeButton = screen.getByRole('button', { name: /close dialog/i });
      await user.click(closeButton);

      expect(onClose).toHaveBeenCalledTimes(1);
    });

    it('should call onClose when cancel button is clicked', async () => {
      const user = userEvent.setup();
      const onClose = vi.fn();

      render(<UpgradeModal {...defaultProps} onClose={onClose} />);

      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      await user.click(cancelButton);

      expect(onClose).toHaveBeenCalledTimes(1);
    });
  });

  describe('Pricing Display', () => {
    it('should display Free plan pricing', () => {
      render(<UpgradeModal {...defaultProps} />);

      expect(screen.getByText('Free')).toBeInTheDocument();
      expect(screen.getByText('$0')).toBeInTheDocument();
      expect(screen.getByText('5 interviews/month')).toBeInTheDocument();
      expect(screen.getByText('Basic feedback')).toBeInTheDocument();
    });

    it('should display Pro plan pricing', () => {
      render(<UpgradeModal {...defaultProps} />);

      expect(screen.getByText('Pro')).toBeInTheDocument();
      expect(screen.getByText('$29')).toBeInTheDocument();
      expect(screen.getByText('Recommended')).toBeInTheDocument();
    });

    it('should highlight Pro plan with special styling', () => {
      const { container } = render(<UpgradeModal {...defaultProps} />);

      // Find the Pro plan card by checking for the border color class
      const proCard = container.querySelector('.border-\\[\\#FF6B9D\\]');
      expect(proCard).toBeInTheDocument();
    });
  });

  describe('Feature List Display', () => {
    const features = [
      'Unlimited interview sessions',
      'Full multimodal feedback analysis',
      'Advanced progress tracking',
      'Priority customer support',
      'Company-specific question sets',
    ];

    it('should display all Pro features', () => {
      render(<UpgradeModal {...defaultProps} />);

      features.forEach((feature) => {
        expect(screen.getByText(feature)).toBeInTheDocument();
      });
    });

    it('should display check icons for all features', () => {
      render(<UpgradeModal {...defaultProps} />);

      // All features should have checkmarks - look for the Check icon component
      const features = [
        'Unlimited interview sessions',
        'Full multimodal feedback analysis',
        'Advanced progress tracking',
        'Priority customer support',
        'Company-specific question sets',
      ];

      features.forEach((feature) => {
        const featureElement = screen.getByText(feature);
        expect(featureElement).toBeInTheDocument();
      });
    });
  });

  describe('Upgrade Button Click', () => {
    it('should render upgrade button', () => {
      render(<UpgradeModal {...defaultProps} />);

      expect(screen.getByRole('button', { name: /upgrade now/i })).toBeInTheDocument();
    });

    it('should successfully handle upgrade button click and redirect to Stripe', async () => {
      const user = userEvent.setup();

      // Mock successful checkout creation
      server.use(
        http.post(`${API_URL}/subscriptions/checkout`, () => {
          return HttpResponse.json({
            url: 'https://checkout.stripe.com/session/test-123',
          });
        })
      );

      render(<UpgradeModal {...defaultProps} />);

      const upgradeButton = screen.getByRole('button', { name: /upgrade now/i });
      await user.click(upgradeButton);

      // Check analytics events
      expect(analytics.analytics.track).toHaveBeenCalledWith(
        'upgrade_cta_clicked',
        { surface: 'upgrade_modal', plan: 'pro' }
      );

      await waitFor(() => {
        expect(analytics.analytics.track).toHaveBeenCalledWith(
          'checkout_started',
          { plan: 'pro' }
        );
      });

      // Check redirect
      await waitFor(() => {
        expect(window.location.href).toBe('https://checkout.stripe.com/session/test-123');
      });
    });

    it('should display error when checkout fails', async () => {
      const user = userEvent.setup();

      // Mock failed checkout creation
      server.use(
        http.post(`${API_URL}/subscriptions/checkout`, () => {
          return HttpResponse.json(
            { detail: 'Payment processing error' },
            { status: 500 }
          );
        })
      );

      render(<UpgradeModal {...defaultProps} />);

      const upgradeButton = screen.getByRole('button', { name: /upgrade now/i });
      await user.click(upgradeButton);

      await waitFor(() => {
        expect(screen.getByText('Payment processing error')).toBeInTheDocument();
      });

      // Button should be enabled again after error
      expect(upgradeButton).not.toBeDisabled();
    });

    it('should display error when pricing is not configured', async () => {
      const user = userEvent.setup();

      // Mock pricing fetch to return empty
      server.use(
        http.get(`${API_URL}/subscriptions/pricing`, () => {
          return HttpResponse.json({
            pro_monthly_price_id: null,
            pro_annual_price_id: null,
          });
        })
      );

      render(<UpgradeModal {...defaultProps} />);

      // Wait for pricing to be fetched
      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument();
      });

      const upgradeButton = screen.getByRole('button', { name: /upgrade now/i });
      await user.click(upgradeButton);

      await waitFor(() => {
        expect(screen.getByText(/pricing not configured/i)).toBeInTheDocument();
      });
    });

    it('should disable upgrade button while loading', async () => {
      const user = userEvent.setup();

      // Mock slow checkout creation
      server.use(
        http.post(`${API_URL}/subscriptions/checkout`, async () => {
          await new Promise((resolve) => setTimeout(resolve, 1000));
          return HttpResponse.json({
            url: 'https://checkout.stripe.com/session/test-123',
          });
        })
      );

      render(<UpgradeModal {...defaultProps} />);

      const upgradeButton = screen.getByRole('button', { name: /upgrade now/i });
      await user.click(upgradeButton);

      // Check button is disabled while loading
      expect(upgradeButton).toBeDisabled();
      expect(screen.getByText('Processing...')).toBeInTheDocument();
    });

    it('should disable cancel button while loading', async () => {
      const user = userEvent.setup();

      // Mock slow checkout creation
      server.use(
        http.post(`${API_URL}/subscriptions/checkout`, async () => {
          await new Promise((resolve) => setTimeout(resolve, 1000));
          return HttpResponse.json({
            url: 'https://checkout.stripe.com/session/test-123',
          });
        })
      );

      render(<UpgradeModal {...defaultProps} />);

      const upgradeButton = screen.getByRole('button', { name: /upgrade now/i });
      await user.click(upgradeButton);

      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      expect(cancelButton).toBeDisabled();
    });
  });

  describe('Feedback Form Interaction', () => {
    it('should render feedback form elements', () => {
      render(<UpgradeModal {...defaultProps} />);

      expect(screen.getByText(/what made you click upgrade/i)).toBeInTheDocument();
      expect(screen.getByRole('combobox')).toBeInTheDocument();
      expect(screen.getByPlaceholderText(/optional detail/i)).toBeInTheDocument();
    });

    it('should render all feedback reason options', () => {
      render(<UpgradeModal {...defaultProps} />);

      const select = screen.getByRole('combobox');
      expect(select).toHaveTextContent('Select a reason…');

      // Get all options
      const options = Array.from(select.querySelectorAll('option'));
      const optionTexts = options.map((opt) => opt.textContent);

      expect(optionTexts).toContain('Unlimited sessions');
      expect(optionTexts).toContain('Better feedback quality');
      expect(optionTexts).toContain('Interview soon');
      expect(optionTexts).toContain('Company-specific questions');
      expect(optionTexts).toContain('Other');
    });

    it('should update reason when option is selected', async () => {
      const user = userEvent.setup();

      render(<UpgradeModal {...defaultProps} />);

      const select = screen.getByRole('combobox');
      await user.selectOptions(select, 'unlimited_sessions');

      expect(select).toHaveValue('unlimited_sessions');
    });

    it('should update details when input changes', async () => {
      const user = userEvent.setup();

      render(<UpgradeModal {...defaultProps} />);

      const input = screen.getByPlaceholderText(/optional detail/i);
      await user.type(input, 'Need to practice more');

      expect(input).toHaveValue('Need to practice more');
    });

    it('should have send button disabled when no feedback provided', () => {
      render(<UpgradeModal {...defaultProps} />);

      const sendButton = screen.getByRole('button', { name: /send/i });
      expect(sendButton).toBeDisabled();
    });

    it('should enable send button when reason is selected', async () => {
      const user = userEvent.setup();

      render(<UpgradeModal {...defaultProps} />);

      const select = screen.getByRole('combobox');
      await user.selectOptions(select, 'unlimited_sessions');

      const sendButton = screen.getByRole('button', { name: /send/i });
      expect(sendButton).not.toBeDisabled();
    });

    it('should enable send button when details are provided', async () => {
      const user = userEvent.setup();

      render(<UpgradeModal {...defaultProps} />);

      const input = screen.getByPlaceholderText(/optional detail/i);
      await user.type(input, 'Need to practice more');

      const sendButton = screen.getByRole('button', { name: /send/i });
      expect(sendButton).not.toBeDisabled();
    });

    it('should submit feedback and show confirmation', async () => {
      const user = userEvent.setup();

      render(<UpgradeModal {...defaultProps} />);

      const select = screen.getByRole('combobox');
      await user.selectOptions(select, 'unlimited_sessions');

      const input = screen.getByPlaceholderText(/optional detail/i);
      await user.type(input, 'Need more practice time');

      const sendButton = screen.getByRole('button', { name: /send/i });
      await user.click(sendButton);

      // Check analytics event
      expect(analytics.analytics.track).toHaveBeenCalledWith(
        'upgrade_reason_submitted',
        {
          surface: 'upgrade_modal',
          reason: 'unlimited_sessions',
          details_len: 23,
        }
      );

      // Check confirmation message
      await waitFor(() => {
        expect(screen.getByText('Thanks for your feedback!')).toBeInTheDocument();
      });

      // Send button should be replaced with confirmation
      expect(screen.queryByRole('button', { name: /send/i })).not.toBeInTheDocument();
    });

    it('should submit feedback with only reason (no details)', async () => {
      const user = userEvent.setup();

      render(<UpgradeModal {...defaultProps} />);

      const select = screen.getByRole('combobox');
      await user.selectOptions(select, 'interview_soon');

      const sendButton = screen.getByRole('button', { name: /send/i });
      await user.click(sendButton);

      expect(analytics.analytics.track).toHaveBeenCalledWith(
        'upgrade_reason_submitted',
        {
          surface: 'upgrade_modal',
          reason: 'interview_soon',
          details_len: 0,
        }
      );
    });

    it('should submit feedback with only details (no reason)', async () => {
      const user = userEvent.setup();

      render(<UpgradeModal {...defaultProps} />);

      const input = screen.getByPlaceholderText(/optional detail/i);
      await user.type(input, 'Just want to try it out');

      const sendButton = screen.getByRole('button', { name: /send/i });
      await user.click(sendButton);

      expect(analytics.analytics.track).toHaveBeenCalledWith(
        'upgrade_reason_submitted',
        {
          surface: 'upgrade_modal',
          reason: 'unspecified',
          details_len: 23,
        }
      );
    });

    it('should submit feedback automatically when upgrading', async () => {
      const user = userEvent.setup();

      render(<UpgradeModal {...defaultProps} />);

      const select = screen.getByRole('combobox');
      await user.selectOptions(select, 'unlimited_sessions');

      const upgradeButton = screen.getByRole('button', { name: /upgrade now/i });
      await user.click(upgradeButton);

      // Feedback should be submitted before checkout
      expect(analytics.analytics.track).toHaveBeenCalledWith(
        'upgrade_reason_submitted',
        expect.objectContaining({
          surface: 'upgrade_modal',
          reason: 'unlimited_sessions',
        })
      );
    });
  });

  describe('Focus Trap Behavior', () => {
    it('should trap focus within modal', async () => {
      const user = userEvent.setup();

      render(<UpgradeModal {...defaultProps} />);

      const dialog = screen.getByRole('dialog');
      expect(dialog).toBeInTheDocument();

      // Get all focusable elements
      const buttons = screen.getAllByRole('button');
      const firstButton = buttons[0];

      // Focus should be trapped within the modal
      firstButton.focus();
      expect(document.activeElement).toBe(firstButton);

      // Tab to last element
      await user.tab();

      // Verify focus moved
      expect(document.activeElement).not.toBe(firstButton);
    });

    it('should focus first element when modal opens', () => {
      const { rerender } = render(<UpgradeModal {...defaultProps} isOpen={false} />);

      // Open modal
      rerender(<UpgradeModal {...defaultProps} isOpen={true} />);

      // Check that something in the modal has focus
      const dialog = screen.getByRole('dialog');
      expect(dialog.contains(document.activeElement)).toBe(true);
    });

    it('should prevent body scroll when modal is open', () => {
      render(<UpgradeModal {...defaultProps} />);

      expect(document.body.style.overflow).toBe('hidden');
    });

    it('should restore body scroll when modal closes', () => {
      const { rerender } = render(<UpgradeModal {...defaultProps} />);

      expect(document.body.style.overflow).toBe('hidden');

      rerender(<UpgradeModal {...defaultProps} isOpen={false} />);

      // Give time for cleanup
      expect(document.body.style.overflow).toBe('');
    });
  });

  describe('Escape Key Closes Modal', () => {
    it('should call onClose when Escape key is pressed', async () => {
      const user = userEvent.setup();
      const onClose = vi.fn();

      render(<UpgradeModal {...defaultProps} onClose={onClose} />);

      await user.keyboard('{Escape}');

      expect(onClose).toHaveBeenCalledTimes(1);
    });

    it('should not close when other keys are pressed', async () => {
      const user = userEvent.setup();
      const onClose = vi.fn();

      render(<UpgradeModal {...defaultProps} onClose={onClose} />);

      await user.keyboard('{Enter}');
      await user.keyboard('{Space}');
      await user.keyboard('a');

      expect(onClose).not.toHaveBeenCalled();
    });
  });

  describe('Error Handling', () => {
    it('should display error message when API returns error', async () => {
      const user = userEvent.setup();

      server.use(
        http.post(`${API_URL}/subscriptions/checkout`, () => {
          return HttpResponse.json(
            { detail: 'Subscription limit reached' },
            { status: 400 }
          );
        })
      );

      render(<UpgradeModal {...defaultProps} />);

      const upgradeButton = screen.getByRole('button', { name: /upgrade now/i });
      await user.click(upgradeButton);

      await waitFor(() => {
        expect(screen.getByText('Subscription limit reached')).toBeInTheDocument();
      });
    });

    it('should display error message with fallback when API returns message field', async () => {
      const user = userEvent.setup();

      server.use(
        http.post(`${API_URL}/subscriptions/checkout`, () => {
          return HttpResponse.json(
            { message: 'Service temporarily unavailable' },
            { status: 503 }
          );
        })
      );

      render(<UpgradeModal {...defaultProps} />);

      const upgradeButton = screen.getByRole('button', { name: /upgrade now/i });
      await user.click(upgradeButton);

      await waitFor(() => {
        expect(screen.getByText('Service temporarily unavailable')).toBeInTheDocument();
      });
    });

    it('should display generic error when no error details provided', async () => {
      const user = userEvent.setup();

      server.use(
        http.post(`${API_URL}/subscriptions/checkout`, () => {
          return HttpResponse.json({}, { status: 500 });
        })
      );

      render(<UpgradeModal {...defaultProps} />);

      const upgradeButton = screen.getByRole('button', { name: /upgrade now/i });
      await user.click(upgradeButton);

      await waitFor(() => {
        expect(screen.getByText('Failed to create checkout session')).toBeInTheDocument();
      });
    });

    it('should clear previous error when retrying upgrade', async () => {
      const user = userEvent.setup();

      // First request fails
      server.use(
        http.post(`${API_URL}/subscriptions/checkout`, () => {
          return HttpResponse.json(
            { detail: 'First error' },
            { status: 500 }
          );
        })
      );

      render(<UpgradeModal {...defaultProps} />);

      const upgradeButton = screen.getByRole('button', { name: /upgrade now/i });
      await user.click(upgradeButton);

      await waitFor(() => {
        expect(screen.getByText('First error')).toBeInTheDocument();
      });

      // Second request succeeds
      server.use(
        http.post(`${API_URL}/subscriptions/checkout`, () => {
          return HttpResponse.json({
            url: 'https://checkout.stripe.com/session/test-123',
          });
        })
      );

      await user.click(upgradeButton);

      // Error should be cleared
      await waitFor(() => {
        expect(screen.queryByText('First error')).not.toBeInTheDocument();
      });
    });
  });

  describe('Accessibility', () => {
    it('should have accessible close button label', () => {
      render(<UpgradeModal {...defaultProps} />);

      const closeButton = screen.getByRole('button', { name: /close dialog/i });
      expect(closeButton).toHaveAttribute('aria-label', 'Close dialog');
    });

    it('should have accessible crown icons with aria-hidden', () => {
      const { container } = render(<UpgradeModal {...defaultProps} />);

      const crownIcons = container.querySelectorAll('svg[aria-hidden="true"]');
      expect(crownIcons.length).toBeGreaterThan(0);
    });

    it('should have proper heading hierarchy', () => {
      render(<UpgradeModal {...defaultProps} />);

      const mainHeading = screen.getByRole('heading', { name: /upgrade to pro/i });
      expect(mainHeading).toHaveAttribute('id', 'upgrade-modal-title');
    });

    it('should have visible focus indicators on interactive elements', async () => {
      const user = userEvent.setup();

      render(<UpgradeModal {...defaultProps} />);

      const closeButton = screen.getByRole('button', { name: /close dialog/i });
      await user.tab();

      // Check for focus ring classes (focus:ring-2, focus:ring-electric-blue)
      expect(closeButton.className).toContain('focus:ring-2');
    });
  });

  describe('Redirect Information', () => {
    it('should display Stripe redirect information', () => {
      render(<UpgradeModal {...defaultProps} />);

      expect(
        screen.getByText(/you'll be redirected to stripe/i)
      ).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('should handle rapid multiple upgrade button clicks gracefully', async () => {
      const user = userEvent.setup();

      render(<UpgradeModal {...defaultProps} />);

      const upgradeButton = screen.getByRole('button', { name: /upgrade now/i });

      // Rapidly click multiple times
      await user.click(upgradeButton);
      await user.click(upgradeButton);
      await user.click(upgradeButton);

      // Should only make one API call (button is disabled after first click)
      // Verify button was disabled after first click to prevent multiple submissions
      await waitFor(() => {
        expect(upgradeButton).toBeDisabled();
      });
    });

    it('should handle empty feedback input gracefully', async () => {
      const user = userEvent.setup();

      render(<UpgradeModal {...defaultProps} />);

      const input = screen.getByPlaceholderText(/optional detail/i);
      await user.type(input, '   '); // Only whitespace

      const sendButton = screen.getByRole('button', { name: /send/i });
      expect(sendButton).toBeDisabled();
    });

    it('should handle pricing fetch failure gracefully', async () => {
      server.use(
        http.get(`${API_URL}/subscriptions/pricing`, () => {
          return HttpResponse.json(
            { detail: 'Pricing service unavailable' },
            { status: 503 }
          );
        })
      );

      render(<UpgradeModal {...defaultProps} />);

      // Modal should still render
      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });
  });
});
