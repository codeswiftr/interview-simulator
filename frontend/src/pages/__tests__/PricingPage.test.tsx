import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import PricingPage from '../PricingPage';
import { AuthProvider } from '../../hooks/useAuth';

// Mock navigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

// Mock the API modules
vi.mock('../../lib/api', () => ({
  authAPI: {
    getCurrentUser: vi.fn(),
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
  },
  subscriptionsAPI: {
    getPricing: vi.fn(() => Promise.resolve({
      data: {
        pro_monthly_price_id: 'price_monthly_123',
        pro_annual_price_id: 'price_annual_123',
      },
    })),
    createCheckout: vi.fn(() => Promise.resolve({
      data: { url: 'https://checkout.stripe.com/test' },
    })),
  },
}));

// Mock the analytics module
vi.mock('../../lib/analytics', () => ({
  analytics: {
    identify: vi.fn(),
    track: vi.fn(),
    reset: vi.fn(),
  },
  Events: {
    PAGE_VIEWED: 'page_viewed',
    UPGRADE_CTA_CLICKED: 'upgrade_cta_clicked',
    CHECKOUT_STARTED: 'checkout_started',
  },
}));

// Mock the utm module
vi.mock('../../lib/utm', () => ({
  getStoredUTM: vi.fn(() => ({})),
}));

describe('PricingPage', () => {
  // Helper function to render PricingPage with routing and auth context
  const renderPricingPage = async (isAuthenticated = false, subscriptionTier = 'free') => {
    // Mock localStorage based on authentication status
    if (isAuthenticated) {
      localStorage.setItem('access_token', 'mock-token');
      const { authAPI } = await import('../../lib/api');
      vi.mocked(authAPI.getCurrentUser).mockResolvedValue({
        data: {
          id: '123',
          email: 'test@example.com',
          full_name: 'Test User',
          subscription_tier: subscriptionTier,
          created_at: new Date().toISOString(),
        },
      } as any);
    } else {
      localStorage.clear();
    }

    return render(
      <MemoryRouter>
        <AuthProvider>
          <PricingPage />
        </AuthProvider>
      </MemoryRouter>
    );
  };

  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    mockNavigate.mockClear();
  });

  describe('Basic Rendering', () => {
    it('renders the page without crashing', async () => {
      const { container } = await renderPricingPage();
      const mainContent = container.querySelector('.min-h-screen');
      expect(mainContent).toBeInTheDocument();
    });

    it('displays the main headline', async () => {
      await renderPricingPage();
      expect(screen.getByText('Simple, Transparent Pricing')).toBeInTheDocument();
    });

    it('displays the subheadline', async () => {
      await renderPricingPage();
      expect(screen.getByText(/Start free, upgrade when you're ready/i)).toBeInTheDocument();
    });
  });

  describe('Billing Toggle', () => {
    it('displays monthly and annual toggle buttons', async () => {
      await renderPricingPage();
      const buttons = screen.getAllByRole('button');
      const monthlyButton = buttons.find(btn => btn.textContent === 'Monthly');
      const annualButton = buttons.find(btn => btn.textContent?.includes('Annual'));
      expect(monthlyButton).toBeTruthy();
      expect(annualButton).toBeTruthy();
    });

    it('shows savings badge on annual option', async () => {
      await renderPricingPage();
      expect(screen.getByText(/Save 17%/i)).toBeInTheDocument();
    });

    it('defaults to monthly billing', async () => {
      await renderPricingPage();
      expect(screen.getByText('$29')).toBeInTheDocument();
    });

    it('switches to annual pricing when annual is selected', async () => {
      await renderPricingPage();
      
      const buttons = screen.getAllByRole('button');
      const annualButton = buttons.find(btn => btn.textContent?.includes('Annual'));
      if (annualButton) fireEvent.click(annualButton);

      // Annual price should show $24/month equivalent
      await waitFor(() => {
        expect(screen.getByText('$24')).toBeInTheDocument();
      });
    });

    it('shows annual total when annual is selected', async () => {
      await renderPricingPage();
      
      const buttons = screen.getAllByRole('button');
      const annualButton = buttons.find(btn => btn.textContent?.includes('Annual'));
      if (annualButton) fireEvent.click(annualButton);

      await waitFor(() => {
        expect(screen.getByText(/\$290\/year/i)).toBeInTheDocument();
      });
    });
  });

  describe('Free Plan Card', () => {
    it('displays Free plan with $0 price', async () => {
      await renderPricingPage();
      expect(screen.getByText('$0')).toBeInTheDocument();
    });

    it('displays Free plan features', async () => {
      await renderPricingPage();
      expect(screen.getByText('5 interviews per month')).toBeInTheDocument();
      expect(screen.getByText('Basic AI feedback')).toBeInTheDocument();
    });

    it('shows Get Started Free button for unauthenticated users', async () => {
      await renderPricingPage(false);
      expect(screen.getByRole('link', { name: /Get Started Free/i })).toBeInTheDocument();
    });

    it('links to register for new users', async () => {
      await renderPricingPage(false);
      const getStartedLink = screen.getByRole('link', { name: /Get Started Free/i });
      expect(getStartedLink).toHaveAttribute('href', '/register');
    });
  });

  describe('Pro Plan Card', () => {
    it('displays Pro plan with correct price', async () => {
      await renderPricingPage();
      expect(screen.getByText('$29')).toBeInTheDocument();
    });

    it('displays MOST POPULAR badge', async () => {
      await renderPricingPage();
      expect(screen.getByText('MOST POPULAR')).toBeInTheDocument();
    });

    it('displays 7-day free trial badge', async () => {
      await renderPricingPage();
      expect(screen.getByText('7-day free trial')).toBeInTheDocument();
    });

    it('displays Pro plan features', async () => {
      await renderPricingPage();
      // These texts appear in both Pro card and comparison table, so use getAllByText
      expect(screen.getAllByText('Unlimited interviews').length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText('Advanced feedback analysis').length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText('Company-specific questions').length).toBeGreaterThanOrEqual(1);
    });

    it('shows Start Free Trial button for unauthenticated users', async () => {
      await renderPricingPage(false);
      const trialButtons = screen.getAllByRole('button', { name: /Start Free Trial/i });
      expect(trialButtons.length).toBeGreaterThanOrEqual(1);
    });

    it('displays Pro plan card with upgrade option', async () => {
      await renderPricingPage(false);
      // Pro plan card should always show Start Free Trial for non-authenticated users
      const trialButtons = screen.getAllByRole('button', { name: /Start Free Trial/i });
      expect(trialButtons.length).toBeGreaterThanOrEqual(1);
    });
  });

  describe('Team Plan Teaser', () => {
    it('displays Team Plans Coming Soon message', async () => {
      await renderPricingPage();
      expect(screen.getByText('Team Plans Coming Soon')).toBeInTheDocument();
    });

    it('displays Get Notified link', async () => {
      await renderPricingPage();
      expect(screen.getByRole('link', { name: /Get Notified/i })).toBeInTheDocument();
    });
  });

  describe('Feature Comparison Table', () => {
    it('displays Compare Plans heading', async () => {
      await renderPricingPage();
      expect(screen.getByText('Compare Plans')).toBeInTheDocument();
    });

    it('displays table headers', async () => {
      await renderPricingPage();
      expect(screen.getByText('Feature')).toBeInTheDocument();
    });

    it('displays comparison rows', async () => {
      await renderPricingPage();
      expect(screen.getByText('Interviews per month')).toBeInTheDocument();
      expect(screen.getByText('AI Feedback')).toBeInTheDocument();
      expect(screen.getByText('Question Bank')).toBeInTheDocument();
    });
  });

  describe('FAQ Section', () => {
    it('displays FAQ heading', async () => {
      await renderPricingPage();
      expect(screen.getByText('Frequently Asked Questions')).toBeInTheDocument();
    });

    it('displays FAQ questions', async () => {
      await renderPricingPage();
      expect(screen.getByText(/What happens after my 7-day free trial/i)).toBeInTheDocument();
      expect(screen.getByText(/Can I cancel my subscription anytime/i)).toBeInTheDocument();
    });

    it('expands FAQ answer when clicked', async () => {
      await renderPricingPage();
      
      const faqButton = screen.getByRole('button', { name: /What happens after my 7-day free trial/i });
      fireEvent.click(faqButton);

      await waitFor(() => {
        expect(screen.getByText(/After your trial ends/i)).toBeInTheDocument();
      });
    });

    it('collapses FAQ answer when clicked again', async () => {
      await renderPricingPage();
      
      const faqButton = screen.getByRole('button', { name: /What happens after my 7-day free trial/i });
      
      // Expand
      fireEvent.click(faqButton);
      await waitFor(() => {
        expect(screen.getByText(/After your trial ends/i)).toBeInTheDocument();
      });

      // Collapse
      fireEvent.click(faqButton);
      await waitFor(() => {
        expect(screen.queryByText(/After your trial ends/i)).not.toBeInTheDocument();
      });
    });
  });

  describe('Final CTA Section', () => {
    it('displays CTA heading', async () => {
      await renderPricingPage();
      expect(screen.getByText('Start Your Interview Prep Today')).toBeInTheDocument();
    });

    it('displays CTA description', async () => {
      await renderPricingPage();
      expect(screen.getByText(/Join thousands of engineers/i)).toBeInTheDocument();
    });

    it('shows Try Free Plan link for unauthenticated users', async () => {
      await renderPricingPage(false);
      expect(screen.getByRole('link', { name: /Try Free Plan/i })).toBeInTheDocument();
    });
  });

  describe('Upgrade Flow - Unauthenticated', () => {
    it('redirects to register with plan intent when clicking upgrade', async () => {
      await renderPricingPage(false);

      const trialButtons = screen.getAllByRole('button', { name: /Start Free Trial/i });
      fireEvent.click(trialButtons[0]);

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/register?plan=pro&billing=monthly');
      });
    });

    it('redirects with annual billing when annual is selected', async () => {
      await renderPricingPage(false);

      // Switch to annual
      const buttons = screen.getAllByRole('button');
      const annualButton = buttons.find(btn => btn.textContent?.includes('Annual'));
      if (annualButton) fireEvent.click(annualButton);

      const trialButtons = screen.getAllByRole('button', { name: /Start Free Trial/i });
      fireEvent.click(trialButtons[0]);

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/register?plan=pro&billing=annual');
      });
    });
  });

  describe('Upgrade Flow - Authenticated', () => {
    it('shows Current Plan button for Pro users', async () => {
      await renderPricingPage(true, 'pro');

      // Wait for auth to resolve and check for current plan button
      await waitFor(() => {
        const buttons = screen.getAllByRole('button');
        const currentPlanButton = buttons.find(btn => btn.textContent?.includes('Current Plan'));
        expect(currentPlanButton).toBeTruthy();
      }, { timeout: 3000 });
    });
  });

  describe('Analytics Tracking', () => {
    it('tracks page view on mount', async () => {
      await renderPricingPage();
      const { analytics, Events } = await import('../../lib/analytics');

      expect(analytics.track).toHaveBeenCalledWith(Events.PAGE_VIEWED, { page: 'pricing' });
    });
  });

  describe('Accessibility', () => {
    it('has proper heading hierarchy', async () => {
      const { container } = await renderPricingPage();

      const h1 = container.querySelector('h1');
      expect(h1).toBeInTheDocument();

      const h2Elements = container.querySelectorAll('h2');
      expect(h2Elements.length).toBeGreaterThanOrEqual(2);

      const h3Elements = container.querySelectorAll('h3');
      expect(h3Elements.length).toBeGreaterThanOrEqual(2);
    });

    it('FAQ buttons have accessible names', async () => {
      await renderPricingPage();
      
      const faqButtons = screen.getAllByRole('button');
      const faqQuestionButtons = faqButtons.filter(btn => 
        btn.textContent?.includes('?')
      );
      
      expect(faqQuestionButtons.length).toBeGreaterThan(0);
    });

    it('uses semantic section elements', async () => {
      const { container } = await renderPricingPage();
      const sections = container.querySelectorAll('section');
      expect(sections.length).toBeGreaterThanOrEqual(4);
    });
  });

  describe('Responsive Design', () => {
    it('has responsive grid for pricing cards', async () => {
      const { container } = await renderPricingPage();
      const grid = container.querySelector('.grid.grid-cols-1.md\\:grid-cols-2');
      expect(grid).toBeInTheDocument();
    });

    it('has responsive padding classes', async () => {
      const { container } = await renderPricingPage();
      const responsiveSection = container.querySelector('.pt-16.sm\\:pt-20');
      expect(responsiveSection).toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {
    it('handles pricing fetch gracefully', async () => {
      const { subscriptionsAPI } = await import('../../lib/api');
      vi.mocked(subscriptionsAPI.getPricing).mockRejectedValueOnce(new Error('Network error'));

      // Page should still render even if pricing fetch fails
      await renderPricingPage();
      expect(screen.getByText('Simple, Transparent Pricing')).toBeInTheDocument();
    });
  });
});
