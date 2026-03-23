import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor, act } from '@/test/utils';
import VideoRecordingDeck from '../VideoRecordingDeck';

// ── API mock ─────────────────────────────────────────────────────────────────
vi.mock('../../../lib/api', () => ({
  videoAPI: {
    uploadVideo: vi.fn(),
  },
}));

import { videoAPI } from '../../../lib/api';
const mockUploadVideo = vi.mocked(videoAPI.uploadVideo);

// ── MediaRecorder mock ────────────────────────────────────────────────────────
class MockMediaRecorder {
  static isTypeSupported = () => true;
  state: string = 'inactive';
  ondataavailable: ((e: { data: Blob }) => void) | null = null;
  onstop: (() => void) | null = null;

  start() {
    this.state = 'recording';
  }

  stop() {
    this.state = 'inactive';
    // Emit a data chunk then fire onstop
    if (this.ondataavailable) {
      this.ondataavailable({ data: new Blob(['chunk'], { type: 'video/webm' }) });
    }
    if (this.onstop) {
      this.onstop();
    }
  }

  abort() {
    this.state = 'inactive';
  }
}

// ── getUserMedia mock helpers ─────────────────────────────────────────────────
const MOCK_STREAM = {
  getTracks: () => [{ stop: vi.fn() }],
} as unknown as MediaStream;

function mockGetUserMediaSuccess() {
  Object.defineProperty(navigator, 'mediaDevices', {
    value: { getUserMedia: vi.fn().mockResolvedValue(MOCK_STREAM) },
    writable: true,
    configurable: true,
  });
}

function mockGetUserMediaDenied() {
  Object.defineProperty(navigator, 'mediaDevices', {
    value: {
      getUserMedia: vi.fn().mockRejectedValue(new DOMException('Permission denied', 'NotAllowedError')),
    },
    writable: true,
    configurable: true,
  });
}

// ── Default props ─────────────────────────────────────────────────────────────
const DEFAULT_PROPS = {
  responseId: 'resp-test-001',
  onUploadComplete: vi.fn(),
  onUploadError: vi.fn(),
  onCancel: vi.fn(),
};

// ── Suite ─────────────────────────────────────────────────────────────────────
describe('VideoRecordingDeck', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Install MediaRecorder mock
    vi.stubGlobal('MediaRecorder', MockMediaRecorder);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  // ── Test 1 ────────────────────────────────────────────────────────────────
  it('renders "Enable Camera" button in idle state', () => {
    render(<VideoRecordingDeck {...DEFAULT_PROPS} />);

    expect(screen.getByRole('button', { name: /enable camera/i })).toBeInTheDocument();
  });

  // ── Test 2 ────────────────────────────────────────────────────────────────
  it('calls getUserMedia when Enable Camera is clicked', async () => {
    mockGetUserMediaSuccess();
    render(<VideoRecordingDeck {...DEFAULT_PROPS} />);

    fireEvent.click(screen.getByRole('button', { name: /enable camera/i }));

    await waitFor(() => {
      expect(navigator.mediaDevices.getUserMedia).toHaveBeenCalledWith({
        video: true,
        audio: true,
      });
    });
  });

  // ── Test 3 ────────────────────────────────────────────────────────────────
  it('shows camera preview (video element) after permission is granted', async () => {
    mockGetUserMediaSuccess();
    render(<VideoRecordingDeck {...DEFAULT_PROPS} />);

    fireEvent.click(screen.getByRole('button', { name: /enable camera/i }));

    await waitFor(() => {
      expect(screen.getByLabelText('Camera preview')).toBeInTheDocument();
    });
  });

  // ── Test 4 ────────────────────────────────────────────────────────────────
  it('shows recording controls after Start Recording is clicked', async () => {
    mockGetUserMediaSuccess();
    render(<VideoRecordingDeck {...DEFAULT_PROPS} />);

    fireEvent.click(screen.getByRole('button', { name: /enable camera/i }));

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /start recording/i })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: /start recording/i }));

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /stop and save recording/i })).toBeInTheDocument();
    });
  });

  // ── Test 5 ────────────────────────────────────────────────────────────────
  it('calls videoAPI.uploadVideo when Stop is clicked', async () => {
    mockGetUserMediaSuccess();
    mockUploadVideo.mockResolvedValue({
      video_url: 'https://cdn.example.com/video.webm',
      file_size_bytes: 1024,
      filename: 'video.webm',
    });

    render(<VideoRecordingDeck {...DEFAULT_PROPS} />);

    // Enable camera → start → stop
    fireEvent.click(screen.getByRole('button', { name: /enable camera/i }));
    await waitFor(() => screen.getByRole('button', { name: /start recording/i }));
    fireEvent.click(screen.getByRole('button', { name: /start recording/i }));
    await waitFor(() => screen.getByRole('button', { name: /stop and save recording/i }));

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /stop and save recording/i }));
    });

    await waitFor(() => {
      expect(mockUploadVideo).toHaveBeenCalledWith(
        'resp-test-001',
        expect.any(Blob),
      );
    });
  });

  // ── Test 6 ────────────────────────────────────────────────────────────────
  it('calls onUploadComplete with videoUrl after successful upload', async () => {
    const onUploadComplete = vi.fn();
    mockGetUserMediaSuccess();
    mockUploadVideo.mockResolvedValue({
      video_url: 'https://cdn.example.com/my-video.webm',
      file_size_bytes: 2048,
      filename: 'my-video.webm',
    });

    render(<VideoRecordingDeck {...DEFAULT_PROPS} onUploadComplete={onUploadComplete} />);

    fireEvent.click(screen.getByRole('button', { name: /enable camera/i }));
    await waitFor(() => screen.getByRole('button', { name: /start recording/i }));
    fireEvent.click(screen.getByRole('button', { name: /start recording/i }));
    await waitFor(() => screen.getByRole('button', { name: /stop and save recording/i }));

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /stop and save recording/i }));
    });

    await waitFor(() => {
      expect(onUploadComplete).toHaveBeenCalledWith('https://cdn.example.com/my-video.webm');
    });
  });

  // ── Test 7 ────────────────────────────────────────────────────────────────
  it('shows error state when upload fails', async () => {
    const onUploadError = vi.fn();
    mockGetUserMediaSuccess();
    mockUploadVideo.mockRejectedValue(new Error('Network timeout'));

    render(<VideoRecordingDeck {...DEFAULT_PROPS} onUploadError={onUploadError} />);

    fireEvent.click(screen.getByRole('button', { name: /enable camera/i }));
    await waitFor(() => screen.getByRole('button', { name: /start recording/i }));
    fireEvent.click(screen.getByRole('button', { name: /start recording/i }));
    await waitFor(() => screen.getByRole('button', { name: /stop and save recording/i }));

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /stop and save recording/i }));
    });

    await waitFor(() => {
      expect(screen.getByText('Upload failed')).toBeInTheDocument();
      expect(screen.getByText('Network timeout')).toBeInTheDocument();
    });

    expect(onUploadError).toHaveBeenCalledWith('Network timeout');
  });

  // ── Test 8 ────────────────────────────────────────────────────────────────
  it('shows camera-denied fallback when getUserMedia is rejected', async () => {
    mockGetUserMediaDenied();
    render(<VideoRecordingDeck {...DEFAULT_PROPS} />);

    fireEvent.click(screen.getByRole('button', { name: /enable camera/i }));

    await waitFor(() => {
      expect(screen.getByText('Camera access denied')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /continue without video/i })).toBeInTheDocument();
    });
  });

  // ── Test 9 (bonus) ────────────────────────────────────────────────────────
  it('"Continue without video" button calls onCancel', async () => {
    const onCancel = vi.fn();
    mockGetUserMediaDenied();
    render(<VideoRecordingDeck {...DEFAULT_PROPS} onCancel={onCancel} />);

    fireEvent.click(screen.getByRole('button', { name: /enable camera/i }));
    await waitFor(() => screen.getByRole('button', { name: /continue without video/i }));

    fireEvent.click(screen.getByRole('button', { name: /continue without video/i }));
    expect(onCancel).toHaveBeenCalledTimes(1);
  });

  // ── Test 10 (bonus) ───────────────────────────────────────────────────────
  it('shows a retry button in error state', async () => {
    mockGetUserMediaSuccess();
    mockUploadVideo.mockRejectedValue(new Error('Server error'));

    render(<VideoRecordingDeck {...DEFAULT_PROPS} />);

    fireEvent.click(screen.getByRole('button', { name: /enable camera/i }));
    await waitFor(() => screen.getByRole('button', { name: /start recording/i }));
    fireEvent.click(screen.getByRole('button', { name: /start recording/i }));
    await waitFor(() => screen.getByRole('button', { name: /stop and save recording/i }));

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /stop and save recording/i }));
    });

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /retry recording/i })).toBeInTheDocument();
    });
  });
});
