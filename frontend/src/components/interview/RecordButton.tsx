import { Mic, Square } from 'lucide-react';
import type { RecordingState } from '../../hooks/useAudioRecording';

interface RecordButtonProps {
  recordingState: RecordingState;
  onStart: () => void;
  onStop: () => void;
  disabled?: boolean;
}

export default function RecordButton({
  recordingState,
  onStart,
  onStop,
  disabled = false
}: RecordButtonProps) {
  const isRecording = recordingState === 'recording';

  const handleClick = () => {
    if (isRecording) {
      onStop();
    } else {
      onStart();
    }
  };

  return (
    <button
      onClick={handleClick}
      disabled={disabled}
      className={`
        relative flex items-center justify-center gap-3
        px-8 py-4 rounded-full
        font-semibold text-lg
        transition-all duration-200
        ${isRecording
          ? 'bg-status-error text-white hover:bg-red-600 shadow-lg'
          : 'bg-electric-blue text-white hover:bg-sky-600 shadow-lg hover:shadow-blue-glow'
        }
        ${disabled ? 'opacity-50 cursor-not-allowed' : 'hover:scale-105'}
        focus:outline-none focus:ring-4 focus:ring-electric-blue/50
      `}
    >
      {isRecording ? (
        <>
          <Square size={24} fill="white" />
          <span>Stop Recording</span>
        </>
      ) : (
        <>
          <Mic size={24} />
          <span>Start Recording</span>
        </>
      )}

      {isRecording && (
        <span className="absolute -top-1 -right-1 flex h-4 w-4">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
          <span className="relative inline-flex rounded-full h-4 w-4 bg-red-500"></span>
        </span>
      )}
    </button>
  );
}
