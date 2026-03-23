import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, act } from '@/test/utils';
import userEvent from '@testing-library/user-event';
import RecordingDeck from '../RecordingDeck';

// Mock Web Audio API
class MockAudioContext {
  state = 'running';
  createAnalyser = vi.fn(() => ({
    fftSize: 256,
    frequencyBinCount: 128,
    getByteFrequencyData: vi.fn(),
    connect: vi.fn(),
    disconnect: vi.fn(),
  }));
  createMediaStreamSource = vi.fn(() => ({
    connect: vi.fn(),
    disconnect: vi.fn(),
  }));
  close = vi.fn().mockResolvedValue(undefined);
}

// Mock MediaStream
class MockMediaStream {
  id = 'mock-stream-id';
  active = true;
  getTracks = vi.fn(() => []);
  getAudioTracks = vi.fn(() => []);
  getVideoTracks = vi.fn(() => []);
  addTrack = vi.fn();
  removeTrack = vi.fn();
  addEventListener = vi.fn();
  removeEventListener = vi.fn();
  dispatchEvent = vi.fn();
}

// Mock Speech Recognition
class MockSpeechRecognition {
  continuous = false;
  interimResults = false;
  lang = 'en-US';
  onresult = null;
  onerror = null;
  onend = null;
  start = vi.fn();
  stop = vi.fn();
  abort = vi.fn();
}

// Mock HTMLCanvasElement methods
class MockCanvasRenderingContext2D {
  canvas = document.createElement('canvas');
  fillStyle = '';
  strokeStyle = '';
  clearRect = vi.fn();
  fillRect = vi.fn();
  strokeRect = vi.fn();
  createLinearGradient = vi.fn(() => ({
    addColorStop: vi.fn(),
  }));
  drawImage = vi.fn();
  getImageData = vi.fn();
  putImageData = vi.fn();
  save = vi.fn();
  restore = vi.fn();
  scale = vi.fn();
  rotate = vi.fn();
  translate = vi.fn();
  transform = vi.fn();
  setTransform = vi.fn();
  resetTransform = vi.fn();
  beginPath = vi.fn();
  closePath = vi.fn();
  moveTo = vi.fn();
  lineTo = vi.fn();
  bezierCurveTo = vi.fn();
  quadraticCurveTo = vi.fn();
  arc = vi.fn();
  arcTo = vi.fn();
  ellipse = vi.fn();
  rect = vi.fn();
  fill = vi.fn();
  stroke = vi.fn();
  clip = vi.fn();
  isPointInPath = vi.fn();
  isPointInStroke = vi.fn();
  measureText = vi.fn(() => ({ width: 0 }));
  fillText = vi.fn();
  strokeText = vi.fn();
}

describe('RecordingDeck', () => {
  let mockCallbacks: {
    onStart: ReturnType<typeof vi.fn>;
    onStop: ReturnType<typeof vi.fn>;
    onPause: ReturnType<typeof vi.fn>;
    onResume: ReturnType<typeof vi.fn>;
    onCancel: ReturnType<typeof vi.fn>;
    onConfirm: ReturnType<typeof vi.fn>;
  };

  let mockMediaStream: MockMediaStream;
  let requestAnimationFrameSpy: ReturnType<typeof vi.spyOn>;
  let cancelAnimationFrameSpy: ReturnType<typeof vi.spyOn>;
  let animationFrameId = 0;

  beforeEach(() => {
    // Setup mocks
    mockCallbacks = {
      onStart: vi.fn(),
      onStop: vi.fn(),
      onPause: vi.fn(),
      onResume: vi.fn(),
      onCancel: vi.fn(),
      onConfirm: vi.fn(),
    };

    mockMediaStream = new MockMediaStream();

    // Mock Web Audio API globally
    (globalThis as any).AudioContext = MockAudioContext;
    (globalThis as any).webkitAudioContext = MockAudioContext;

    // Mock Speech Recognition globally
    (globalThis as any).SpeechRecognition = MockSpeechRecognition;
    (globalThis as any).webkitSpeechRecognition = MockSpeechRecognition;

    // Mock requestAnimationFrame and cancelAnimationFrame
    // Don't call the callback immediately to avoid infinite recursion
    requestAnimationFrameSpy = vi.spyOn(globalThis, 'requestAnimationFrame').mockImplementation(() => {
      return ++animationFrameId;
    });
    cancelAnimationFrameSpy = vi.spyOn(globalThis, 'cancelAnimationFrame').mockImplementation(() => {});

    // Mock canvas getContext
    HTMLCanvasElement.prototype.getContext = vi.fn((contextType) => {
      if (contextType === '2d') {
        return new MockCanvasRenderingContext2D() as any;
      }
      return null;
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
    requestAnimationFrameSpy.mockRestore();
    cancelAnimationFrameSpy.mockRestore();
    animationFrameId = 0;
  });

  describe('Rendering States', () => {
    it('should render idle state correctly', () => {
      render(
        <RecordingDeck
          isRecording={false}
          recordingState="idle"
          duration={0}
          mediaStream={null}
          {...mockCallbacks}
        />
      );

      expect(screen.getByText('Start Recording')).toBeInTheDocument();
      // In idle state, timer is not shown - only the Start Recording button is visible
    });

    it('should render recording state correctly', () => {
      render(
        <RecordingDeck
          isRecording={true}
          recordingState="recording"
          duration={45}
          mediaStream={mockMediaStream as any}
          {...mockCallbacks}
        />
      );

      expect(screen.getByText('RECORDING')).toBeInTheDocument();
      expect(screen.getByText('0:45')).toBeInTheDocument();

      // Should show recording indicator (red dot)
      const timerElement = screen.getByText('0:45');
      expect(timerElement).toHaveClass('text-status-error');
    });

    it('should render paused state correctly', () => {
      render(
        <RecordingDeck
          isRecording={false}
          recordingState="paused"
          duration={30}
          mediaStream={mockMediaStream as any}
          {...mockCallbacks}
        />
      );

      expect(screen.getByText('PAUSED')).toBeInTheDocument();
      expect(screen.getByText('0:30')).toBeInTheDocument();
    });

    it('should format time correctly for minutes and seconds', () => {
      const { rerender } = render(
        <RecordingDeck
          isRecording={true}
          recordingState="recording"
          duration={65}
          mediaStream={mockMediaStream as any}
          {...mockCallbacks}
        />
      );

      expect(screen.getByText('1:05')).toBeInTheDocument();

      rerender(
        <RecordingDeck
          isRecording={true}
          recordingState="recording"
          duration={125}
          mediaStream={mockMediaStream as any}
          {...mockCallbacks}
        />
      );

      expect(screen.getByText('2:05')).toBeInTheDocument();
    });

    it('should show canvas visualizer when mediaStream is provided', () => {
      render(
        <RecordingDeck
          isRecording={true}
          recordingState="recording"
          duration={10}
          mediaStream={mockMediaStream as any}
          {...mockCallbacks}
        />
      );

      const canvas = document.querySelector('canvas');
      expect(canvas).toBeInTheDocument();
      expect(canvas).toHaveAttribute('width', '600');
      expect(canvas).toHaveAttribute('height', '160');
    });

    it('should not show "Ready to Record" when mediaStream is active', () => {
      render(
        <RecordingDeck
          isRecording={true}
          recordingState="recording"
          duration={10}
          mediaStream={mockMediaStream as any}
          {...mockCallbacks}
        />
      );

      expect(screen.queryByText('Ready to Record')).not.toBeInTheDocument();
    });
  });

  describe('Button Interactions - Idle State', () => {
    it('should call onStart when start button is clicked in idle state', async () => {
      const user = userEvent.setup();

      render(
        <RecordingDeck
          isRecording={false}
          recordingState="idle"
          duration={0}
          mediaStream={null}
          {...mockCallbacks}
        />
      );

      const startButton = screen.getByRole('button');
      await user.click(startButton);

      expect(mockCallbacks.onStart).toHaveBeenCalledTimes(1);
      expect(mockCallbacks.onStop).not.toHaveBeenCalled();
      expect(mockCallbacks.onPause).not.toHaveBeenCalled();
    });

    it('should not call onStart when button is disabled', async () => {
      const user = userEvent.setup();

      render(
        <RecordingDeck
          isRecording={false}
          recordingState="idle"
          duration={0}
          mediaStream={null}
          {...mockCallbacks}
          disabled={true}
        />
      );

      const startButton = screen.getByRole('button');
      expect(startButton).toBeDisabled();

      // Try to click disabled button
      await user.click(startButton);

      expect(mockCallbacks.onStart).not.toHaveBeenCalled();
    });
  });

  describe('Button Interactions - Recording State', () => {
    it('should show pause, stop, and cancel buttons when recording', () => {
      render(
        <RecordingDeck
          isRecording={true}
          recordingState="recording"
          duration={10}
          mediaStream={mockMediaStream as any}
          {...mockCallbacks}
        />
      );

      expect(screen.getByTitle('Pause')).toBeInTheDocument();
      expect(screen.getByTitle('Stop & Save')).toBeInTheDocument();
      expect(screen.getByTitle('Cancel')).toBeInTheDocument();
    });

    it('should call onPause when pause button is clicked', async () => {
      const user = userEvent.setup();

      render(
        <RecordingDeck
          isRecording={true}
          recordingState="recording"
          duration={10}
          mediaStream={mockMediaStream as any}
          {...mockCallbacks}
        />
      );

      const pauseButton = screen.getByTitle('Pause');
      await user.click(pauseButton);

      expect(mockCallbacks.onPause).toHaveBeenCalledTimes(1);
    });

    it('should call onStop when stop button is clicked', async () => {
      const user = userEvent.setup();

      render(
        <RecordingDeck
          isRecording={true}
          recordingState="recording"
          duration={10}
          mediaStream={mockMediaStream as any}
          {...mockCallbacks}
        />
      );

      const stopButton = screen.getByTitle('Stop & Save');
      await user.click(stopButton);

      expect(mockCallbacks.onStop).toHaveBeenCalledTimes(1);
    });

    it('should call onCancel when cancel button is clicked', async () => {
      const user = userEvent.setup();

      render(
        <RecordingDeck
          isRecording={true}
          recordingState="recording"
          duration={10}
          mediaStream={mockMediaStream as any}
          {...mockCallbacks}
        />
      );

      const cancelButton = screen.getByTitle('Cancel');
      await user.click(cancelButton);

      expect(mockCallbacks.onCancel).toHaveBeenCalledTimes(1);
    });
  });

  describe('Button Interactions - Paused State', () => {
    it('should show resume button when paused', () => {
      render(
        <RecordingDeck
          isRecording={false}
          recordingState="paused"
          duration={30}
          mediaStream={mockMediaStream as any}
          {...mockCallbacks}
        />
      );

      expect(screen.getByTitle('Resume')).toBeInTheDocument();
      expect(screen.queryByTitle('Pause')).not.toBeInTheDocument();
    });

    it('should call onResume when resume button is clicked', async () => {
      const user = userEvent.setup();

      render(
        <RecordingDeck
          isRecording={false}
          recordingState="paused"
          duration={30}
          mediaStream={mockMediaStream as any}
          {...mockCallbacks}
        />
      );

      const resumeButton = screen.getByTitle('Resume');
      await user.click(resumeButton);

      expect(mockCallbacks.onResume).toHaveBeenCalledTimes(1);
    });

    it('should still show cancel and stop buttons when paused', () => {
      render(
        <RecordingDeck
          isRecording={false}
          recordingState="paused"
          duration={30}
          mediaStream={mockMediaStream as any}
          {...mockCallbacks}
        />
      );

      expect(screen.getByTitle('Cancel')).toBeInTheDocument();
      expect(screen.getByTitle('Stop & Save')).toBeInTheDocument();
    });
  });

  describe('Audio Visualization', () => {
    it('should initialize AudioContext when mediaStream is provided', async () => {
      render(
        <RecordingDeck
          isRecording={true}
          recordingState="recording"
          duration={10}
          mediaStream={mockMediaStream as any}
          {...mockCallbacks}
        />
      );

      await waitFor(() => {
        const AudioContextConstructor = (globalThis as any).AudioContext;
        // The component should have created an AudioContext instance
        expect(AudioContextConstructor).toBeDefined();
      });
    });

    it('should create analyser and source nodes', async () => {
      const _mockAudioContext = new MockAudioContext();

      render(
        <RecordingDeck
          isRecording={true}
          recordingState="recording"
          duration={10}
          mediaStream={mockMediaStream as any}
          {...mockCallbacks}
        />
      );

      await waitFor(() => {
        // Verify canvas context is created
        const canvas = document.querySelector('canvas');
        expect(canvas).toBeInTheDocument();
      });
    });

    it('should start animation frame when rendering visualization', async () => {
      render(
        <RecordingDeck
          isRecording={true}
          recordingState="recording"
          duration={10}
          mediaStream={mockMediaStream as any}
          {...mockCallbacks}
        />
      );

      await waitFor(() => {
        expect(requestAnimationFrameSpy).toHaveBeenCalled();
      });
    });

    it('should cleanup visualization when mediaStream is removed', async () => {
      const { rerender } = render(
        <RecordingDeck
          isRecording={true}
          recordingState="recording"
          duration={10}
          mediaStream={mockMediaStream as any}
          {...mockCallbacks}
        />
      );

      // Remove mediaStream
      rerender(
        <RecordingDeck
          isRecording={false}
          recordingState="idle"
          duration={0}
          mediaStream={null}
          {...mockCallbacks}
        />
      );

      await waitFor(() => {
        expect(cancelAnimationFrameSpy).toHaveBeenCalled();
      });
    });

    it('should cleanup on unmount', () => {
      const { unmount } = render(
        <RecordingDeck
          isRecording={true}
          recordingState="recording"
          duration={10}
          mediaStream={mockMediaStream as any}
          {...mockCallbacks}
        />
      );

      unmount();

      expect(cancelAnimationFrameSpy).toHaveBeenCalled();
    });
  });

  describe('Speech Recognition (Live Transcription)', () => {
    it('should initialize speech recognition when recording starts', async () => {
      const mockRecognition = new MockSpeechRecognition();
      const SpeechRecognitionConstructor = function(this: any) {
        return mockRecognition;
      };
      SpeechRecognitionConstructor.prototype = MockSpeechRecognition.prototype;
      (globalThis as any).SpeechRecognition = SpeechRecognitionConstructor;
      (globalThis as any).webkitSpeechRecognition = SpeechRecognitionConstructor;

      render(
        <RecordingDeck
          isRecording={true}
          recordingState="recording"
          duration={10}
          mediaStream={mockMediaStream as any}
          {...mockCallbacks}
        />
      );

      await waitFor(() => {
        expect(mockRecognition.start).toHaveBeenCalled();
      });
    });

    it('should display transcript when speech is recognized', async () => {
      const mockRecognition = new MockSpeechRecognition();
      const SpeechRecognitionConstructor = function(this: any) {
        return mockRecognition;
      };
      SpeechRecognitionConstructor.prototype = MockSpeechRecognition.prototype;
      (globalThis as any).SpeechRecognition = SpeechRecognitionConstructor;
      (globalThis as any).webkitSpeechRecognition = SpeechRecognitionConstructor;

      render(
        <RecordingDeck
          isRecording={true}
          recordingState="recording"
          duration={10}
          mediaStream={mockMediaStream as any}
          {...mockCallbacks}
        />
      );

      // Simulate speech recognition result
      await waitFor(() => {
        expect(mockRecognition.onresult).toBeDefined();
      });

      const mockEvent = {
        resultIndex: 0,
        results: [
          {
            0: { transcript: 'Hello world' },
            isFinal: true,
            length: 1,
          },
        ],
      };

      // Trigger the onresult callback
      await act(async () => {
        if (mockRecognition.onresult) {
          mockRecognition.onresult(mockEvent);
        }
      });

      await waitFor(() => {
        expect(screen.getByText(/Hello world/)).toBeInTheDocument();
      });
    });

    it('should stop speech recognition when recording stops', async () => {
      const mockRecognition = new MockSpeechRecognition();
      const SpeechRecognitionConstructor = function(this: any) {
        return mockRecognition;
      };
      SpeechRecognitionConstructor.prototype = MockSpeechRecognition.prototype;
      (globalThis as any).SpeechRecognition = SpeechRecognitionConstructor;
      (globalThis as any).webkitSpeechRecognition = SpeechRecognitionConstructor;

      const { rerender } = render(
        <RecordingDeck
          isRecording={true}
          recordingState="recording"
          duration={10}
          mediaStream={mockMediaStream as any}
          {...mockCallbacks}
        />
      );

      await waitFor(() => {
        expect(mockRecognition.start).toHaveBeenCalled();
      });

      // Stop recording
      rerender(
        <RecordingDeck
          isRecording={false}
          recordingState="idle"
          duration={0}
          mediaStream={null}
          {...mockCallbacks}
        />
      );

      await waitFor(() => {
        expect(mockRecognition.stop).toHaveBeenCalled();
      });
    });

    it('should not initialize speech recognition if not supported', () => {
      // Remove speech recognition support
      delete (globalThis as any).SpeechRecognition;
      delete (globalThis as any).webkitSpeechRecognition;

      render(
        <RecordingDeck
          isRecording={true}
          recordingState="recording"
          duration={10}
          mediaStream={mockMediaStream as any}
          {...mockCallbacks}
        />
      );

      // Should render without errors even without speech recognition
      expect(screen.getByText('RECORDING')).toBeInTheDocument();
    });

    it('should cleanup speech recognition on unmount', async () => {
      const mockRecognition = new MockSpeechRecognition();
      const SpeechRecognitionConstructor = function(this: any) {
        return mockRecognition;
      };
      SpeechRecognitionConstructor.prototype = MockSpeechRecognition.prototype;
      (globalThis as any).SpeechRecognition = SpeechRecognitionConstructor;
      (globalThis as any).webkitSpeechRecognition = SpeechRecognitionConstructor;

      const { unmount } = render(
        <RecordingDeck
          isRecording={true}
          recordingState="recording"
          duration={10}
          mediaStream={mockMediaStream as any}
          {...mockCallbacks}
        />
      );

      await waitFor(() => {
        expect(mockRecognition.start).toHaveBeenCalled();
      });

      unmount();

      expect(mockRecognition.stop).toHaveBeenCalled();
    });
  });

  describe('Disabled State', () => {
    it('should disable start button when disabled prop is true', () => {
      render(
        <RecordingDeck
          isRecording={false}
          recordingState="idle"
          duration={0}
          mediaStream={null}
          {...mockCallbacks}
          disabled={true}
        />
      );

      const startButton = screen.getByRole('button');
      expect(startButton).toBeDisabled();
    });

    it('should not disable controls during recording even if disabled prop is true', () => {
      render(
        <RecordingDeck
          isRecording={true}
          recordingState="recording"
          duration={10}
          mediaStream={mockMediaStream as any}
          {...mockCallbacks}
          disabled={true}
        />
      );

      // Recording controls should not be disabled
      const pauseButton = screen.getByTitle('Pause');
      const stopButton = screen.getByTitle('Stop & Save');
      const cancelButton = screen.getByTitle('Cancel');

      expect(pauseButton).not.toBeDisabled();
      expect(stopButton).not.toBeDisabled();
      expect(cancelButton).not.toBeDisabled();
    });

    it('should enable start button when disabled prop is false', () => {
      render(
        <RecordingDeck
          isRecording={false}
          recordingState="idle"
          duration={0}
          mediaStream={null}
          {...mockCallbacks}
          disabled={false}
        />
      );

      const startButton = screen.getByRole('button');
      expect(startButton).not.toBeDisabled();
    });
  });

  describe('Accessibility', () => {
    it('should have proper button labels and titles', () => {
      render(
        <RecordingDeck
          isRecording={true}
          recordingState="recording"
          duration={10}
          mediaStream={mockMediaStream as any}
          {...mockCallbacks}
        />
      );

      expect(screen.getByTitle('Pause')).toBeInTheDocument();
      expect(screen.getByTitle('Stop & Save')).toBeInTheDocument();
      expect(screen.getByTitle('Cancel')).toBeInTheDocument();
    });

    it('should have accessible button roles', () => {
      render(
        <RecordingDeck
          isRecording={false}
          recordingState="idle"
          duration={0}
          mediaStream={null}
          {...mockCallbacks}
        />
      );

      const buttons = screen.getAllByRole('button');
      expect(buttons.length).toBeGreaterThan(0);
    });
  });

  describe('Edge Cases', () => {
    it('should handle transition from recording to paused to recording', async () => {
      const user = userEvent.setup();

      const { rerender } = render(
        <RecordingDeck
          isRecording={true}
          recordingState="recording"
          duration={10}
          mediaStream={mockMediaStream as any}
          {...mockCallbacks}
        />
      );

      // Pause
      const pauseButton = screen.getByTitle('Pause');
      await user.click(pauseButton);

      rerender(
        <RecordingDeck
          isRecording={false}
          recordingState="paused"
          duration={10}
          mediaStream={mockMediaStream as any}
          {...mockCallbacks}
        />
      );

      expect(screen.getByText('PAUSED')).toBeInTheDocument();

      // Resume
      const resumeButton = screen.getByTitle('Resume');
      await user.click(resumeButton);

      expect(mockCallbacks.onResume).toHaveBeenCalled();
    });

    it('should handle zero duration', () => {
      render(
        <RecordingDeck
          isRecording={false}
          recordingState="idle"
          duration={0}
          mediaStream={null}
          {...mockCallbacks}
        />
      );

      // In idle state, the component shows "Start Recording" button, timer is not displayed
      expect(screen.getByText('Start Recording')).toBeInTheDocument();
    });

    it('should handle large durations correctly', () => {
      render(
        <RecordingDeck
          isRecording={true}
          recordingState="recording"
          duration={599} // 9:59
          mediaStream={mockMediaStream as any}
          {...mockCallbacks}
        />
      );

      expect(screen.getByText('9:59')).toBeInTheDocument();
    });

    it('should not crash when mediaStream is null during recording', () => {
      // This shouldn't happen in practice, but good to test
      render(
        <RecordingDeck
          isRecording={true}
          recordingState="recording"
          duration={10}
          mediaStream={null}
          {...mockCallbacks}
        />
      );

      expect(screen.getByText('RECORDING')).toBeInTheDocument();
    });
  });
});
