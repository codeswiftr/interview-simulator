import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { act } from 'react';
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

    const renderResult = await act(async () =>
      render(
        <MemoryRouter>
          <AuthProvider>
            <PricingPage />
          </AuthProvider>
        </MemoryRouter>
      )
    );

    await waitFor(() => {
      expect(screen.getByText('Simple, Transparent Pricing')).toBeInTheDocument();
    });

    return renderResult;
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
      // Badge shows "Save XX%" inside the annual toggle button — use getAllByText to handle
      // whitespace variations in the rendered span
      const savingsBadges = screen.getAllByText(/Save/i);
      expect(savingsBadges.length).toBeGreaterThanOrEqual(1);
    });

    it('defaults to monthly billing', async () => {
      await renderPricingPage();
      // Monthly price is $19 (updated from $29)
      expect(screen.getByText('$19')).toBeInTheDocument();
    });

    it('switches to annual pricing when annual is selected', async () => {
      await renderPricingPage();

      const buttons = screen.getAllByRole('button');
      const annualButton = buttons.find(btn => btn.textContent?.includes('Annual'));
      if (annualButton) {
        await act(async () => {
          fireEvent.click(annualButton);
        });
      }

      // Annual price: ANNUAL_MONTHLY_EQUIVALENT = Math.round((149/12)*10)/10 = 12.4
      await waitFor(() => {
        expect(screen.getByText('$12.4')).toBeInTheDocument();
      });
    });

    it('shows annual total when annual is selected', async () => {
      await renderPricingPage();

      const buttons = screen.getAllByRole('button');
      const annualButton = buttons.find(btn => btn.textContent?.includes('Annual'));
      if (annualButton) {
        await act(async () => {
          fireEvent.click(annualButton);
        });
      }

      // Annual total is $149/year (not $290)
      await waitFor(() => {
        expect(screen.getByText(/\$149\/year/i)).toBeInTheDocument();
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
      // Feature text updated in component: "3 AI interviews per month"
      expect(screen.getByText('3 AI interviews per month')).toBeInTheDocument();
      expect(screen.getByText('Basic AI feedback')).toBeInTheDocument();
    });

    it('shows Get Started Free button for unauthenticated users', async () => {
      await renderPricingPage(false);
      // Free plan CTA is now "Start Free" link (with ArrowRight icon)
      const startFreeLinks = screen.getAllByRole('link', { name: /Start Free/i });
      expect(startFreeLinks.length).toBeGreaterThanOrEqual(1);
    });

    it('links to register for new users', async () => {
      await renderPricingPage(false);
      // Free plan "Start Free" link goes to /register
      const startFreeLinks = screen.getAllByRole('link', { name: /Start Free/i });
      const registerLink = startFreeLinks.find(link => link.getAttribute('href') === '/register');
      expect(registerLink).toBeTruthy();
    });
  });

  describe('Pro Plan Card', () => {
    it('displays Pro plan with correct price', async () => {
      await renderPricingPage();
      // Monthly price is $19 (updated from $29)
      expect(screen.getByText('$19')).toBeInTheDocument();
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
      // Feature text updated: "Unlimited AI interviews", "Detailed analytics & scoring"
      expect(screen.getAllByText('Unlimited AI interviews').length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText('Detailed analytics & scoring').length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText('Company-specific questions').length).toBeGreaterThanOrEqual(1);
    });

    it('shows Start Free Trial button for unauthenticated users', async () => {
      await renderPricingPage(false);
      // Pro card CTA is now "Upgrade to Pro" button (not "Start Free Trial")
      const upgradeButtons = screen.getAllByRole('button', { name: /Upgrade to Pro/i });
      expect(upgradeButtons.length).toBeGreaterThanOrEqual(1);
    });

    it('displays Pro plan card with upgrade option', async () => {
      await renderPricingPage(false);
      // Pro plan card shows "Upgrade to Pro" button for unauthenticated users
      const upgradeButtons = screen.getAllByRole('button', { name: /Upgrade to Pro/i });
      expect(upgradeButtons.length).toBeGreaterThanOrEqual(1);
    });
  });

  describe('Enterprise Plan Teaser', () => {
    it('displays Enterprise plan message', async () => {
      await renderPricingPage();
      expect(screen.getByText('Enterprise')).toBeInTheDocument();
    });

    it('displays Contact Sales link', async () => {
      await renderPricingPage();
      // Multiple "Contact Sales" links exist (Team card + Enterprise card)
      const contactLinks = screen.getAllByRole('link', { name: /Contact Sales/i });
      expect(contactLinks.length).toBeGreaterThanOrEqual(1);
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
      // "AI Feedback" appears multiple times (feature card + comparison table)
      expect(screen.getAllByText('AI Feedback').length).toBeGreaterThanOrEqual(1);
      // "Question Bank" is not a comparison row — "Question types" appears in table + mobile view
      expect(screen.getAllByText(/Question types/i).length).toBeGreaterThanOrEqual(1);
    });
  });

  describe('FAQ Section', () => {
    it('displays FAQ heading', async () => {
      await renderPricingPage();
      // FAQ section heading changed from "Frequently Asked Questions" to "Common Questions"
      expect(screen.getByText('Common Questions')).toBeInTheDocument();
    });

    it('displays FAQ questions', async () => {
      await renderPricingPage();
      // FAQ questions updated in component
      expect(screen.getByText(/What's included in the free tier/i)).toBeInTheDocument();
      expect(screen.getByText(/Can I cancel anytime/i)).toBeInTheDocument();
    });

    it('expands FAQ answer when clicked', async () => {
      await renderPricingPage();

      // First FAQ question is "What's included in the free tier?"
      const faqButton = screen.getByRole('button', { name: /What's included in the free tier/i });
      fireEvent.click(faqButton);

      await waitFor(() => {
        // Answer contains text about free tier
        expect(screen.getByText(/3 AI-powered interviews per month/i)).toBeInTheDocument();
      });
    });

    it('collapses FAQ answer when clicked again', async () => {
      await renderPricingPage();

      const faqButton = screen.getByRole('button', { name: /What's included in the free tier/i });

      // Expand
      fireEvent.click(faqButton);
      await waitFor(() => {
        expect(screen.getByText(/3 AI-powered interviews per month/i)).toBeInTheDocument();
      });

      // Collapse
      fireEvent.click(faqButton);
      await waitFor(() => {
        expect(screen.queryByText(/3 AI-powered interviews per month/i)).not.toBeInTheDocument();
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
      // Description updated: "Join 2,000+ engineers..."
      expect(screen.getByText(/Join 2,000\+ engineers/i)).toBeInTheDocument();
    });

    it('shows Try Free Plan link for unauthenticated users', async () => {
      await renderPricingPage(false);
      expect(screen.getByRole('link', { name: /Try Free Plan/i })).toBeInTheDocument();
    });
  });

  describe('Upgrade Flow - Unauthenticated', () => {
    it('redirects to register with plan intent when clicking upgrade', async () => {
      await renderPricingPage(false);

      // Pro card CTA is "Upgrade to Pro" for unauthenticated users (triggers navigate)
      const upgradeButtons = screen.getAllByRole('button', { name: /Upgrade to Pro/i });
      fireEvent.click(upgradeButtons[0]);

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

      const upgradeButtons = screen.getAllByRole('button', { name: /Upgrade to Pro/i });
      fireEvent.click(upgradeButtons[0]);

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
