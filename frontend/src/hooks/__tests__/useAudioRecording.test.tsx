import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useAudioRecording } from '../useAudioRecording';

// Mock MediaRecorder
class MockMediaRecorder {
  state = 'inactive';
  mimeType = 'audio/webm';
  ondataavailable: ((e: { data: Blob }) => void) | null = null;
  onstop: (() => void) | null = null;
  onerror: ((e: Event) => void) | null = null;
  start = vi.fn(() => {
    this.state = 'recording';
  });
  stop = vi.fn(() => {
    this.state = 'inactive';
    this.onstop?.();
  });
  pause = vi.fn(() => {
    this.state = 'paused';
  });
  resume = vi.fn(() => {
    this.state = 'recording';
  });

  static isTypeSupported = vi.fn(() => true);
}

// Mock MediaStream
const createMockMediaStream = () => {
  const mockTrack = {
    stop: vi.fn(),
    kind: 'audio',
    enabled: true,
    muted: false,
  };
  return {
    getTracks: () => [mockTrack],
    getAudioTracks: () => [mockTrack],
    active: true,
  } as unknown as MediaStream;
};

// Mock Audio element
const createMockAudio = () => {
  const audio = {
    play: vi.fn().mockResolvedValue(undefined),
    pause: vi.fn(),
    currentTime: 0,
    duration: 60,
    volume: 1,
    onloadedmetadata: null as (() => void) | null,
    ontimeupdate: null as (() => void) | null,
    onended: null as (() => void) | null,
    onerror: null as ((e: Event) => void) | null,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
  };
  return audio as unknown as HTMLAudioElement;
};

// Mock URL.createObjectURL and URL.revokeObjectURL
const mockObjectURLs = new Map<string, string>();
let urlCounter = 0;

global.URL.createObjectURL = vi.fn((blob: Blob) => {
  const url = `blob:http://localhost:3000/${urlCounter++}`;
  mockObjectURLs.set(url, '');
  return url;
});

global.URL.revokeObjectURL = vi.fn((url: string) => {
  mockObjectURLs.delete(url);
});

// Mock getSupportedMimeType
vi.mock('../../lib/audio-utils', () => ({
  getSupportedMimeType: vi.fn(() => 'audio/webm;codecs=opus'),
}));

describe('useAudioRecording', () => {
  let mockMediaRecorderInstance: MockMediaRecorder;
  let mockStream: MediaStream;
  let mockAudio: HTMLAudioElement;
  let originalMediaRecorder: typeof MediaRecorder;
  let originalGetUserMedia: typeof MediaDevices.prototype.getUserMedia;
  let originalAudio: typeof Audio;

  beforeEach(() => {
    // Reset mocks
    vi.clearAllMocks();
    mockObjectURLs.clear();
    urlCounter = 0;

    // Create fresh mock instances
    mockMediaRecorderInstance = new MockMediaRecorder();
    mockStream = createMockMediaStream();
    mockAudio = createMockAudio();

    // Mock global MediaRecorder constructor to return our mock instance
    originalMediaRecorder = global.MediaRecorder;
    const MediaRecorderConstructor = vi.fn(() => mockMediaRecorderInstance) as unknown as typeof MediaRecorder;
    MediaRecorderConstructor.isTypeSupported = MockMediaRecorder.isTypeSupported;
    global.MediaRecorder = MediaRecorderConstructor;
    // Ensure it's also on window for browser-like behavior
    (global as any).window = global;
    (global.window as any).MediaRecorder = MediaRecorderConstructor;

    // Mock navigator.mediaDevices.getUserMedia
    originalGetUserMedia = navigator.mediaDevices?.getUserMedia || (() => Promise.resolve(mockStream));
    if (!global.navigator) {
      (global as any).navigator = {};
    }
    global.navigator.mediaDevices = {
      getUserMedia: vi.fn().mockResolvedValue(mockStream),
    } as unknown as MediaDevices;
    // Also set on window for browser-like behavior
    if ((global as any).window) {
      (global.window as any).navigator = global.navigator;
    }

    // Mock Audio constructor - always return the same mock instance
    originalAudio = global.Audio;
    global.Audio = vi.fn(() => mockAudio) as unknown as typeof Audio;
    if ((global as any).window) {
      (global.window as any).Audio = global.Audio;
    }
  });

  afterEach(() => {
    // Restore originals
    global.MediaRecorder = originalMediaRecorder;
    global.Audio = originalAudio;
    if (navigator.mediaDevices) {
      (navigator.mediaDevices as any).getUserMedia = originalGetUserMedia;
    }
    vi.restoreAllMocks();
  });

  describe('Initial state', () => {
    it('should start with idle state and null values', () => {
      const { result } = renderHook(() => useAudioRecording());

      expect(result.current.recordingState).toBe('idle');
      expect(result.current.audioBlob).toBeNull();
      expect(result.current.audioUrl).toBeNull();
      expect(result.current.duration).toBe(0);
      expect(result.current.isRecording).toBe(false);
      expect(result.current.isPreviewMode).toBe(false);
      expect(result.current.isPlaying).toBe(false);
      expect(result.current.currentTime).toBe(0);
      expect(result.current.audioDuration).toBe(0);
      expect(result.current.error).toBeNull();
      expect(result.current.mediaStream).toBeNull();
      expect(result.current.mimeType).toBeNull();
    });
  });

  describe('Browser support checks', () => {
    it('should handle missing mediaDevices', async () => {
      const originalMediaDevices = global.navigator.mediaDevices;
      // @ts-expect-error - testing error case
      delete global.navigator.mediaDevices;

      const { result } = renderHook(() => useAudioRecording());

      await act(async () => {
        await result.current.startRecording();
      });

      await waitFor(() => {
        expect(result.current.error).toBeTruthy();
      });

      expect(result.current.error).toContain('does not support audio recording');
      expect(result.current.recordingState).toBe('idle');

      global.navigator.mediaDevices = originalMediaDevices;
    });

    it('should handle missing MediaRecorder', async () => {
      // @ts-expect-error - testing error case
      delete global.MediaRecorder;

      const { result } = renderHook(() => useAudioRecording());

      await act(async () => {
        await result.current.startRecording();
      });

      await waitFor(() => {
        expect(result.current.error).toBeTruthy();
      });

      expect(result.current.error).toContain('does not support MediaRecorder');
      expect(result.current.recordingState).toBe('idle');
    });
  });

  describe('startRecording', () => {
    it('should request microphone permission and start recording', async () => {
      const getUserMediaSpy = vi.fn().mockResolvedValue(mockStream);
      global.navigator.mediaDevices.getUserMedia = getUserMediaSpy;

      const { result } = renderHook(() => useAudioRecording());

      await act(async () => {
        await result.current.startRecording();
      });

      // Check if getUserMedia was called
      expect(getUserMediaSpy).toHaveBeenCalledWith({ audio: true });

      // Check for errors
      if (result.current.error) {
        throw new Error(`Recording failed with error: ${result.current.error}`);
      }

      // Wait for recording state
      await waitFor(() => {
        expect(result.current.recordingState).toBe('recording');
      }, { timeout: 3000 });

      expect(mockMediaRecorderInstance.start).toHaveBeenCalled();
      expect(result.current.isRecording).toBe(true);
      expect(result.current.mediaStream).toBeTruthy();
      expect(result.current.mimeType).toBe('audio/webm;codecs=opus');
      expect(result.current.error).toBeNull();
    });

    it('should handle permission denied error', async () => {
      const error = new Error('Permission denied');
      (error as any).name = 'NotAllowedError';
      (navigator.mediaDevices.getUserMedia as any).mockRejectedValueOnce(error);

      const { result } = renderHook(() => useAudioRecording());

      await act(async () => {
        await result.current.startRecording();
      });

      await waitFor(() => {
        expect(result.current.error).toBeTruthy();
      });

      expect(result.current.error).toContain('Microphone access denied');
      expect(result.current.recordingState).toBe('idle');
    });

    it('should handle no microphone found error', async () => {
      const error = new Error('No microphone');
      (error as any).name = 'NotFoundError';
      (navigator.mediaDevices.getUserMedia as any).mockRejectedValueOnce(error);

      const { result } = renderHook(() => useAudioRecording());

      await act(async () => {
        await result.current.startRecording();
      });

      await waitFor(() => {
        expect(result.current.error).toBeTruthy();
      });

      expect(result.current.error).toContain('No microphone found');
      expect(result.current.recordingState).toBe('idle');
    });

    it('should handle generic microphone error', async () => {
      const error = new Error('Generic error');
      (error as any).name = 'UnknownError';
      (navigator.mediaDevices.getUserMedia as any).mockRejectedValueOnce(error);

      const { result } = renderHook(() => useAudioRecording());

      await act(async () => {
        await result.current.startRecording();
      });

      await waitFor(() => {
        expect(result.current.error).toBeTruthy();
      });

      expect(result.current.error).toContain('Could not access microphone');
      expect(result.current.recordingState).toBe('idle');
    });
  });

  describe('stopRecording', () => {
    it('should stop recording and enter preview mode', async () => {
      const { result } = renderHook(() => useAudioRecording());

      // Start recording
      await act(async () => {
        await result.current.startRecording();
      });

      await waitFor(() => {
        expect(result.current.recordingState).toBe('recording');
      });

      // Create blob data
      const blob = new Blob(['audio data'], { type: 'audio/webm' });
      mockMediaRecorderInstance.ondataavailable?.({ data: blob });

      // Stop recording
      await act(() => {
        result.current.stopRecording();
      });

      // Trigger onstop callback
      await act(() => {
        mockMediaRecorderInstance.onstop?.();
      });

      await waitFor(() => {
        expect(result.current.recordingState).toBe('preview');
      });

      expect(mockMediaRecorder.stop).toHaveBeenCalled();
      expect(result.current.audioBlob).toBeTruthy();
      expect(result.current.audioUrl).toBeTruthy();
      expect(result.current.isPreviewMode).toBe(true);
      expect(mockStream.getTracks()[0].stop).toHaveBeenCalled();
    });

    it('should not stop if not recording', async () => {
      const { result } = renderHook(() => useAudioRecording());

      await act(() => {
        result.current.stopRecording();
      });

      expect(mockMediaRecorderInstance.stop).not.toHaveBeenCalled();
    });
  });

  describe('pauseRecording', () => {
    it('should pause recording', async () => {
      const { result } = renderHook(() => useAudioRecording());

      // Start recording
      await act(async () => {
        await result.current.startRecording();
      });

      await waitFor(() => {
        expect(result.current.recordingState).toBe('recording');
      });

      // Pause recording
      await act(() => {
        result.current.pauseRecording();
      });

      await waitFor(() => {
        expect(result.current.recordingState).toBe('paused');
      });

      expect(mockMediaRecorderInstance.pause).toHaveBeenCalled();
      expect(result.current.isRecording).toBe(false);
    });

    it('should not pause if not recording', async () => {
      const { result } = renderHook(() => useAudioRecording());

      await act(() => {
        result.current.pauseRecording();
      });

      expect(mockMediaRecorderInstance.pause).not.toHaveBeenCalled();
    });
  });

  describe('resumeRecording', () => {
    it('should resume paused recording', async () => {
      const { result } = renderHook(() => useAudioRecording());

      // Start and pause recording
      await act(async () => {
        await result.current.startRecording();
      });

      await waitFor(() => {
        expect(result.current.recordingState).toBe('recording');
      });

      await act(() => {
        result.current.pauseRecording();
      });

      await waitFor(() => {
        expect(result.current.recordingState).toBe('paused');
      });

      // Resume recording
      await act(() => {
        result.current.resumeRecording();
      });

      await waitFor(() => {
        expect(result.current.recordingState).toBe('recording');
      });

      expect(mockMediaRecorderInstance.resume).toHaveBeenCalled();
      expect(result.current.isRecording).toBe(true);
    });

    it('should not resume if not paused', async () => {
      const { result } = renderHook(() => useAudioRecording());

      await act(() => {
        result.current.resumeRecording();
      });

      expect(mockMediaRecorderInstance.resume).not.toHaveBeenCalled();
    });
  });

  describe('resetRecording', () => {
    it('should reset all state to idle', async () => {
      const { result } = renderHook(() => useAudioRecording());

      // Start recording first
      await act(async () => {
        await result.current.startRecording();
      });

      await waitFor(() => {
        expect(result.current.recordingState).toBe('recording');
      });

      // Reset
      await act(() => {
        result.current.resetRecording();
      });

      expect(result.current.recordingState).toBe('idle');
      expect(result.current.audioBlob).toBeNull();
      expect(result.current.audioUrl).toBeNull();
      expect(result.current.duration).toBe(0);
      expect(result.current.error).toBeNull();
      expect(mockStream.getTracks()[0].stop).toHaveBeenCalled();
    });

    it('should stop MediaRecorder if active', async () => {
      const { result } = renderHook(() => useAudioRecording());

      await act(async () => {
        await result.current.startRecording();
      });

      await waitFor(() => {
        expect(result.current.recordingState).toBe('recording');
      });

      mockMediaRecorderInstance.state = 'recording';

      await act(() => {
        result.current.resetRecording();
      });

      expect(mockMediaRecorderInstance.stop).toHaveBeenCalled();
    });
  });

  describe('Preview mode', () => {
    it('should create Audio element when entering preview mode', async () => {
      const { result } = renderHook(() => useAudioRecording());

      // Start and stop recording to enter preview
      await act(async () => {
        await result.current.startRecording();
      });

      await waitFor(() => {
        expect(result.current.recordingState).toBe('recording');
      });

      const blob = new Blob(['audio data'], { type: 'audio/webm' });
      mockMediaRecorderInstance.ondataavailable?.({ data: blob });

      await act(() => {
        result.current.stopRecording();
      });

      await act(() => {
        mockMediaRecorderInstance.onstop?.();
      });

      await waitFor(() => {
        expect(result.current.isPreviewMode).toBe(true);
      });

      // Audio should be created
      expect(global.Audio).toHaveBeenCalled();
    });

    it('should update audio duration when metadata loads', async () => {
      const { result } = renderHook(() => useAudioRecording());

      // Enter preview mode
      await act(async () => {
        await result.current.startRecording();
      });

      await waitFor(() => {
        expect(result.current.recordingState).toBe('recording');
      });

      const blob = new Blob(['audio data'], { type: 'audio/webm' });
      mockMediaRecorderInstance.ondataavailable?.({ data: blob });

      await act(() => {
        result.current.stopRecording();
      });

      await act(() => {
        mockMediaRecorderInstance.onstop?.();
      });

      await waitFor(() => {
        expect(result.current.isPreviewMode).toBe(true);
      });

      // Trigger onloadedmetadata
      await act(() => {
        if (mockAudio.onloadedmetadata) {
          mockAudio.onloadedmetadata(new Event('loadedmetadata'));
        }
      });

      await waitFor(() => {
        expect(result.current.audioDuration).toBe(60);
      });
    });

    it('should update current time during playback', async () => {
      const { result } = renderHook(() => useAudioRecording());

      // Enter preview mode
      await act(async () => {
        await result.current.startRecording();
      });

      await waitFor(() => {
        expect(result.current.recordingState).toBe('recording');
      });

      const blob = new Blob(['audio data'], { type: 'audio/webm' });
      mockMediaRecorderInstance.ondataavailable?.({ data: blob });

      await act(() => {
        result.current.stopRecording();
      });

      await act(() => {
        mockMediaRecorderInstance.onstop?.();
      });

      await waitFor(() => {
        expect(result.current.isPreviewMode).toBe(true);
      });

      // Trigger ontimeupdate
      (mockAudio as any).currentTime = 5.5;
      await act(() => {
        if (mockAudio.ontimeupdate) {
          mockAudio.ontimeupdate(new Event('timeupdate'));
        }
      });

      await waitFor(() => {
        expect(result.current.currentTime).toBe(5.5);
      });
    });
  });

  describe('playPreview', () => {
    it('should play audio preview', async () => {
      const { result } = renderHook(() => useAudioRecording());

      // Enter preview mode
      await act(async () => {
        await result.current.startRecording();
      });

      await waitFor(() => {
        expect(result.current.recordingState).toBe('recording');
      });

      const blob = new Blob(['audio data'], { type: 'audio/webm' });
      mockMediaRecorderInstance.ondataavailable?.({ data: blob });

      await act(() => {
        result.current.stopRecording();
      });

      await act(() => {
        mockMediaRecorderInstance.onstop?.();
      });

      await waitFor(() => {
        expect(result.current.isPreviewMode).toBe(true);
      });

      // Play preview
      await act(() => {
        result.current.playPreview();
      });

      expect(mockAudio.play).toHaveBeenCalled();
      await waitFor(() => {
        expect(result.current.isPlaying).toBe(true);
      });
    });

    it('should handle play error gracefully', async () => {
      const { result } = renderHook(() => useAudioRecording());

      // Enter preview mode
      await act(async () => {
        await result.current.startRecording();
      });

      await waitFor(() => {
        expect(result.current.recordingState).toBe('recording');
      });

      const blob = new Blob(['audio data'], { type: 'audio/webm' });
      mockMediaRecorderInstance.ondataavailable?.({ data: blob });

      await act(() => {
        result.current.stopRecording();
      });

      await act(() => {
        mockMediaRecorderInstance.onstop?.();
      });

      await waitFor(() => {
        expect(result.current.isPreviewMode).toBe(true);
      });

      // Mock play error
      (mockAudio.play as any).mockRejectedValueOnce(new Error('Play failed'));

      await act(() => {
        result.current.playPreview();
      });

      await waitFor(() => {
        expect(result.current.error).toBeTruthy();
      });

      expect(result.current.error).toContain('Failed to play');
    });
  });

  describe('pausePreview', () => {
    it('should pause audio preview', async () => {
      const { result } = renderHook(() => useAudioRecording());

      // Enter preview mode and start playing
      await act(async () => {
        await result.current.startRecording();
      });

      await waitFor(() => {
        expect(result.current.recordingState).toBe('recording');
      });

      const blob = new Blob(['audio data'], { type: 'audio/webm' });
      mockMediaRecorderInstance.ondataavailable?.({ data: blob });

      await act(() => {
        result.current.stopRecording();
      });

      await act(() => {
        mockMediaRecorderInstance.onstop?.();
      });

      await waitFor(() => {
        expect(result.current.isPreviewMode).toBe(true);
      });

      await act(() => {
        result.current.playPreview();
      });

      await waitFor(() => {
        expect(result.current.isPlaying).toBe(true);
      });

      // Pause preview
      await act(() => {
        result.current.pausePreview();
      });

      expect(mockAudio.pause).toHaveBeenCalled();
      expect(result.current.isPlaying).toBe(false);
    });
  });

  describe('clearPreview', () => {
    it('should clear preview and return to idle', async () => {
      const { result } = renderHook(() => useAudioRecording());

      // Enter preview mode
      await act(async () => {
        await result.current.startRecording();
      });

      await waitFor(() => {
        expect(result.current.recordingState).toBe('recording');
      });

      const blob = new Blob(['audio data'], { type: 'audio/webm' });
      mockMediaRecorderInstance.ondataavailable?.({ data: blob });

      await act(() => {
        result.current.stopRecording();
      });

      await act(() => {
        mockMediaRecorderInstance.onstop?.();
      });

      await waitFor(() => {
        expect(result.current.isPreviewMode).toBe(true);
      });

      // Clear preview
      await act(() => {
        result.current.clearPreview();
      });

      expect(result.current.recordingState).toBe('idle');
      expect(result.current.audioBlob).toBeNull();
      expect(result.current.audioUrl).toBeNull();
      expect(result.current.isPreviewMode).toBe(false);
      expect(mockAudio.pause).toHaveBeenCalled();
      expect(global.URL.revokeObjectURL).toHaveBeenCalled();
    });
  });

  describe('confirmRecording', () => {
    it('should return audio blob', async () => {
      const { result } = renderHook(() => useAudioRecording());

      // Enter preview mode
      await act(async () => {
        await result.current.startRecording();
      });

      await waitFor(() => {
        expect(result.current.recordingState).toBe('recording');
      });

      const blob = new Blob(['audio data'], { type: 'audio/webm' });
      mockMediaRecorderInstance.ondataavailable?.({ data: blob });

      await act(() => {
        result.current.stopRecording();
      });

      await act(() => {
        mockMediaRecorderInstance.onstop?.();
      });

      await waitFor(() => {
        expect(result.current.isPreviewMode).toBe(true);
      });

      // Confirm recording
      const confirmedBlob = result.current.confirmRecording();

      expect(confirmedBlob).toBeTruthy();
      expect(confirmedBlob).toBe(result.current.audioBlob);
      expect(mockAudio.pause).toHaveBeenCalled();
    });

    it('should return null if no blob available', () => {
      const { result } = renderHook(() => useAudioRecording());

      const confirmedBlob = result.current.confirmRecording();

      expect(confirmedBlob).toBeNull();
    });
  });

  describe('Cleanup on unmount', () => {
    it('should cleanup resources on unmount', async () => {
      const { result, unmount } = renderHook(() => useAudioRecording());

      // Start recording
      await act(async () => {
        await result.current.startRecording();
      });

      await waitFor(() => {
        expect(result.current.recordingState).toBe('recording');
      });

      // Unmount
      unmount();

      // Verify cleanup
      expect(mockMediaRecorderInstance.stop).toHaveBeenCalled();
      expect(mockStream.getTracks()[0].stop).toHaveBeenCalled();
      expect(global.URL.revokeObjectURL).toHaveBeenCalled();
    });

    it('should revoke object URL on unmount', async () => {
      const { result, unmount } = renderHook(() => useAudioRecording());

      // Enter preview mode first
      await act(async () => {
        await result.current.startRecording();
      });

      await waitFor(() => {
        expect(result.current.recordingState).toBe('recording');
      });

      const blob = new Blob(['audio data'], { type: 'audio/webm' });
      mockMediaRecorderInstance.ondataavailable?.({ data: blob });

      await act(() => {
        result.current.stopRecording();
      });

      await act(() => {
        mockMediaRecorderInstance.onstop?.();
      });

      await waitFor(() => {
        expect(result.current.isPreviewMode).toBe(true);
      });

      const audioUrl = result.current.audioUrl;

      // Unmount
      unmount();

      expect(global.URL.revokeObjectURL).toHaveBeenCalledWith(audioUrl);
    });
  });

  describe('Timer functionality', () => {
    it('should increment duration during recording', async () => {
      vi.useFakeTimers();
      const { result } = renderHook(() => useAudioRecording());

      await act(async () => {
        await result.current.startRecording();
      });

      await waitFor(() => {
        expect(result.current.recordingState).toBe('recording');
      });

      // Advance time
      act(() => {
        vi.advanceTimersByTime(2100); // 2.1 seconds
      });

      // Duration should be approximately 2 seconds (floored)
      await waitFor(() => {
        expect(result.current.duration).toBeGreaterThanOrEqual(2);
      });
      expect(result.current.duration).toBeLessThan(3);

      vi.useRealTimers();
    });

    it('should pause duration timer when paused', async () => {
      vi.useFakeTimers();
      const { result } = renderHook(() => useAudioRecording());

      await act(async () => {
        await result.current.startRecording();
      });

      await waitFor(() => {
        expect(result.current.recordingState).toBe('recording');
      });

      // Record for 1 second
      act(() => {
        vi.advanceTimersByTime(1000);
      });

      await waitFor(() => {
        expect(result.current.duration).toBeGreaterThanOrEqual(1);
      });

      const durationBeforePause = result.current.duration;

      // Pause
      await act(() => {
        result.current.pauseRecording();
      });

      await waitFor(() => {
        expect(result.current.recordingState).toBe('paused');
      });

      // Advance time while paused
      act(() => {
        vi.advanceTimersByTime(2000);
      });

      // Duration should not increase while paused
      await waitFor(() => {
        expect(result.current.duration).toBe(durationBeforePause);
      });

      vi.useRealTimers();
    });
  });

  describe('Error handling', () => {
    it('should handle audio loading error', async () => {
      const { result } = renderHook(() => useAudioRecording());

      // Enter preview mode
      await act(async () => {
        await result.current.startRecording();
      });

      await waitFor(() => {
        expect(result.current.recordingState).toBe('recording');
      });

      const blob = new Blob(['audio data'], { type: 'audio/webm' });
      mockMediaRecorderInstance.ondataavailable?.({ data: blob });

      await act(() => {
        result.current.stopRecording();
      });

      await act(() => {
        mockMediaRecorderInstance.onstop?.();
      });

      await waitFor(() => {
        expect(result.current.isPreviewMode).toBe(true);
      });

      // Trigger error
      await act(() => {
        if (mockAudio.onerror) {
          mockAudio.onerror(new Event('error'));
        }
      });

      await waitFor(() => {
        expect(result.current.error).toContain('Failed to load audio preview');
      });
    });

    it('should handle audio ended event', async () => {
      const { result } = renderHook(() => useAudioRecording());

      // Enter preview mode and start playing
      await act(async () => {
        await result.current.startRecording();
      });

      await waitFor(() => {
        expect(result.current.recordingState).toBe('recording');
      });

      const blob = new Blob(['audio data'], { type: 'audio/webm' });
      mockMediaRecorderInstance.ondataavailable?.({ data: blob });

      await act(() => {
        result.current.stopRecording();
      });

      await act(() => {
        mockMediaRecorderInstance.onstop?.();
      });

      await waitFor(() => {
        expect(result.current.isPreviewMode).toBe(true);
      });

      await act(() => {
        result.current.playPreview();
      });

      await waitFor(() => {
        expect(result.current.isPlaying).toBe(true);
      });

      // Trigger ended
      await act(() => {
        if (mockAudio.onended) {
          mockAudio.onended(new Event('ended'));
        }
      });

      await waitFor(() => {
        expect(result.current.isPlaying).toBe(false);
        expect(result.current.currentTime).toBe(0);
      });
    });
  });
});
