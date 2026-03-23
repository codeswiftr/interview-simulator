import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@/test/utils';
import RecordingSection from '../RecordingSection';

// ── InterviewContext mock ─────────────────────────────────────────────────────
// Path is resolved relative to this test file: ../../../contexts/InterviewContext
vi.mock('../../../contexts/InterviewContext', () => ({
  useInterview: vi.fn(),
}));

import { useInterview } from '../../../contexts/InterviewContext';
const mockUseInterview = vi.mocked(useInterview);

// ── useAudioRecording mock ────────────────────────────────────────────────────
vi.mock('../../../hooks/useAudioRecording', () => ({
  useAudioRecording: vi.fn(),
}));

import { useAudioRecording } from '../../../hooks/useAudioRecording';
const mockUseAudioRecording = vi.mocked(useAudioRecording);

const defaultAudioRecording = {
  duration: 0,
  isRecording: false,
  recordingState: 'idle' as const,
  isPreviewMode: false,
  isPlaying: false,
  currentTime: 0,
  audioDuration: 0,
  startRecording: vi.fn(),
  stopRecording: vi.fn(),
  resetRecording: vi.fn(),
  playPreview: vi.fn(),
  pausePreview: vi.fn(),
  clearPreview: vi.fn(),
  pauseRecording: vi.fn(),
  resumeRecording: vi.fn(),
  confirmRecording: vi.fn(),
  error: null,
  mediaStream: null,
  mimeType: null,
};

// ── useCoachingHint mock ──────────────────────────────────────────────────────
vi.mock('../../../hooks/useCoachingHint', () => ({
  useCoachingHint: vi.fn(() => ({
    hint: null,
    isLoading: false,
    isStreaming: false,
    error: null,
  })),
}));

// ── Analytics mock ────────────────────────────────────────────────────────────
vi.mock('../../../lib/analytics', () => ({
  analytics: { track: vi.fn() },
  Events: {
    RECORDING_STARTED: 'recording_started',
    RECORDING_COMPLETED: 'recording_completed',
  },
}));

// ── VideoRecordingDeck mock ───────────────────────────────────────────────────
vi.mock('../VideoRecordingDeck', () => ({
  default: ({
    responseId,
    onUploadComplete,
    onCancel,
  }: {
    responseId: string;
    onUploadComplete: (url: string) => void;
    onUploadError: (e: string) => void;
    onCancel: () => void;
  }) => (
    <div data-testid="video-recording-deck" data-response-id={responseId}>
      <button onClick={() => onUploadComplete('https://cdn.example.com/video.webm')}>
        Complete Upload
      </button>
      <button onClick={onCancel}>Cancel</button>
    </div>
  ),
}));

// ── Child component mocks (keep tests focused on RecordingSection logic) ───────
vi.mock('../RecordingDeck', () => ({
  default: ({ onStart }: { onStart: () => void }) => (
    <div data-testid="recording-deck">
      <button onClick={onStart}>Start Recording</button>
    </div>
  ),
}));

vi.mock('../AudioPreview', () => ({
  default: () => <div data-testid="audio-preview" />,
}));

vi.mock('../CoachOverlay', () => ({
  default: () => <div data-testid="coach-overlay" />,
}));

// ── Base context factory ──────────────────────────────────────────────────────
function makeContext(overrides: Partial<ReturnType<typeof useInterview>> = {}): ReturnType<typeof useInterview> {
  return {
    session: { id: 'sess-123' } as any,
    currentQuestion: {
      id: 'q-1',
      content: 'Tell me about yourself',
      category: 'behavioral',
      expected_duration_seconds: 120,
    } as any,
    isSubmitting: false,
    submitProgress: null,
    showCoach: false,
    setShowCoach: vi.fn(),
    lastFailedUpload: null,
    lastSubmittedResponseId: null,
    clearLastSubmittedResponseId: vi.fn(),
    handleSubmitAnswer: vi.fn(),
    handleSkipQuestion: vi.fn(),
    handleRetryUpload: vi.fn(),
    handleExit: vi.fn(),
    setError: vi.fn(),
    ...overrides,
  } as any;
}

// ── Suite ─────────────────────────────────────────────────────────────────────
describe('RecordingSection — video recording feature (Sprint 15)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseAudioRecording.mockReturnValue(defaultAudioRecording);
  });

  it('does NOT show video button when lastSubmittedResponseId is null', () => {
    mockUseInterview.mockReturnValue(makeContext({ lastSubmittedResponseId: null }));

    render(<RecordingSection />);

    expect(screen.queryByText(/add video for your last answer/i)).not.toBeInTheDocument();
  });

  it('shows "Add video for your last answer" button when lastSubmittedResponseId is set', () => {
    mockUseInterview.mockReturnValue(makeContext({ lastSubmittedResponseId: 'resp-abc' }));

    render(<RecordingSection />);

    expect(screen.getByText(/add video for your last answer/i)).toBeInTheDocument();
  });

  it('does NOT show video button while recording (isRecording=true)', () => {
    mockUseAudioRecording.mockReturnValue({
      ...defaultAudioRecording,
      isRecording: true,
      recordingState: 'recording' as const,
    });
    mockUseInterview.mockReturnValue(makeContext({ lastSubmittedResponseId: 'resp-abc' }));

    render(<RecordingSection />);

    expect(screen.queryByText(/add video for your last answer/i)).not.toBeInTheDocument();
  });

  it('does NOT show video button while submitting (isSubmitting=true)', () => {
    mockUseInterview.mockReturnValue(
      makeContext({ lastSubmittedResponseId: 'resp-abc', isSubmitting: true })
    );

    render(<RecordingSection />);

    expect(screen.queryByText(/add video for your last answer/i)).not.toBeInTheDocument();
  });

  it('shows VideoRecordingDeck after clicking the add video button', () => {
    mockUseInterview.mockReturnValue(makeContext({ lastSubmittedResponseId: 'resp-abc' }));

    render(<RecordingSection />);

    expect(screen.queryByTestId('video-recording-deck')).not.toBeInTheDocument();

    fireEvent.click(screen.getByText(/add video for your last answer/i));

    expect(screen.getByTestId('video-recording-deck')).toBeInTheDocument();
  });

  it('VideoRecordingDeck receives correct responseId', () => {
    mockUseInterview.mockReturnValue(makeContext({ lastSubmittedResponseId: 'resp-xyz-999' }));

    render(<RecordingSection />);

    fireEvent.click(screen.getByText(/add video for your last answer/i));

    const deck = screen.getByTestId('video-recording-deck');
    expect(deck).toHaveAttribute('data-response-id', 'resp-xyz-999');
  });

  it('calls clearLastSubmittedResponseId on upload complete', () => {
    const clearLastSubmittedResponseId = vi.fn();
    mockUseInterview.mockReturnValue(
      makeContext({ lastSubmittedResponseId: 'resp-abc', clearLastSubmittedResponseId })
    );

    render(<RecordingSection />);

    fireEvent.click(screen.getByText(/add video for your last answer/i));
    fireEvent.click(screen.getByText('Complete Upload'));

    expect(clearLastSubmittedResponseId).toHaveBeenCalledTimes(1);
  });

  it('hides VideoRecordingDeck on upload complete', () => {
    mockUseInterview.mockReturnValue(makeContext({ lastSubmittedResponseId: 'resp-abc' }));

    render(<RecordingSection />);

    fireEvent.click(screen.getByText(/add video for your last answer/i));
    expect(screen.getByTestId('video-recording-deck')).toBeInTheDocument();

    fireEvent.click(screen.getByText('Complete Upload'));

    // showVideoRecorder is set to false; clearLastSubmittedResponseId clears the responseId
    // so the outer condition becomes false and the whole video block disappears
    expect(screen.queryByTestId('video-recording-deck')).not.toBeInTheDocument();
  });

  it('calls clearLastSubmittedResponseId on cancel', () => {
    const clearLastSubmittedResponseId = vi.fn();
    mockUseInterview.mockReturnValue(
      makeContext({ lastSubmittedResponseId: 'resp-abc', clearLastSubmittedResponseId })
    );

    render(<RecordingSection />);

    fireEvent.click(screen.getByText(/add video for your last answer/i));
    fireEvent.click(screen.getByText('Cancel'));

    expect(clearLastSubmittedResponseId).toHaveBeenCalledTimes(1);
  });

  it('hides VideoRecordingDeck on cancel', () => {
    mockUseInterview.mockReturnValue(makeContext({ lastSubmittedResponseId: 'resp-abc' }));

    render(<RecordingSection />);

    fireEvent.click(screen.getByText(/add video for your last answer/i));
    expect(screen.getByTestId('video-recording-deck')).toBeInTheDocument();

    fireEvent.click(screen.getByText('Cancel'));

    expect(screen.queryByTestId('video-recording-deck')).not.toBeInTheDocument();
  });
});
