import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import InterviewHeader from '../InterviewHeader';
import * as InterviewContext from '../../../contexts/InterviewContext';

// Mock the InterviewContext
vi.mock('../../../contexts/InterviewContext', () => ({
  useInterview: vi.fn(),
}));

// Helper to wrap component
const renderWithRouter = (ui: React.ReactElement) => {
  return render(<BrowserRouter>{ui}</BrowserRouter>);
};

describe('InterviewHeader', () => {
  const mockSetShowCoach = vi.fn();
  const mockHandleExit = vi.fn();

  const defaultContextValue = {
    sessionStartTime: Date.now(),
    progress: 40,
    showCoach: false,
    setShowCoach: mockSetShowCoach,
    handleExit: mockHandleExit,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(InterviewContext.useInterview).mockReturnValue(
      defaultContextValue as ReturnType<typeof InterviewContext.useInterview>
    );
  });

  describe('Rendering', () => {
    it('should render the header component', () => {
      renderWithRouter(<InterviewHeader />);

      expect(screen.getByRole('banner')).toBeInTheDocument();
    });

    it('should render the timer', () => {
      renderWithRouter(<InterviewHeader />);

      // Timer displays formatted time like 00:00
      expect(screen.getByText(/\d{2}:\d{2}/)).toBeInTheDocument();
    });

    it('should render progress indicator', () => {
      renderWithRouter(<InterviewHeader />);

      expect(screen.getByText('Progress')).toBeInTheDocument();
      expect(screen.getByText('40%')).toBeInTheDocument();
    });

    it('should render progress bar with correct value', () => {
      renderWithRouter(<InterviewHeader />);

      const progressBar = screen.getByRole('progressbar');
      expect(progressBar).toBeInTheDocument();
      expect(progressBar).toHaveAttribute('aria-valuenow', '40');
      expect(progressBar).toHaveAttribute('aria-valuemin', '0');
      expect(progressBar).toHaveAttribute('aria-valuemax', '100');
    });

    it('should render coach toggle button', () => {
      renderWithRouter(<InterviewHeader />);

      const coachButton = screen.getByRole('button', { name: /AI Coach/i });
      expect(coachButton).toBeInTheDocument();
    });

    it('should render exit button', () => {
      renderWithRouter(<InterviewHeader />);

      const exitButton = screen.getByRole('button', { name: /Exit interview/i });
      expect(exitButton).toBeInTheDocument();
    });
  });

  describe('Progress Display', () => {
    it('should display 0% progress correctly', () => {
      vi.mocked(InterviewContext.useInterview).mockReturnValue({
        ...defaultContextValue,
        progress: 0,
      } as ReturnType<typeof InterviewContext.useInterview>);

      renderWithRouter(<InterviewHeader />);

      expect(screen.getByText('0%')).toBeInTheDocument();
      const progressBar = screen.getByRole('progressbar');
      expect(progressBar).toHaveAttribute('aria-label', 'Interview progress: 0%');
    });

    it('should display 100% progress correctly', () => {
      vi.mocked(InterviewContext.useInterview).mockReturnValue({
        ...defaultContextValue,
        progress: 100,
      } as ReturnType<typeof InterviewContext.useInterview>);

      renderWithRouter(<InterviewHeader />);

      expect(screen.getByText('100%')).toBeInTheDocument();
    });

    it('should round progress to nearest whole number', () => {
      vi.mocked(InterviewContext.useInterview).mockReturnValue({
        ...defaultContextValue,
        progress: 33.7,
      } as ReturnType<typeof InterviewContext.useInterview>);

      renderWithRouter(<InterviewHeader />);

      expect(screen.getByText('34%')).toBeInTheDocument();
    });
  });

  describe('Coach Toggle', () => {
    it('should show "Enable AI Coach" when coach is disabled', () => {
      vi.mocked(InterviewContext.useInterview).mockReturnValue({
        ...defaultContextValue,
        showCoach: false,
      } as ReturnType<typeof InterviewContext.useInterview>);

      renderWithRouter(<InterviewHeader />);

      const coachButton = screen.getByRole('button', { name: /Enable AI Coach/i });
      expect(coachButton).toHaveAttribute('aria-pressed', 'false');
    });

    it('should show "Disable AI Coach" when coach is enabled', () => {
      vi.mocked(InterviewContext.useInterview).mockReturnValue({
        ...defaultContextValue,
        showCoach: true,
      } as ReturnType<typeof InterviewContext.useInterview>);

      renderWithRouter(<InterviewHeader />);

      const coachButton = screen.getByRole('button', { name: /Disable AI Coach/i });
      expect(coachButton).toHaveAttribute('aria-pressed', 'true');
    });

    it('should toggle coach when clicked', async () => {
      const user = userEvent.setup();
      const setShowCoach = vi.fn();

      vi.mocked(InterviewContext.useInterview).mockReturnValue({
        ...defaultContextValue,
        showCoach: false,
        setShowCoach,
      } as ReturnType<typeof InterviewContext.useInterview>);

      renderWithRouter(<InterviewHeader />);

      await user.click(screen.getByRole('button', { name: /Enable AI Coach/i }));
      expect(setShowCoach).toHaveBeenCalledWith(true);
    });

    it('should disable coach when clicked while enabled', async () => {
      const user = userEvent.setup();
      const setShowCoach = vi.fn();

      vi.mocked(InterviewContext.useInterview).mockReturnValue({
        ...defaultContextValue,
        showCoach: true,
        setShowCoach,
      } as ReturnType<typeof InterviewContext.useInterview>);

      renderWithRouter(<InterviewHeader />);

      await user.click(screen.getByRole('button', { name: /Disable AI Coach/i }));
      expect(setShowCoach).toHaveBeenCalledWith(false);
    });

    it('should have active styling when coach is enabled', () => {
      vi.mocked(InterviewContext.useInterview).mockReturnValue({
        ...defaultContextValue,
        showCoach: true,
      } as ReturnType<typeof InterviewContext.useInterview>);

      renderWithRouter(<InterviewHeader />);

      const coachButton = screen.getByRole('button', { name: /Disable AI Coach/i });
      expect(coachButton.className).toContain('bg-electric-blue');
    });
  });

  describe('Exit Button', () => {
    it('should call handleExit when exit button is clicked', async () => {
      const user = userEvent.setup();
      const handleExit = vi.fn();

      vi.mocked(InterviewContext.useInterview).mockReturnValue({
        ...defaultContextValue,
        handleExit,
      } as ReturnType<typeof InterviewContext.useInterview>);

      renderWithRouter(<InterviewHeader />);

      await user.click(screen.getByRole('button', { name: /Exit interview/i }));
      expect(handleExit).toHaveBeenCalledTimes(1);
    });
  });

  describe('Timer', () => {
    it('should pass sessionStartTime to Timer component', () => {
      const startTime = Date.now() - 60000; // 1 minute ago

      vi.mocked(InterviewContext.useInterview).mockReturnValue({
        ...defaultContextValue,
        sessionStartTime: startTime,
      } as ReturnType<typeof InterviewContext.useInterview>);

      renderWithRouter(<InterviewHeader />);

      // Timer should display approximately 01:00
      expect(screen.getByText(/01:0\d/)).toBeInTheDocument();
    });

    it('should handle null sessionStartTime', () => {
      vi.mocked(InterviewContext.useInterview).mockReturnValue({
        ...defaultContextValue,
        sessionStartTime: null,
      } as ReturnType<typeof InterviewContext.useInterview>);

      renderWithRouter(<InterviewHeader />);

      expect(screen.getByText('00:00')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have accessible progress bar', () => {
      renderWithRouter(<InterviewHeader />);

      const progressBar = screen.getByRole('progressbar');
      expect(progressBar).toHaveAttribute('aria-label');
      expect(progressBar).toHaveAttribute('aria-valuenow');
      expect(progressBar).toHaveAttribute('aria-valuemin');
      expect(progressBar).toHaveAttribute('aria-valuemax');
    });

    it('should have proper aria-label on exit button', () => {
      renderWithRouter(<InterviewHeader />);

      expect(screen.getByRole('button', { name: /Exit interview/i })).toBeInTheDocument();
    });

    it('should have proper aria-pressed on coach toggle', () => {
      renderWithRouter(<InterviewHeader />);

      const coachButton = screen.getByRole('button', { name: /AI Coach/i });
      expect(coachButton).toHaveAttribute('aria-pressed');
    });

    it('should have minimum touch target size', () => {
      renderWithRouter(<InterviewHeader />);

      const coachButton = screen.getByRole('button', { name: /AI Coach/i });
      const exitButton = screen.getByRole('button', { name: /Exit interview/i });

      // Verify min-w-[44px] min-h-[44px] classes are present
      expect(coachButton.className).toContain('min-w-[44px]');
      expect(coachButton.className).toContain('min-h-[44px]');
      expect(exitButton.className).toContain('min-w-[44px]');
      expect(exitButton.className).toContain('min-h-[44px]');
    });
  });

  describe('Styling', () => {
    it('should have sticky positioning', () => {
      renderWithRouter(<InterviewHeader />);

      const header = screen.getByRole('banner');
      expect(header.className).toContain('sticky');
      expect(header.className).toContain('top-0');
      expect(header.className).toContain('z-50');
    });

    it('should have backdrop blur effect', () => {
      renderWithRouter(<InterviewHeader />);

      const header = screen.getByRole('banner');
      expect(header.className).toContain('backdrop-blur');
    });
  });
});
