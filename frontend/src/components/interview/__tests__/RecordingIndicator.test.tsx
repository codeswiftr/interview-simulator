import { describe, it, expect } from 'vitest';
import { render, screen } from '../../../test/utils';
import RecordingIndicator from '../RecordingIndicator';


describe('RecordingIndicator', () => {
  it('renders idle state when not recording', () => {
    render(<RecordingIndicator isRecording={false} duration={0} />);

    expect(screen.getByText('Ready to Record')).toBeInTheDocument();
    expect(screen.getByText(/Click the microphone button/i)).toBeInTheDocument();
  });

  it('renders recording state with duration', () => {
    render(<RecordingIndicator isRecording={true} duration={65} />);

    expect(screen.getByText('Recording')).toBeInTheDocument();
    expect(screen.getByText('01:05')).toBeInTheDocument();
  });

  it('hides idle state when showIdleState is false', () => {
    const { container } = render(
      <RecordingIndicator isRecording={false} duration={0} showIdleState={false} />
    );

    expect(container.firstChild).toBeNull();
  });
});
