import { describe, it, expect } from 'vitest';
import { render, screen } from '../../../test/utils';
import TranscriptionDisplay from '../TranscriptionDisplay';
import type { ProcessingStatus } from '../../../types';

const renderStatus = (status: ProcessingStatus, extras?: Partial<{ transcript: string; error: string }>) =>
  render(
    <TranscriptionDisplay
      processingStatus={status}
      transcript={extras?.transcript}
      processingError={extras?.error}
      questionNumber={1}
    />
  );

describe('TranscriptionDisplay', () => {
  it('renders pending status with helper text', () => {
    renderStatus('pending');

    expect(screen.getByText('Waiting to process...')).toBeInTheDocument();
    expect(screen.getByText(/being processed/i)).toBeInTheDocument();
  });

  it('renders transcribing status', () => {
    renderStatus('transcribing');

    expect(screen.getByText('Transcribing your answer...')).toBeInTheDocument();
  });

  it('renders analyzing status', () => {
    renderStatus('analyzing');

    expect(screen.getByText('Analyzing content...')).toBeInTheDocument();
  });

  it('renders transcript when completed', () => {
    renderStatus('completed', { transcript: 'Completed transcript' });

    expect(screen.getByText('Transcription complete')).toBeInTheDocument();
    expect(screen.getByText('Completed transcript')).toBeInTheDocument();
  });

  it('renders error when failed', () => {
    renderStatus('failed', { error: 'Processing failed' });

    expect(screen.getAllByText('Processing failed')).toHaveLength(2);
    expect(screen.getByRole('alert')).toHaveTextContent('Processing failed');
  });
});
