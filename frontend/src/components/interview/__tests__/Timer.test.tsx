import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, act } from '@testing-library/react';
import Timer from '../Timer';

describe('Timer', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('Elapsed Mode (default)', () => {
    it('should render 00:00 when no startTime is provided', () => {
      render(<Timer />);
      expect(screen.getByText('00:00')).toBeInTheDocument();
    });

    it('should display elapsed time correctly', () => {
      const startTime = Date.now() - 65000; // 65 seconds ago (1:05)
      render(<Timer startTime={startTime} />);
      expect(screen.getByText('01:05')).toBeInTheDocument();
    });

    it('should update time every second', () => {
      const startTime = Date.now();
      render(<Timer startTime={startTime} />);

      expect(screen.getByText('00:00')).toBeInTheDocument();

      act(() => {
        vi.advanceTimersByTime(1000);
      });
      expect(screen.getByText('00:01')).toBeInTheDocument();

      act(() => {
        vi.advanceTimersByTime(59000); // Advance to 1 minute
      });
      expect(screen.getByText('01:00')).toBeInTheDocument();
    });

    it('should handle minutes correctly', () => {
      const startTime = Date.now() - 125000; // 2:05
      render(<Timer startTime={startTime} />);
      expect(screen.getByText('02:05')).toBeInTheDocument();
    });

    it('should pad single digit minutes and seconds with zeros', () => {
      const startTime = Date.now() - 9000; // 9 seconds
      render(<Timer startTime={startTime} />);
      expect(screen.getByText('00:09')).toBeInTheDocument();
    });
  });

  describe('Countdown Mode', () => {
    it('should display countdown time correctly', () => {
      const startTime = Date.now() - 10000; // Started 10 seconds ago
      const maxSeconds = 120; // 2 minutes max
      render(<Timer startTime={startTime} variant="countdown" maxSeconds={maxSeconds} />);
      // 120 - 10 = 110 seconds = 1:50
      expect(screen.getByText('01:50')).toBeInTheDocument();
    });

    it('should count down to zero', () => {
      const startTime = Date.now();
      const maxSeconds = 5;
      render(<Timer startTime={startTime} variant="countdown" maxSeconds={maxSeconds} />);

      expect(screen.getByText('00:05')).toBeInTheDocument();

      act(() => {
        vi.advanceTimersByTime(3000);
      });
      expect(screen.getByText('00:02')).toBeInTheDocument();

      act(() => {
        vi.advanceTimersByTime(3000);
      });
      // Should stop at 00:00, not go negative
      expect(screen.getByText('00:00')).toBeInTheDocument();
    });

    it('should not show negative time', () => {
      const startTime = Date.now() - 150000; // Started 150 seconds ago
      const maxSeconds = 120; // 2 minutes max - already expired
      render(<Timer startTime={startTime} variant="countdown" maxSeconds={maxSeconds} />);
      expect(screen.getByText('00:00')).toBeInTheDocument();
    });
  });

  describe('Styling', () => {
    it('should apply custom className', () => {
      render(<Timer className="custom-timer-class" />);
      const timerDiv = screen.getByText('00:00').closest('div');
      expect(timerDiv).toHaveClass('custom-timer-class');
      expect(timerDiv).toHaveClass('timer-display');
    });

    it('should apply timer-display class by default', () => {
      render(<Timer />);
      const timerDiv = screen.getByText('00:00').closest('div');
      expect(timerDiv).toHaveClass('timer-display');
    });
  });

  describe('Cleanup', () => {
    it('should clear interval on unmount', () => {
      const startTime = Date.now();
      const { unmount } = render(<Timer startTime={startTime} />);

      const clearIntervalSpy = vi.spyOn(window, 'clearInterval');
      unmount();

      expect(clearIntervalSpy).toHaveBeenCalled();
      clearIntervalSpy.mockRestore();
    });

    it('should not start interval when no startTime', () => {
      const setIntervalSpy = vi.spyOn(window, 'setInterval');
      render(<Timer />);

      // Should not call setInterval without startTime
      expect(setIntervalSpy).not.toHaveBeenCalled();
      setIntervalSpy.mockRestore();
    });
  });

  describe('Edge Cases', () => {
    it('should handle startTime changes after interval tick', () => {
      const initialStart = Date.now() - 10000;
      const { rerender } = render(<Timer startTime={initialStart} />);
      expect(screen.getByText('00:10')).toBeInTheDocument();

      // Advance timer to trigger an update
      act(() => {
        vi.advanceTimersByTime(1000);
      });

      // Now rerender with a new startTime - the interval callback will pick up new value
      const newStart = Date.now() - 5000;
      rerender(<Timer startTime={newStart} />);

      // After rerender and a tick, should reflect new startTime
      act(() => {
        vi.advanceTimersByTime(1000);
      });

      // Timer should now be around 6 seconds (5s + 1s elapsed during test)
      expect(screen.getByText('00:06')).toBeInTheDocument();
    });

    it('should handle variant change', () => {
      const startTime = Date.now() - 30000;
      const { rerender } = render(<Timer startTime={startTime} variant="elapsed" />);
      expect(screen.getByText('00:30')).toBeInTheDocument();

      // Tick to ensure interval updates after variant change
      rerender(<Timer startTime={startTime} variant="countdown" maxSeconds={60} />);
      act(() => {
        vi.advanceTimersByTime(1000);
      });

      // 60 - 31 = 29 (30 seconds elapsed + 1 second for tick)
      expect(screen.getByText('00:29')).toBeInTheDocument();
    });

    it('should handle large time values', () => {
      const startTime = Date.now() - 3661000; // 1 hour, 1 minute, 1 second
      render(<Timer startTime={startTime} />);
      expect(screen.getByText('61:01')).toBeInTheDocument();
    });
  });
});
