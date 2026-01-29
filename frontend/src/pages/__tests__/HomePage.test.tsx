import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import HomePage from '../HomePage';
import { AuthProvider } from '../../hooks/useAuth';

// Mock the authAPI module
vi.mock('../../lib/api', () => ({
  authAPI: {
    getCurrentUser: vi.fn(),
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
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
    USER_LOGGED_IN: 'user_logged_in',
    USER_REGISTERED: 'user_registered',
    USER_LOGGED_OUT: 'user_logged_out',
  },
}));

// Mock the utm module
vi.mock('../../lib/utm', () => ({
  getStoredUTM: vi.fn(() => ({})),
}));

describe('HomePage', () => {
  // Helper function to render HomePage with routing and auth context
  const renderHomePage = async (isAuthenticated = false) => {
    // Mock localStorage based on authentication status
    if (isAuthenticated) {
      localStorage.setItem('access_token', 'mock-token');
      const { authAPI } = await import('../../lib/api');
      vi.mocked(authAPI.getCurrentUser).mockResolvedValue({
        data: {
          id: 1,
          email: 'test@example.com',
          full_name: 'Test User',
          subscription_tier: 'free',
          created_at: new Date().toISOString(),
        },
      } as any);
    } else {
      localStorage.clear();
    }

    return render(
      <MemoryRouter>
        <AuthProvider>
          <HomePage />
        </AuthProvider>
      </MemoryRouter>
    );
  };

  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  describe('Basic Rendering', () => {
    it('renders the page without crashing', async () => {
      const { container } = await renderHomePage();
      // Check for either role="main" or the main container class
      const mainContent = screen.queryByRole('main') || container.querySelector('.min-h-screen');
      expect(mainContent).toBeInTheDocument();
    });

    it('has proper background styling', async () => {
      const { container } = await renderHomePage();
      const mainDiv = container.querySelector('.min-h-screen');
      expect(mainDiv).toBeInTheDocument();
    });
  });

  describe('Hero Section Content', () => {
    it('displays the main headline with AI-powered gradient text', async () => {
      await renderHomePage();

      // Check for the headline text
      expect(screen.getByText(/Master Your Interview Skills with/i)).toBeInTheDocument();
      expect(screen.getByText(/Real-Time AI Feedback/i)).toBeInTheDocument();
    });

    it('displays the AI-Powered Interview Coach badge', async () => {
      await renderHomePage();
      expect(screen.getByText('AI-Powered Interview Coach')).toBeInTheDocument();
    });

    it('displays the hero description text', async () => {
      await renderHomePage();
      expect(
        screen.getByText(/Simulate real interview scenarios, record your answers, and get instant, actionable feedback/i)
      ).toBeInTheDocument();
    });

    it('displays the hero illustration image', async () => {
      await renderHomePage();
      const heroImage = screen.getByAltText('Dashboard Preview');
      expect(heroImage).toBeInTheDocument();
      expect(heroImage).toHaveAttribute('src', '/images/hero-illustration.png');
      expect(heroImage).toHaveAttribute('loading', 'eager');
      expect(heroImage).toHaveAttribute('fetchPriority', 'high');
    });

    it('displays the audio score floating element on desktop', async () => {
      await renderHomePage();
      expect(screen.getByText('Audio Score')).toBeInTheDocument();
      expect(screen.getByText('92/100')).toBeInTheDocument();
    });

    it('has proper heading hierarchy with h1 element', async () => {
      const { container } = await renderHomePage();
      const heading = container.querySelector('h1');
      expect(heading).toBeInTheDocument();
      expect(heading).toHaveClass('text-3xl');
    });
  });

  describe('Feature Cards Display', () => {
    it('renders all four feature cards', async () => {
      await renderHomePage();

      expect(screen.getByText('Voice Recording')).toBeInTheDocument();
      expect(screen.getByText('AI Feedback')).toBeInTheDocument();
      expect(screen.getByText('Track Progress')).toBeInTheDocument();
      expect(screen.getByText('Question Bank')).toBeInTheDocument();
    });

    it('displays Voice Recording feature with correct description', async () => {
      await renderHomePage();

      expect(screen.getByText('Voice Recording')).toBeInTheDocument();
      expect(
        screen.getByText(/Practice your answers out loud. Our advanced audio capture simulates real interview conditions./i)
      ).toBeInTheDocument();
    });

    it('displays AI Feedback feature with correct description', async () => {
      await renderHomePage();

      expect(screen.getByText('AI Feedback')).toBeInTheDocument();
      expect(
        screen.getByText(/Get instant, detailed analysis of your content, delivery, and structure with actionable tips./i)
      ).toBeInTheDocument();
    });

    it('displays Track Progress feature with correct description', async () => {
      await renderHomePage();

      expect(screen.getByText('Track Progress')).toBeInTheDocument();
      expect(
        screen.getByText(/Monitor your improvement over time with detailed analytics and performance metrics./i)
      ).toBeInTheDocument();
    });

    it('displays Question Bank feature with correct description', async () => {
      await renderHomePage();

      expect(screen.getByText('Question Bank')).toBeInTheDocument();
      expect(
        screen.getByText(/Access hundreds of real interview questions across multiple categories and difficulty levels./i)
      ).toBeInTheDocument();
    });

    it('renders feature cards with hover effects', async () => {
      const { container } = await renderHomePage();
      // Feature cards should have hover effects and transitions
      const featureCards = container.querySelectorAll('.hover\\:translate-y-\\[-4px\\]');
      expect(featureCards.length).toBe(4);
    });

    it('displays feature section heading', async () => {
      await renderHomePage();
      expect(screen.getByText('Everything you need to excel')).toBeInTheDocument();
    });

    it('displays feature section description', async () => {
      await renderHomePage();
      expect(
        screen.getByText(/Our platform provides comprehensive tools to help you prepare for behavioral, technical, and system design interviews./i)
      ).toBeInTheDocument();
    });

    it('renders feature cards in a grid layout', async () => {
      const { container } = await renderHomePage();
      const gridContainer = container.querySelector('.grid.md\\:grid-cols-2.lg\\:grid-cols-4');
      expect(gridContainer).toBeInTheDocument();
    });
  });

  describe('CTA Buttons - Unauthenticated User', () => {
    it('displays "Start Practicing Free" button when not authenticated', async () => {
      await renderHomePage(false);

      const startButton = screen.getByRole('link', { name: /Start Practicing Free/i });
      expect(startButton).toBeInTheDocument();
      expect(startButton).toHaveAttribute('href', '/register');
    });

    it('displays "Login" button when not authenticated', async () => {
      await renderHomePage(false);

      const loginButton = screen.getByRole('link', { name: /^Login$/i });
      expect(loginButton).toBeInTheDocument();
      expect(loginButton).toHaveAttribute('href', '/login');
    });

    it('displays "Get Started Now" button in CTA section when not authenticated', async () => {
      await renderHomePage(false);

      const getStartedButton = screen.getByRole('link', { name: /Get Started Now/i });
      expect(getStartedButton).toBeInTheDocument();
      expect(getStartedButton).toHaveAttribute('href', '/register');
    });

    it('hero CTA buttons have proper styling classes', async () => {
      await renderHomePage(false);

      const startButton = screen.getByRole('link', { name: /Start Practicing Free/i });
      expect(startButton).toHaveClass('btn-primary');

      const loginButton = screen.getByRole('link', { name: /^Login$/i });
      expect(loginButton).toHaveClass('btn-secondary');
    });

    it('displays arrow icon in Start Practicing button', async () => {
      await renderHomePage(false);
      const startButton = screen.getByRole('link', { name: /Start Practicing Free/i });
      // Check for svg icon (lucide-react ArrowRight)
      const svg = startButton.querySelector('svg');
      expect(svg).toBeInTheDocument();
    });
  });

  describe('CTA Buttons - Authenticated User', () => {
    it('displays "Go to Dashboard" button in hero when authenticated', async () => {
      await renderHomePage(true);

      // Wait for auth state to update - there are two buttons with this text (hero + CTA)
      const dashboardButtons = await screen.findAllByRole('link', { name: /Go to Dashboard/i });
      expect(dashboardButtons.length).toBeGreaterThanOrEqual(1);
      expect(dashboardButtons[0]).toHaveAttribute('href', '/dashboard');
    });

    it('does not display "Start Practicing Free" when authenticated', async () => {
      await renderHomePage(true);

      // Wait for auth state to update
      await screen.findAllByRole('link', { name: /Go to Dashboard/i });

      // Should not have the register button
      expect(screen.queryByRole('link', { name: /Start Practicing Free/i })).not.toBeInTheDocument();
    });

    it('does not display "Login" button when authenticated', async () => {
      await renderHomePage(true);

      // Wait for auth state to update
      await screen.findAllByRole('link', { name: /Go to Dashboard/i });

      // Should not have the login button
      expect(screen.queryByRole('link', { name: /^Login$/i })).not.toBeInTheDocument();
    });

    it('displays dashboard button in CTA section when authenticated', async () => {
      await renderHomePage(true);

      // Wait for auth state to update
      const dashboardButtons = await screen.findAllByRole('link', { name: /Go to Dashboard/i });
      // Should have dashboard button in both hero and CTA sections
      expect(dashboardButtons.length).toBeGreaterThanOrEqual(1);
    });
  });

  describe('CTA Section', () => {
    it('displays CTA section heading', async () => {
      await renderHomePage();
      expect(screen.getByText('Ready to Ace Your Next Interview?')).toBeInTheDocument();
    });

    it('displays CTA section description', async () => {
      await renderHomePage();
      expect(
        screen.getByText(/Join thousands of engineers who have improved their interview skills with our AI-powered simulator./i)
      ).toBeInTheDocument();
    });

    it('has dark background styling in CTA section', async () => {
      const { container } = await renderHomePage();
      // Check for the CTA section with charcoal background
      const ctaSection = container.querySelector('.bg-charcoal');
      expect(ctaSection).toBeInTheDocument();
    });
  });

  describe('Responsive Layout Classes', () => {
    it('has responsive padding classes in hero section', async () => {
      const { container } = await renderHomePage();
      const heroSection = container.querySelector('.pt-16');
      expect(heroSection).toBeInTheDocument();
      expect(heroSection).toHaveClass('lg:pt-48');
    });

    it('has responsive flex direction for CTA buttons', async () => {
      const { container } = await renderHomePage();
      const buttonContainer = container.querySelector('.flex.flex-col');
      expect(buttonContainer).toBeInTheDocument();
    });

    it('has responsive grid for feature cards', async () => {
      const { container } = await renderHomePage();
      const featureGrid = container.querySelector('.grid');
      expect(featureGrid).toBeInTheDocument();
      expect(featureGrid).toHaveClass('md:grid-cols-2');
    });

    it('has responsive max-width for hero content', async () => {
      const { container } = await renderHomePage();
      const heroContent = container.querySelector('.max-w-4xl');
      expect(heroContent).toBeInTheDocument();
    });

    it('has responsive max-width for hero visual', async () => {
      const { container } = await renderHomePage();
      const heroVisual = container.querySelector('.max-w-5xl');
      expect(heroVisual).toBeInTheDocument();
    });

    it('floating audio score element is hidden on mobile', async () => {
      const { container } = await renderHomePage();
      const floatingElement = container.querySelector('.hidden');
      expect(floatingElement).toBeInTheDocument();
      expect(floatingElement).toHaveClass('sm:block');
    });
  });

  describe('Animation Classes', () => {
    it('has fade-in animation on badge', async () => {
      const { container } = await renderHomePage();
      const badge = container.querySelector('.animate-fade-in');
      expect(badge).toBeInTheDocument();
    });

    it('has slide-up animations on hero content', async () => {
      const { container } = await renderHomePage();
      const slideUpElements = container.querySelectorAll('.animate-slide-up');
      expect(slideUpElements.length).toBe(3); // h1, p, and button container
    });

    it('has scale-in animation on hero visual', async () => {
      const { container } = await renderHomePage();
      const scaleInElement = container.querySelector('.animate-scale-in');
      expect(scaleInElement).toBeInTheDocument();
    });

    it('has pulse-glow animations on background elements', async () => {
      const { container } = await renderHomePage();
      const pulseElements = container.querySelectorAll('.animate-pulse-glow');
      expect(pulseElements.length).toBe(2); // Two background elements
    });

    it('has float animation on audio score element', async () => {
      const { container } = await renderHomePage();
      const floatElement = container.querySelector('.animate-float');
      expect(floatElement).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has proper alt text for hero image', async () => {
      await renderHomePage();
      const heroImage = screen.getByAltText('Dashboard Preview');
      expect(heroImage).toBeInTheDocument();
    });

    it('links have accessible names', async () => {
      await renderHomePage(false);

      expect(screen.getByRole('link', { name: /Start Practicing Free/i })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /^Login$/i })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /Get Started Now/i })).toBeInTheDocument();
    });

    it('has semantic heading hierarchy', async () => {
      const { container } = await renderHomePage();

      // Should have h1 for main heading
      const h1 = container.querySelector('h1');
      expect(h1).toBeInTheDocument();

      // Should have h2 for section headings
      const h2Elements = container.querySelectorAll('h2');
      expect(h2Elements.length).toBe(3); // Features, Pricing, and CTA headings

      // Should have h3 for feature card headings
      const h3Elements = container.querySelectorAll('h3');
      expect(h3Elements.length).toBe(6); // Four feature cards + two pricing cards
    });

    it('sections use semantic HTML5 section tags', async () => {
      const { container } = await renderHomePage();
      const sections = container.querySelectorAll('section');
      expect(sections.length).toBe(4); // Hero, Features, Pricing, CTA
    });
  });

  describe('Theme Support', () => {
    it('has theme-aware background classes', async () => {
      const { container } = await renderHomePage();

      // Check for bg-surface-primary which is theme-aware
      const surfaceElements = container.querySelector('.bg-surface-primary');
      expect(surfaceElements).toBeInTheDocument();
    });

    it('has theme-aware text color classes', async () => {
      const { container } = await renderHomePage();

      // Check for text-text-primary and text-text-secondary classes
      const textPrimaryElements = container.querySelectorAll('.text-text-primary');
      const textSecondaryElements = container.querySelectorAll('.text-text-secondary');

      expect(textPrimaryElements.length).toBeGreaterThan(0);
      expect(textSecondaryElements.length).toBeGreaterThan(0);
    });
  });
});
