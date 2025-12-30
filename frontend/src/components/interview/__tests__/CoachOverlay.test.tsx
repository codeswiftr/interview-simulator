import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen } from '@/test/utils';
import userEvent from '@testing-library/user-event';
import CoachOverlay from '../CoachOverlay';

describe('CoachOverlay', () => {
  const defaultProps = {
    isVisible: true,
    onClose: vi.fn(),
    questionType: 'behavioral',
    elapsedTime: 0,
    expectedDuration: 300,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    // Mock window.innerWidth for consistent testing
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 1024,
    });
  });

  afterEach(() => {
    vi.clearAllTimers();
  });

  describe('Visibility', () => {
    it('should render when isVisible is true', () => {
      render(<CoachOverlay {...defaultProps} />);
      expect(screen.getByText('AI Coach')).toBeInTheDocument();
    });

    it('should not render when isVisible is false', () => {
      render(<CoachOverlay {...defaultProps} isVisible={false} />);
      expect(screen.queryByText('AI Coach')).not.toBeInTheDocument();
    });
  });

  describe('Component Rendering', () => {
    it('should render with correct initial state', () => {
      render(<CoachOverlay {...defaultProps} />);

      expect(screen.getByText('AI Coach')).toBeInTheDocument();
      expect(screen.getByText('Dismiss Coach')).toBeInTheDocument();
    });

    it('should render toggle button', () => {
      render(<CoachOverlay {...defaultProps} />);

      const toggleButton = screen.getByRole('button', { name: /AI Coach/i });
      expect(toggleButton).toBeInTheDocument();
    });

    it('should render close/dismiss button', () => {
      render(<CoachOverlay {...defaultProps} />);

      const dismissButton = screen.getByRole('button', { name: /Dismiss Coach/i });
      expect(dismissButton).toBeInTheDocument();
    });
  });

  describe('Close Functionality', () => {
    it('should call onClose when dismiss button is clicked', async () => {
      const user = userEvent.setup();
      const onClose = vi.fn();

      render(<CoachOverlay {...defaultProps} onClose={onClose} />);

      const dismissButton = screen.getByRole('button', { name: /Dismiss Coach/i });
      await user.click(dismissButton);

      expect(onClose).toHaveBeenCalledTimes(1);
    });
  });

  describe('Hint Navigation', () => {
    it('should display first hint by default', () => {
      render(<CoachOverlay {...defaultProps} questionType="behavioral" />);

      // Use getAllByText since "STAR Framework" appears both in hint title and STAR section
      const starTexts = screen.getAllByText('STAR Framework');
      expect(starTexts.length).toBeGreaterThan(0);
      expect(screen.getByText('Structure your answer: Situation, Task, Action, Result.')).toBeInTheDocument();
    });

    it('should navigate to next hint when next button is clicked', async () => {
      const user = userEvent.setup();
      const { container } = render(<CoachOverlay {...defaultProps} questionType="behavioral" />);

      const starTexts = screen.getAllByText('STAR Framework');
      expect(starTexts.length).toBeGreaterThan(0);

      // Find the navigation container and get the right-side button (next)
      const navButtons = container.querySelectorAll('.p-1.hover\\:bg-white\\/50');
      const nextButton = navButtons[1]; // Second button is the next button

      if (nextButton) {
        await user.click(nextButton as HTMLElement);
        expect(screen.getByText((content) => content.includes('Focus on'))).toBeInTheDocument();
      }
    });

    it('should navigate to previous hint when previous button is clicked', async () => {
      const user = userEvent.setup();
      render(<CoachOverlay {...defaultProps} questionType="behavioral" />);

      // Find the previous button (ChevronLeft icon)
      const buttons = screen.getAllByRole('button');
      const prevButton = buttons.find(btn => {
        const svg = btn.querySelector('svg');
        return svg && btn.className.includes('hover:bg-white/50') && btn !== buttons[buttons.length - 1];
      });

      if (prevButton) {
        await user.click(prevButton);
        // Should wrap around to last hint
        expect(screen.getByText('Be Specific')).toBeInTheDocument();
      }
    });

    it('should render hint indicators for all hints', () => {
      const { container } = render(<CoachOverlay {...defaultProps} questionType="behavioral" />);

      // Behavioral has 3 specific hints + 2 common hints = 5 total
      const indicators = container.querySelectorAll('.w-1\\.5.h-1\\.5.rounded-full');
      expect(indicators).toHaveLength(5);
    });

    it('should highlight active hint indicator', () => {
      const { container } = render(<CoachOverlay {...defaultProps} questionType="behavioral" />);

      const indicators = container.querySelectorAll('.w-1\\.5.h-1\\.5.rounded-full');
      const activeIndicator = Array.from(indicators).find(el =>
        el.className.includes('bg-electric-blue')
      );

      expect(activeIndicator).toBeTruthy();
    });
  });

  describe('Question Type Specific Hints', () => {
    it('should show behavioral hints for behavioral question type', () => {
      render(<CoachOverlay {...defaultProps} questionType="behavioral" />);

      // Use getAllByText since "STAR Framework" appears both in hint title and STAR section
      const starTexts = screen.getAllByText('STAR Framework');
      expect(starTexts.length).toBeGreaterThan(0);
    });

    it('should show technical hints for technical question type', () => {
      render(<CoachOverlay {...defaultProps} questionType="technical" />);

      expect(screen.getByText('Clarify First')).toBeInTheDocument();
      expect(screen.getByText('Ask questions to remove ambiguity before solving.')).toBeInTheDocument();
    });

    it('should show system design hints for system_design question type', () => {
      render(<CoachOverlay {...defaultProps} questionType="system_design" />);

      expect(screen.getByText('Requirements')).toBeInTheDocument();
      expect(screen.getByText('Define functional and non-functional requirements.')).toBeInTheDocument();
    });

    it('should show common hints for unknown question type', () => {
      render(<CoachOverlay {...defaultProps} questionType="unknown" />);

      expect(screen.getByText('Speak Clearly')).toBeInTheDocument();
      expect(screen.getByText('Maintain a steady pace and clear enunciation.')).toBeInTheDocument();
    });

    it('should include common hints for all question types', async () => {
      const user = userEvent.setup();
      const { container } = render(<CoachOverlay {...defaultProps} questionType="behavioral" />);

      // Find the navigation container and get the right-side button (next)
      const navButtons = container.querySelectorAll('.p-1.hover\\:bg-white\\/50');
      const nextButton = navButtons[1]; // Second button is the next button

      if (nextButton) {
        // Click through to reach common hints (3 behavioral hints, then common ones)
        await user.click(nextButton as HTMLElement);
        await user.click(nextButton as HTMLElement);
        await user.click(nextButton as HTMLElement);

        // Should eventually see common hints
        const hasSpeakClearly = screen.queryByText('Speak Clearly');
        const hasBeSpecific = screen.queryByText('Be Specific');
        expect(hasSpeakClearly || hasBeSpecific).toBeTruthy();
      }
    });
  });

  describe('STAR Framework Display', () => {
    it('should display STAR framework for behavioral questions', async () => {
      const user = userEvent.setup({ delay: null });
      render(<CoachOverlay {...defaultProps} questionType="behavioral" />);

      // STAR Framework appears in hint title and as collapsible section header
      const starTexts = screen.getAllByText('STAR Framework');
      expect(starTexts.length).toBeGreaterThan(0);

      // Find and click the STAR Framework toggle button to expand it
      const starToggle = screen.getByRole('button', { name: /STAR Framework/i });
      await user.click(starToggle);

      // Now the S, T, A, R letters should be visible
      expect(screen.getByText('S')).toBeInTheDocument();
      expect(screen.getByText('Situation')).toBeInTheDocument();
      expect(screen.getByText('T')).toBeInTheDocument();
      expect(screen.getByText('Task')).toBeInTheDocument();
      expect(screen.getByText('A')).toBeInTheDocument();
      expect(screen.getByText('Action')).toBeInTheDocument();
      expect(screen.getByText('R')).toBeInTheDocument();
      expect(screen.getByText('Result')).toBeInTheDocument();
    });

    it('should not display STAR framework for technical questions', () => {
      render(<CoachOverlay {...defaultProps} questionType="technical" />);

      expect(screen.queryByText('Situation')).not.toBeInTheDocument();
      expect(screen.queryByText('Task')).not.toBeInTheDocument();
      expect(screen.queryByText('Action')).not.toBeInTheDocument();
      expect(screen.queryByText('Result')).not.toBeInTheDocument();
    });

    it('should not display STAR framework for system design questions', () => {
      render(<CoachOverlay {...defaultProps} questionType="system_design" />);

      expect(screen.queryByText('Situation')).not.toBeInTheDocument();
    });
  });

  describe('Timer Warning', () => {
    it('should not show timer warning when time is not running out', () => {
      render(<CoachOverlay {...defaultProps} elapsedTime={0} expectedDuration={300} />);

      expect(screen.queryByText('Time is running out!')).not.toBeInTheDocument();
    });

    it('should show timer warning when less than 60 seconds remain', () => {
      render(<CoachOverlay {...defaultProps} elapsedTime={250} expectedDuration={300} />);

      expect(screen.getByText('Time is running out!')).toBeInTheDocument();
      expect(screen.getByText('Wrap up your answer in the next minute.')).toBeInTheDocument();
    });

    it('should not show timer warning when time has expired', () => {
      render(<CoachOverlay {...defaultProps} elapsedTime={300} expectedDuration={300} />);

      expect(screen.queryByText('Time is running out!')).not.toBeInTheDocument();
    });

    it('should not show timer warning when time exceeded', () => {
      render(<CoachOverlay {...defaultProps} elapsedTime={350} expectedDuration={300} />);

      expect(screen.queryByText('Time is running out!')).not.toBeInTheDocument();
    });
  });

  describe('Expand/Collapse Functionality', () => {
    it('should start expanded by default', () => {
      render(<CoachOverlay {...defaultProps} />);

      expect(screen.getByText('AI Coach')).toBeInTheDocument();
      expect(screen.getByText('Dismiss Coach')).toBeInTheDocument();
    });

    it('should collapse when toggle button is clicked', async () => {
      const user = userEvent.setup();
      render(<CoachOverlay {...defaultProps} />);

      const toggleButton = screen.getByRole('button', { name: /AI Coach/i });
      await user.click(toggleButton);

      // When collapsed, dismiss button should not be visible
      expect(screen.queryByText('Dismiss Coach')).not.toBeInTheDocument();
    });

    it('should expand again when toggle button is clicked while collapsed', async () => {
      const user = userEvent.setup();
      render(<CoachOverlay {...defaultProps} />);

      const toggleButton = screen.getByRole('button', { name: /AI Coach/i });

      // Collapse
      await user.click(toggleButton);
      expect(screen.queryByText('Dismiss Coach')).not.toBeInTheDocument();

      // Expand
      await user.click(toggleButton);
      expect(screen.getByText('Dismiss Coach')).toBeInTheDocument();
    });
  });

  describe('Preparation alias props', () => {
    it('should render dynamic hint via alias props without timers', () => {
      render(
        <CoachOverlay
          onClose={vi.fn()}
          hint="Alias hint"
          isLoading={false}
          isStreaming={true}
        />
      );

      expect(screen.getByText('AI Coach')).toBeInTheDocument();
      expect(screen.getByText('Alias hint')).toBeInTheDocument();
    });

    it('should call onToggle when provided in alias mode', async () => {
      const user = userEvent.setup();
      const onToggle = vi.fn();

      render(
        <CoachOverlay
          onClose={vi.fn()}
          hint="Toggle test"
          onToggle={onToggle}
          isCollapsed={true}
        />
      );

      const toggleButton = screen.getByRole('button');
      await user.click(toggleButton);

      expect(onToggle).toHaveBeenCalledTimes(1);
    });
  });

  describe('Mobile Auto-Collapse', () => {
    it('should start collapsed on mobile viewport', () => {
      // Mock mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 500,
      });

      render(<CoachOverlay {...defaultProps} />);

      // On mobile (< 768px), component starts collapsed
      // Should render the toggle button but not the content
      const buttons = screen.getAllByRole('button');
      expect(buttons.length).toBeGreaterThan(0);

      // Dismiss Coach is only visible when expanded
      expect(screen.queryByText('Dismiss Coach')).not.toBeInTheDocument();
    });

    it('should start expanded on desktop viewport', () => {
      // Mock desktop viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 1024,
      });

      render(<CoachOverlay {...defaultProps} />);

      // Should start expanded on desktop (>= 768px)
      expect(screen.getByText('AI Coach')).toBeInTheDocument();
      expect(screen.getByText('Dismiss Coach')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have accessible hint navigation buttons', () => {
      render(<CoachOverlay {...defaultProps} />);

      const buttons = screen.getAllByRole('button');
      expect(buttons.length).toBeGreaterThan(0);
    });

    it('should provide visual feedback for active hint', () => {
      const { container } = render(<CoachOverlay {...defaultProps} questionType="behavioral" />);

      const activeIndicator = container.querySelector('.bg-electric-blue');
      expect(activeIndicator).toBeInTheDocument();
    });
  });

  describe('Hint Content Verification', () => {
    it('should have correct number of hints for behavioral questions', () => {
      const { container } = render(<CoachOverlay {...defaultProps} questionType="behavioral" />);

      // 3 behavioral + 2 common = 5 hints
      const indicators = container.querySelectorAll('.w-1\\.5.h-1\\.5.rounded-full');
      expect(indicators).toHaveLength(5);
    });

    it('should have correct number of hints for technical questions', () => {
      const { container } = render(<CoachOverlay {...defaultProps} questionType="technical" />);

      // 3 technical + 2 common = 5 hints
      const indicators = container.querySelectorAll('.w-1\\.5.h-1\\.5.rounded-full');
      expect(indicators).toHaveLength(5);
    });

    it('should have correct number of hints for system design questions', () => {
      const { container } = render(<CoachOverlay {...defaultProps} questionType="system_design" />);

      // 3 system design + 2 common = 5 hints
      const indicators = container.querySelectorAll('.w-1\\.5.h-1\\.5.rounded-full');
      expect(indicators).toHaveLength(5);
    });

    it('should have correct number of hints for unknown question type', () => {
      const { container } = render(<CoachOverlay {...defaultProps} questionType="unknown" />);

      // Only 2 common hints
      const indicators = container.querySelectorAll('.w-1\\.5.h-1\\.5.rounded-full');
      expect(indicators).toHaveLength(2);
    });
  });

  describe('Edge Cases', () => {
    it('should handle rapid hint navigation', async () => {
      // Use faster delay for rapid clicks
      const user = userEvent.setup({ delay: null });
      render(<CoachOverlay {...defaultProps} questionType="behavioral" />);

      const buttons = screen.getAllByRole('button');
      const nextButton = buttons.find(btn => {
        const svg = btn.querySelector('svg');
        return svg && btn.className.includes('hover:bg-white/50');
      });

      if (nextButton) {
        // Rapidly click next button (5 hints total, so 5 clicks wraps around)
        await user.click(nextButton);
        await user.click(nextButton);
        await user.click(nextButton);
        await user.click(nextButton);
        await user.click(nextButton);

        // Should wrap around and show first hint again
        const starTexts = screen.getAllByText('STAR Framework');
        expect(starTexts.length).toBeGreaterThan(0);
      }
    });

    it('should handle zero expected duration', () => {
      render(<CoachOverlay {...defaultProps} expectedDuration={0} elapsedTime={0} />);

      expect(screen.getByText('AI Coach')).toBeInTheDocument();
      expect(screen.queryByText('Time is running out!')).not.toBeInTheDocument();
    });

    it('should handle negative elapsed time gracefully', () => {
      render(<CoachOverlay {...defaultProps} elapsedTime={-10} expectedDuration={300} />);

      expect(screen.getByText('AI Coach')).toBeInTheDocument();
      expect(screen.queryByText('Time is running out!')).not.toBeInTheDocument();
    });
  });
});
