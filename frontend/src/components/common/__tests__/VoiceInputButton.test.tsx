import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { VoiceInputButton } from '../VoiceInputButton';
import * as speechRecognitionModule from '../../../hooks/useSpeechRecognition';

// Mock useSpeechRecognition hook
const mockStartListening = vi.fn();
const mockStopListening = vi.fn();
const mockResetTranscript = vi.fn();

vi.mock('../../../hooks/useSpeechRecognition', () => ({
  useSpeechRecognition: vi.fn(),
}));

describe('VoiceInputButton', () => {
  const defaultMockReturn = {
    isListening: false,
    transcript: '',
    finalTranscript: '',
    error: null,
    isSupported: true,
    startListening: mockStartListening,
    stopListening: mockStopListening,
    resetTranscript: mockResetTranscript,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(speechRecognitionModule.useSpeechRecognition).mockReturnValue(defaultMockReturn);
  });

  describe('rendering', () => {
    it('should render microphone button', () => {
      render(<VoiceInputButton onTranscript={vi.fn()} />);
      
      const button = screen.getByRole('button', { name: /start voice input/i });
      expect(button).toBeInTheDocument();
    });

    it('should show listening state when active', () => {
      vi.mocked(speechRecognitionModule.useSpeechRecognition).mockReturnValue({
        ...defaultMockReturn,
        isListening: true,
      });

      render(<VoiceInputButton onTranscript={vi.fn()} />);
      
      const button = screen.getByRole('button', { name: /stop voice input/i });
      expect(button).toHaveAttribute('aria-pressed', 'true');
    });

    it('should show placeholder when listening', () => {
      vi.mocked(speechRecognitionModule.useSpeechRecognition).mockReturnValue({
        ...defaultMockReturn,
        isListening: true,
      });

      render(<VoiceInputButton onTranscript={vi.fn()} placeholder="Listening..." />);
      
      expect(screen.getByText('Listening...')).toBeInTheDocument();
    });

    it('should show error message when error occurs', () => {
      vi.mocked(speechRecognitionModule.useSpeechRecognition).mockReturnValue({
        ...defaultMockReturn,
        error: 'Permission denied',
      });

      render(<VoiceInputButton onTranscript={vi.fn()} />);
      
      expect(screen.getByText('Permission denied')).toBeInTheDocument();
    });

    it('should show unsupported state when browser not supported', () => {
      vi.mocked(speechRecognitionModule.useSpeechRecognition).mockReturnValue({
        ...defaultMockReturn,
        isSupported: false,
      });

      render(<VoiceInputButton onTranscript={vi.fn()} />);
      
      const button = screen.getByRole('button');
      expect(button).toBeDisabled();
      expect(button).toHaveAttribute('title', 'Speech recognition not supported in this browser');
    });
  });

  describe('size variants', () => {
    it('should apply small size', () => {
      render(<VoiceInputButton onTranscript={vi.fn()} size="sm" />);
      
      const button = screen.getByRole('button');
      expect(button).toHaveClass('h-8', 'w-8');
    });

    it('should apply medium size by default', () => {
      render(<VoiceInputButton onTranscript={vi.fn()} />);
      
      const button = screen.getByRole('button');
      expect(button).toHaveClass('h-10', 'w-10');
    });

    it('should apply large size', () => {
      render(<VoiceInputButton onTranscript={vi.fn()} size="lg" />);
      
      const button = screen.getByRole('button');
      expect(button).toHaveClass('h-12', 'w-12');
    });
  });

  describe('interactions', () => {
    it('should start listening when clicked', async () => {
      const user = userEvent.setup();
      render(<VoiceInputButton onTranscript={vi.fn()} />);
      
      const button = screen.getByRole('button', { name: /start voice input/i });
      await user.click(button);
      
      expect(mockResetTranscript).toHaveBeenCalled();
      expect(mockStartListening).toHaveBeenCalled();
    });

    it('should stop listening when clicked while active', async () => {
      vi.mocked(speechRecognitionModule.useSpeechRecognition).mockReturnValue({
        ...defaultMockReturn,
        isListening: true,
        transcript: 'Hello world',
      });

      const onTranscript = vi.fn();
      const user = userEvent.setup();
      render(<VoiceInputButton onTranscript={onTranscript} />);
      
      const button = screen.getByRole('button', { name: /stop voice input/i });
      await user.click(button);
      
      expect(mockStopListening).toHaveBeenCalled();
      expect(onTranscript).toHaveBeenCalledWith('Hello world');
      expect(mockResetTranscript).toHaveBeenCalled();
    });

    it('should be disabled when disabled prop is true', () => {
      render(<VoiceInputButton onTranscript={vi.fn()} disabled />);
      
      const button = screen.getByRole('button');
      expect(button).toBeDisabled();
    });

    it('should be disabled when error occurs', () => {
      vi.mocked(speechRecognitionModule.useSpeechRecognition).mockReturnValue({
        ...defaultMockReturn,
        error: 'Some error',
      });

      render(<VoiceInputButton onTranscript={vi.fn()} />);
      
      const button = screen.getByRole('button');
      expect(button).toBeDisabled();
    });
  });

  describe('transcript handling', () => {
    it('should call onTranscript with final transcript', async () => {
      const onTranscript = vi.fn();
      
      // First render with no final transcript
      const { rerender } = render(<VoiceInputButton onTranscript={onTranscript} />);
      
      // Simulate final transcript arriving
      vi.mocked(speechRecognitionModule.useSpeechRecognition).mockReturnValue({
        ...defaultMockReturn,
        finalTranscript: 'Hello world',
      });
      
      rerender(<VoiceInputButton onTranscript={onTranscript} />);
      
      await waitFor(() => {
        expect(onTranscript).toHaveBeenCalledWith('Hello world');
      });
      expect(mockResetTranscript).toHaveBeenCalled();
    });

    it('should call onInterim with interim transcript', async () => {
      const onInterim = vi.fn();
      const onResult = vi.fn();
      
      // Mock the hook to call onResult callback
      let resultCallback: ((text: string, isFinal: boolean) => void) | undefined;
      vi.mocked(speechRecognitionModule.useSpeechRecognition).mockImplementation((options) => {
        resultCallback = options?.onResult;
        return defaultMockReturn;
      });

      render(<VoiceInputButton onTranscript={vi.fn()} onInterim={onInterim} />);
      
      // Simulate interim result
      if (resultCallback) {
        resultCallback('Hello', false);
      }
      
      await waitFor(() => {
        expect(onInterim).toHaveBeenCalledWith('Hello');
      });
    });

    it('should not call onInterim for final results', async () => {
      const onInterim = vi.fn();
      const onResult = vi.fn();
      
      let resultCallback: ((text: string, isFinal: boolean) => void) | undefined;
      vi.mocked(speechRecognitionModule.useSpeechRecognition).mockImplementation((options) => {
        resultCallback = options?.onResult;
        return defaultMockReturn;
      });

      render(<VoiceInputButton onTranscript={vi.fn()} onInterim={onInterim} />);
      
      // Simulate final result
      if (resultCallback) {
        resultCallback('Hello world', true);
      }
      
      // onInterim should not be called for final results
      expect(onInterim).not.toHaveBeenCalled();
    });
  });

  describe('auto-start', () => {
    it('should auto-start when autoStart is true', () => {
      vi.mocked(speechRecognitionModule.useSpeechRecognition).mockReturnValue({
        ...defaultMockReturn,
        isSupported: true,
      });

      render(<VoiceInputButton onTranscript={vi.fn()} autoStart />);
      
      expect(mockStartListening).toHaveBeenCalled();
    });

    it('should not auto-start when disabled', () => {
      vi.mocked(speechRecognitionModule.useSpeechRecognition).mockReturnValue({
        ...defaultMockReturn,
        isSupported: true,
      });

      render(<VoiceInputButton onTranscript={vi.fn()} autoStart disabled />);
      
      expect(mockStartListening).not.toHaveBeenCalled();
    });

    it('should not auto-start when not supported', () => {
      vi.mocked(speechRecognitionModule.useSpeechRecognition).mockReturnValue({
        ...defaultMockReturn,
        isSupported: false,
      });

      render(<VoiceInputButton onTranscript={vi.fn()} autoStart />);
      
      expect(mockStartListening).not.toHaveBeenCalled();
    });
  });

  describe('accessibility', () => {
    it('should have proper aria-label', () => {
      render(<VoiceInputButton onTranscript={vi.fn()} />);
      
      const button = screen.getByRole('button', { name: /start voice input/i });
      expect(button).toHaveAttribute('aria-label', 'Start voice input');
    });

    it('should have aria-pressed when listening', () => {
      vi.mocked(speechRecognitionModule.useSpeechRecognition).mockReturnValue({
        ...defaultMockReturn,
        isListening: true,
      });

      render(<VoiceInputButton onTranscript={vi.fn()} />);
      
      const button = screen.getByRole('button');
      expect(button).toHaveAttribute('aria-pressed', 'true');
      expect(button).toHaveAttribute('aria-label', 'Stop voice input');
    });

    it('should have focus-visible ring', () => {
      render(<VoiceInputButton onTranscript={vi.fn()} />);
      
      const button = screen.getByRole('button');
      expect(button).toHaveClass('focus-visible:ring-2', 'focus-visible:ring-electric-blue');
    });
  });
});
