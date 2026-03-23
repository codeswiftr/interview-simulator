import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useSpeechRecognition } from '../useSpeechRecognition';
import type { SpeechRecognition, SpeechRecognitionEvent } from '../../types/speech';

// Mock SpeechRecognition
class MockSpeechRecognition implements SpeechRecognition {
  continuous = true;
  interimResults = true;
  lang = 'en-US';
  onresult: ((event: SpeechRecognitionEvent) => void) | null = null;
  onerror: ((event: any) => void) | null = null;
  onend: (() => void) | null = null;
  onstart: (() => void) | null = null;

  start = vi.fn(() => {
    this.onstart?.();
  });

  stop = vi.fn(() => {
    this.onend?.();
  });

  addEventListener = vi.fn();
  removeEventListener = vi.fn();
  dispatchEvent = vi.fn();
}

// Helper to create mock speech recognition event
function createMockSpeechEvent(
  transcripts: Array<{ text: string; isFinal: boolean }>,
  resultIndex = 0
): SpeechRecognitionEvent {
  const results = transcripts.map((t, _i) => ({
    isFinal: t.isFinal,
    0: { transcript: t.text, confidence: 0.9 },
    length: 1,
  }));

  return {
    resultIndex,
    results: {
      length: results.length,
      ...results,
    } as any,
  };
}

describe('useSpeechRecognition', () => {
  let mockRecognition: MockSpeechRecognition;
  let originalSpeechRecognition: typeof window.SpeechRecognition;
  let originalWebkitSpeechRecognition: typeof window.webkitSpeechRecognition;

  beforeEach(() => {
    vi.clearAllMocks();

    // Create fresh mock instance
    mockRecognition = new MockSpeechRecognition();

    // Save original values
    originalSpeechRecognition = (window as any).SpeechRecognition;
    originalWebkitSpeechRecognition = (window as any).webkitSpeechRecognition;

    // Mock SpeechRecognition constructor as a class
    (window as any).SpeechRecognition = class {
      constructor() {
        return mockRecognition;
      }
    };
    (window as any).webkitSpeechRecognition = undefined;
  });

  afterEach(() => {
    // Restore original values
    (window as any).SpeechRecognition = originalSpeechRecognition;
    (window as any).webkitSpeechRecognition = originalWebkitSpeechRecognition;
  });

  describe('initialization', () => {
    it('should detect browser support', () => {
      const { result } = renderHook(() => useSpeechRecognition());
      expect(result.current.isSupported).toBe(true);
    });

    it('should detect lack of browser support', () => {
      (window as any).SpeechRecognition = undefined;
      (window as any).webkitSpeechRecognition = undefined;

      const { result } = renderHook(() => useSpeechRecognition());
      expect(result.current.isSupported).toBe(false);
      expect(result.current.error).toBeTruthy();
    });

    it('should use webkit prefix when available', () => {
      (window as any).SpeechRecognition = undefined;
      (window as any).webkitSpeechRecognition = class {
        constructor() {
          return mockRecognition;
        }
      };

      const { result } = renderHook(() => useSpeechRecognition());
      expect(result.current.isSupported).toBe(true);
    });

    it('should initialize with default options', () => {
      renderHook(() => useSpeechRecognition());
      
      expect(mockRecognition.continuous).toBe(true);
      expect(mockRecognition.interimResults).toBe(true);
      expect(mockRecognition.lang).toBe('en-US');
    });

    it('should accept custom options', () => {
      renderHook(() => useSpeechRecognition({
        lang: 'es-ES',
        continuous: false,
        interimResults: false,
      }));

      expect(mockRecognition.lang).toBe('es-ES');
      expect(mockRecognition.continuous).toBe(false);
      expect(mockRecognition.interimResults).toBe(false);
    });
  });

  describe('listening control', () => {
    it('should start listening', () => {
      const { result } = renderHook(() => useSpeechRecognition());

      act(() => {
        result.current.startListening();
      });

      expect(mockRecognition.start).toHaveBeenCalled();
      expect(result.current.isListening).toBe(true);
    });

    it('should stop listening', () => {
      const { result } = renderHook(() => useSpeechRecognition());

      act(() => {
        result.current.startListening();
      });

      expect(result.current.isListening).toBe(true);

      act(() => {
        result.current.stopListening();
      });

      expect(mockRecognition.stop).toHaveBeenCalled();
      expect(result.current.isListening).toBe(false);
    });

    it('should not start if already listening', () => {
      const { result } = renderHook(() => useSpeechRecognition());

      act(() => {
        result.current.startListening();
      });

      const startCallCount = mockRecognition.start.mock.calls.length;

      act(() => {
        result.current.startListening();
      });

      expect(mockRecognition.start).toHaveBeenCalledTimes(startCallCount);
    });

    it('should handle start errors gracefully', () => {
      mockRecognition.start = vi.fn(() => {
        throw new Error('Permission denied');
      });

      const onError = vi.fn();
      const { result } = renderHook(() => useSpeechRecognition({ onError }));

      act(() => {
        result.current.startListening();
      });

      expect(result.current.error).toBeTruthy();
      expect(result.current.isListening).toBe(false);
      expect(onError).toHaveBeenCalled();
    });
  });

  describe('transcript handling', () => {
    it('should update transcript on interim results', () => {
      const { result } = renderHook(() => useSpeechRecognition());

      act(() => {
        result.current.startListening();
      });

      act(() => {
        const event = createMockSpeechEvent([
          { text: 'Hello', isFinal: false },
        ]);
        mockRecognition.onresult?.(event);
      });

      expect(result.current.transcript).toBe('Hello');
      expect(result.current.finalTranscript).toBe('');
    });

    it('should update final transcript on final results', () => {
      const { result } = renderHook(() => useSpeechRecognition());

      act(() => {
        result.current.startListening();
      });

      act(() => {
        const event = createMockSpeechEvent([
          { text: 'Hello world', isFinal: true },
        ]);
        mockRecognition.onresult?.(event);
      });

      expect(result.current.transcript).toBe('Hello world');
      expect(result.current.finalTranscript).toBe('Hello world');
    });

    it('should accumulate transcripts across multiple results', () => {
      const { result } = renderHook(() => useSpeechRecognition());

      act(() => {
        result.current.startListening();
      });

      // First event: final result "Hello" at index 0
      act(() => {
        const event1 = createMockSpeechEvent([
          { text: 'Hello', isFinal: true },
        ], 0);
        mockRecognition.onresult?.(event1);
      });

      expect(result.current.transcript).toBe('Hello');
      expect(result.current.finalTranscript).toBe('Hello');

      // Second event: new interim result " world" 
      // resultIndex 1 means results[0] was already processed, process from index 1
      act(() => {
        const event2: SpeechRecognitionEvent = {
          resultIndex: 1, // Start from index 1 (skip already processed index 0)
          results: {
            length: 2,
            0: {
              isFinal: true,
              0: { transcript: 'Hello', confidence: 0.9 },
              length: 1,
            },
            1: {
              isFinal: false,
              0: { transcript: ' world', confidence: 0.8 },
              length: 1,
            },
          } as any,
        };
        mockRecognition.onresult?.(event2);
      });

      expect(result.current.transcript).toBe('Hello world');
      expect(result.current.finalTranscript).toBe('Hello');
    });

    it('should reset transcript', () => {
      const { result } = renderHook(() => useSpeechRecognition());

      act(() => {
        result.current.startListening();
      });

      act(() => {
        const event = createMockSpeechEvent([
          { text: 'Hello world', isFinal: true },
        ]);
        mockRecognition.onresult?.(event);
      });

      expect(result.current.transcript).toBe('Hello world');

      act(() => {
        result.current.resetTranscript();
      });

      expect(result.current.transcript).toBe('');
      expect(result.current.finalTranscript).toBe('');
    });
  });

  describe('callbacks', () => {
    it('should call onResult with interim results', () => {
      const onResult = vi.fn();
      const { result } = renderHook(() => useSpeechRecognition({ onResult }));

      act(() => {
        result.current.startListening();
      });

      act(() => {
        const event = createMockSpeechEvent([
          { text: 'Hello', isFinal: false },
        ]);
        mockRecognition.onresult?.(event);
      });

      expect(onResult).toHaveBeenCalledWith('Hello', false);
    });

    it('should call onResult with final results', () => {
      const onResult = vi.fn();
      const { result } = renderHook(() => useSpeechRecognition({ onResult }));

      act(() => {
        result.current.startListening();
      });

      act(() => {
        const event = createMockSpeechEvent([
          { text: 'Hello world', isFinal: true },
        ]);
        mockRecognition.onresult?.(event);
      });

      expect(onResult).toHaveBeenCalledWith('Hello world', true);
    });

    it('should call onError on recognition errors', () => {
      const onError = vi.fn();
      renderHook(() => useSpeechRecognition({ onError }));

      act(() => {
        mockRecognition.onerror?.({
          error: 'no-speech',
          message: 'No speech detected',
        } as any);
      });

      expect(onError).toHaveBeenCalled();
    });
  });

  describe('error handling', () => {
    it('should handle no-speech error', () => {
      const { result } = renderHook(() => useSpeechRecognition());

      act(() => {
        mockRecognition.onerror?.({
          error: 'no-speech',
          message: 'No speech detected',
        } as any);
      });

      expect(result.current.error).toContain('no-speech');
      expect(result.current.isListening).toBe(false);
    });

    it('should handle network error', () => {
      const { result } = renderHook(() => useSpeechRecognition());

      act(() => {
        mockRecognition.onerror?.({
          error: 'network',
          message: 'Network error',
        } as any);
      });

      expect(result.current.error).toContain('network');
    });

    it('should handle service-not-allowed error', () => {
      const { result } = renderHook(() => useSpeechRecognition());

      act(() => {
        mockRecognition.onerror?.({
          error: 'service-not-allowed',
          message: 'Service not allowed',
        } as any);
      });

      expect(result.current.error).toContain('service-not-allowed');
    });
  });

  describe('cleanup', () => {
    it('should stop recognition on unmount', () => {
      const { result, unmount } = renderHook(() => useSpeechRecognition());

      act(() => {
        result.current.startListening();
      });

      unmount();

      expect(mockRecognition.stop).toHaveBeenCalled();
    });

    it('should handle stop errors gracefully', () => {
      mockRecognition.stop = vi.fn(() => {
        throw new Error('Stop failed');
      });

      const { result } = renderHook(() => useSpeechRecognition());

      act(() => {
        result.current.startListening();
      });

      act(() => {
        result.current.stopListening();
      });

      // Should not throw, just set listening to false
      expect(result.current.isListening).toBe(false);
    });
  });
});
