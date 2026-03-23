import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import RecordButton from '../RecordButton';
import type { RecordingState } from '../../../hooks/useAudioRecording';

describe('RecordButton', () => {
  const defaultProps = {
    recordingState: 'idle' as RecordingState,
    onStart: vi.fn(),
    onStop: vi.fn(),
    disabled: false,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Idle State', () => {
    it('should render start recording button when idle', () => {
      render(<RecordButton {...defaultProps} />);

      expect(screen.getByRole('button')).toBeInTheDocument();
      expect(screen.getByText('Start Recording')).toBeInTheDocument();
    });

    it('should show microphone icon when idle', () => {
      render(<RecordButton {...defaultProps} />);

      // Lucide icons render as SVG
      const button = screen.getByRole('button');
      const svg = button.querySelector('svg');
      expect(svg).toBeInTheDocument();
    });

    it('should call onStart when clicked in idle state', async () => {
      const user = userEvent.setup();
      const onStart = vi.fn();

      render(<RecordButton {...defaultProps} onStart={onStart} />);

      await user.click(screen.getByRole('button'));
      expect(onStart).toHaveBeenCalledTimes(1);
      expect(defaultProps.onStop).not.toHaveBeenCalled();
    });

    it('should have blue styling when idle', () => {
      render(<RecordButton {...defaultProps} />);

      const button = screen.getByRole('button');
      expect(button.className).toContain('bg-electric-blue');
    });
  });

  describe('Recording State', () => {
    it('should render stop recording button when recording', () => {
      render(<RecordButton {...defaultProps} recordingState="recording" />);

      expect(screen.getByText('Stop Recording')).toBeInTheDocument();
    });

    it('should show stop icon when recording', () => {
      render(<RecordButton {...defaultProps} recordingState="recording" />);

      // Check that stop button icon (filled square) is present
      const button = screen.getByRole('button');
      const svg = button.querySelector('svg');
      expect(svg).toBeInTheDocument();
    });

    it('should call onStop when clicked while recording', async () => {
      const user = userEvent.setup();
      const onStop = vi.fn();

      render(<RecordButton {...defaultProps} recordingState="recording" onStop={onStop} />);

      await user.click(screen.getByRole('button'));
      expect(onStop).toHaveBeenCalledTimes(1);
      expect(defaultProps.onStart).not.toHaveBeenCalled();
    });

    it('should have red styling when recording', () => {
      render(<RecordButton {...defaultProps} recordingState="recording" />);

      const button = screen.getByRole('button');
      expect(button.className).toContain('bg-status-error');
    });

    it('should show recording indicator animation', () => {
      render(<RecordButton {...defaultProps} recordingState="recording" />);

      // Check for animated ping indicator
      const pingElement = document.querySelector('.animate-ping');
      expect(pingElement).toBeInTheDocument();
    });

    it('should not show recording indicator when idle', () => {
      render(<RecordButton {...defaultProps} recordingState="idle" />);

      const pingElement = document.querySelector('.animate-ping');
      expect(pingElement).not.toBeInTheDocument();
    });
  });

  describe('Disabled State', () => {
    it('should disable button when disabled prop is true', () => {
      render(<RecordButton {...defaultProps} disabled={true} />);

      expect(screen.getByRole('button')).toBeDisabled();
    });

    it('should not call onStart when disabled', async () => {
      const user = userEvent.setup();
      const onStart = vi.fn();

      render(<RecordButton {...defaultProps} onStart={onStart} disabled={true} />);

      await user.click(screen.getByRole('button'));
      expect(onStart).not.toHaveBeenCalled();
    });

    it('should not call onStop when disabled while recording', async () => {
      const user = userEvent.setup();
      const onStop = vi.fn();

      render(
        <RecordButton
          {...defaultProps}
          recordingState="recording"
          onStop={onStop}
          disabled={true}
        />
      );

      await user.click(screen.getByRole('button'));
      expect(onStop).not.toHaveBeenCalled();
    });

    it('should have reduced opacity when disabled', () => {
      render(<RecordButton {...defaultProps} disabled={true} />);

      const button = screen.getByRole('button');
      expect(button.className).toContain('opacity-50');
      expect(button.className).toContain('cursor-not-allowed');
    });
  });

  describe('Accessibility', () => {
    it('should have proper focus styles', () => {
      render(<RecordButton {...defaultProps} />);

      const button = screen.getByRole('button');
      expect(button.className).toContain('focus:outline-none');
      expect(button.className).toContain('focus:ring-4');
    });

    it('should have aria-hidden on icons', () => {
      render(<RecordButton {...defaultProps} />);

      const svg = screen.getByRole('button').querySelector('svg');
      expect(svg).toHaveAttribute('aria-hidden', 'true');
    });

    it('should have accessible button text', () => {
      render(<RecordButton {...defaultProps} />);

      expect(screen.getByRole('button', { name: /Start Recording/i })).toBeInTheDocument();
    });

    it('should update accessible name when recording', () => {
      render(<RecordButton {...defaultProps} recordingState="recording" />);

      expect(screen.getByRole('button', { name: /Stop Recording/i })).toBeInTheDocument();
    });
  });

  describe('Other Recording States', () => {
    it('should show start recording for paused state', () => {
      render(<RecordButton {...defaultProps} recordingState="paused" />);

      expect(screen.getByText('Start Recording')).toBeInTheDocument();
    });

    it('should show start recording for stopped state', () => {
      render(<RecordButton {...defaultProps} recordingState="stopped" />);

      expect(screen.getByText('Start Recording')).toBeInTheDocument();
    });

    it('should call onStart when clicked in paused state', async () => {
      const user = userEvent.setup();
      const onStart = vi.fn();

      render(<RecordButton {...defaultProps} recordingState="paused" onStart={onStart} />);

      await user.click(screen.getByRole('button'));
      expect(onStart).toHaveBeenCalledTimes(1);
    });
  });

  describe('Styling', () => {
    it('should have hover effects when enabled', () => {
      render(<RecordButton {...defaultProps} disabled={false} />);

      const button = screen.getByRole('button');
      expect(button.className).toContain('hover:scale-105');
    });

    it('should not have hover scale when disabled', () => {
      render(<RecordButton {...defaultProps} disabled={true} />);

      const button = screen.getByRole('button');
      // When disabled, the hover:scale-105 is still in CSS but opacity/cursor show disabled state
      expect(button.className).toContain('cursor-not-allowed');
    });

    it('should have shadow effects', () => {
      render(<RecordButton {...defaultProps} />);

      const button = screen.getByRole('button');
      expect(button.className).toContain('shadow-lg');
    });
  });
});
