import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import axios from 'axios';

// Mock axios before importing the api module
vi.mock('axios', () => {
  const mockAxiosInstance = {
    post: vi.fn().mockResolvedValue({ data: { audio_url: 'test-url' }, status: 200 }),
    get: vi.fn().mockResolvedValue({ data: {}, status: 200 }),
    patch: vi.fn().mockResolvedValue({ data: {}, status: 200 }),
    delete: vi.fn().mockResolvedValue({ data: {}, status: 200 }),
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() },
    },
  };

  return {
    default: {
      create: vi.fn(() => mockAxiosInstance),
      post: vi.fn(),
    },
  };
});

describe('uploadAPI', () => {
  let uploadAPI: typeof import('../api').uploadAPI;
  let mockAxiosInstance: ReturnType<typeof axios.create>;

  beforeEach(async () => {
    vi.resetModules();
    const apiModule = await import('../api');
    uploadAPI = apiModule.uploadAPI;
    mockAxiosInstance = (axios.create as ReturnType<typeof vi.fn>).mock.results[0].value;
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('uploadAudio', () => {
    /**
     * REGRESSION TEST: Audio upload Content-Type header
     *
     * This test ensures we never regress on the audio upload issue where
     * sending FormData with 'Content-Type: application/json' header causes
     * a 422 Unprocessable Content error from the backend.
     *
     * The fix: Set 'Content-Type': undefined in the request config to let
     * the browser automatically set 'multipart/form-data' with boundary.
     *
     * Issue: Audio uploads were failing with 422 because axios was using
     * its default 'application/json' Content-Type for FormData uploads.
     */
    it('should set Content-Type to undefined to allow browser to set multipart/form-data', async () => {
      const mockFile = new File(['test'], 'test.webm', { type: 'audio/webm' });

      await uploadAPI.uploadAudio(mockFile, 'session-123', 'question-456');

      // Verify axios.post was called with the correct config
      expect(mockAxiosInstance.post).toHaveBeenCalledWith(
        '/upload/audio',
        expect.any(FormData),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Content-Type': undefined, // CRITICAL: Must be undefined, not 'application/json'
          }),
        })
      );
    });

    it('should NOT use application/json Content-Type for FormData uploads', async () => {
      const mockFile = new File(['test'], 'test.webm', { type: 'audio/webm' });

      await uploadAPI.uploadAudio(mockFile, 'session-123', 'question-456');

      const callArgs = (mockAxiosInstance.post as ReturnType<typeof vi.fn>).mock.calls[0];
      const config = callArgs[2];

      // Ensure Content-Type is explicitly undefined (not the default 'application/json')
      expect(config.headers['Content-Type']).toBeUndefined();
      expect(config.headers['Content-Type']).not.toBe('application/json');
    });

    it('should include all required form fields in FormData', async () => {
      const mockFile = new File(['audio data'], 'recording.webm', { type: 'audio/webm' });

      await uploadAPI.uploadAudio(mockFile, 'session-id-123', 'question-id-456');

      const callArgs = (mockAxiosInstance.post as ReturnType<typeof vi.fn>).mock.calls[0];
      const formData = callArgs[1] as FormData;

      expect(formData.get('file')).toBeInstanceOf(File);
      expect(formData.get('session_id')).toBe('session-id-123');
      expect(formData.get('question_id')).toBe('question-id-456');
    });

    it('should have extended timeout for large audio files', async () => {
      const mockFile = new File(['test'], 'test.webm', { type: 'audio/webm' });

      await uploadAPI.uploadAudio(mockFile, 'session-123', 'question-456');

      const callArgs = (mockAxiosInstance.post as ReturnType<typeof vi.fn>).mock.calls[0];
      const config = callArgs[2];

      // Should have 60 second timeout for large audio files
      expect(config.timeout).toBe(60000);
    });
  });
});
