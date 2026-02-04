import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '../../../test/utils';
import userEvent from '@testing-library/user-event';
import TranscriptionPanel from '../TranscriptionPanel';

const mockUseInterview = vi.fn();

vi.mock('../../../contexts/InterviewContext', () => ({
  useInterview: () => mockUseInterview(),
}));

describe('TranscriptionPanel', () => {
  it('returns null when there are no submitted responses', () => {
    mockUseInterview.mockReturnValue({
      submittedResponses: [],
      showTranscriptionPanel: false,
      setShowTranscriptionPanel: vi.fn(),
    });

    const { container } = render(<TranscriptionPanel />);
    expect(container.firstChild).toBeNull();
  });

  it('shows processing badge when responses are still processing', () => {
    mockUseInterview.mockReturnValue({
      submittedResponses: [
        { id: 'r1', questionIndex: 0, processingStatus: 'transcribing' },
      ],
      showTranscriptionPanel: false,
      setShowTranscriptionPanel: vi.fn(),
    });

    render(<TranscriptionPanel />);
    expect(screen.getByText(/Processing/i)).toBeInTheDocument();
  });

  it('toggles panel when button is clicked', async () => {
    const setShow = vi.fn();
    const user = userEvent.setup();

    mockUseInterview.mockReturnValue({
      submittedResponses: [
        { id: 'r1', questionIndex: 0, processingStatus: 'completed', transcript: 'Hi' },
      ],
      showTranscriptionPanel: false,
      setShowTranscriptionPanel: setShow,
    });

    render(<TranscriptionPanel />);

    await user.click(screen.getByRole('button', { name: /Your Transcriptions/i }));
    expect(setShow).toHaveBeenCalledWith(true);
  });

  it('renders transcription list when panel is open', () => {
    mockUseInterview.mockReturnValue({
      submittedResponses: [
        { id: 'r1', questionIndex: 0, processingStatus: 'completed', transcript: 'Hello' },
        { id: 'r2', questionIndex: 1, processingStatus: 'failed', processingError: 'No audio' },
      ],
      showTranscriptionPanel: true,
      setShowTranscriptionPanel: vi.fn(),
    });

    render(<TranscriptionPanel />);

    expect(screen.getByText('Answer 1 Transcription')).toBeInTheDocument();
    expect(screen.getByText('Hello')).toBeInTheDocument();
    expect(screen.getByText('Processing failed')).toBeInTheDocument();
  });
});
