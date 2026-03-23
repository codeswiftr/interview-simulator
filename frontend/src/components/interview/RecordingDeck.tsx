import { useEffect, useRef, useState, useCallback } from 'react';
import { Mic, Square, Play, Pause, X, SkipForward } from 'lucide-react';
import type { RecordingState } from '../../hooks/useAudioRecording';
import type { SpeechRecognition, SpeechRecognitionEvent } from '../../types/speech';
import { getSpeechRecognitionConstructor } from '../../types/speech';
import { WaveformPlaceholder } from './WaveformPlaceholder';

interface RecordingDeckProps {
  isRecording: boolean;
  recordingState: RecordingState;
  duration: number;
  mediaStream: MediaStream | null;
  onStart: () => void;
  onStop: () => void;
  onPause: () => void;
  onResume: () => void;
  onCancel: () => void;
  onConfirm: () => void;
  onSkip?: () => void;
  disabled?: boolean;
  onTranscriptChange?: (transcript: string) => void;
}

export default function RecordingDeck({
  isRecording,
  recordingState,
  duration,
  mediaStream,
  onStart,
  onStop,
  onPause,
  onResume,
  onCancel,
  onSkip,
  disabled = false,
  onTranscriptChange
}: RecordingDeckProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number | undefined>(undefined);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const [transcript, setTranscript] = useState('');
  const recognitionRef = useRef<SpeechRecognition | null>(null);

  // Audio Visualizer
  useEffect(() => {
    if (!mediaStream || !canvasRef.current) return;

    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    if (!AudioContextClass) return;
    const audioContext = new AudioContextClass();
    const analyser = audioContext.createAnalyser();
    const source = audioContext.createMediaStreamSource(mediaStream);

    source.connect(analyser);
    analyser.fftSize = 256;

    analyserRef.current = analyser;
    sourceRef.current = source;

    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');

    const draw = () => {
      if (!ctx) return;
      animationRef.current = requestAnimationFrame(draw);

      analyser.getByteFrequencyData(dataArray);

      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const barWidth = (canvas.width / bufferLength) * 2.5;
      let barHeight;
      let x = 0;

      for (let i = 0; i < bufferLength; i++) {
        barHeight = dataArray[i] / 2;

        const gradient = ctx.createLinearGradient(0, 0, 0, canvas.height);
        gradient.addColorStop(0, '#38bdf8'); // sky-400
        gradient.addColorStop(1, '#6366f1'); // indigo-500

        ctx.fillStyle = gradient;
        ctx.fillRect(x, canvas.height - barHeight, barWidth, barHeight);

        x += barWidth + 1;
      }
    };

    draw();

    return () => {
      if (animationRef.current) cancelAnimationFrame(animationRef.current);
      if (sourceRef.current) sourceRef.current.disconnect();
      if (audioContext.state !== 'closed') audioContext.close();
    };
  }, [mediaStream]);

  // Speech Recognition (Live Transcription)
  // Memoize callback to avoid dependency issues
  const handleTranscriptChange = useCallback((newTranscript: string) => {
    if (onTranscriptChange) {
      onTranscriptChange(newTranscript);
    }
  }, [onTranscriptChange]);

  useEffect(() => {
    if (typeof window === 'undefined') return;

    // Check availability
    const SpeechRecognitionClass = getSpeechRecognitionConstructor();

    if (SpeechRecognitionClass && isRecording) {
      const recognition = new SpeechRecognitionClass();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'en-US';

      recognition.onresult = (event: SpeechRecognitionEvent) => {
        let currentTranscript = '';
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          if (event.results[i].isFinal) {
            currentTranscript += event.results[i][0].transcript;
          } else {
            currentTranscript += event.results[i][0].transcript;
          }
        }
        setTranscript(currentTranscript);
        // Notify parent component of transcript changes
        handleTranscriptChange(currentTranscript);
      };

      recognition.start();
      recognitionRef.current = recognition;
    } else {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    }

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, [isRecording, handleTranscriptChange]);

  // Format time
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div
      className="recording-deck w-full rounded-2xl shadow-xl overflow-hidden relative"
      role="region"
      aria-label="Audio recording interface"
    >
      {recordingState === 'idle' ? (
        /* Idle State - Prominent CTA */
        <div className="p-6 sm:p-10 flex flex-col items-center justify-center gap-4 sm:gap-6 bg-gradient-to-b from-slate-900 via-slate-800 to-slate-900 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950 min-h-[240px] sm:min-h-[280px]">
          {/* Pulsing mic icon */}
          <div className="relative">
            <div className="absolute inset-0 bg-electric-blue/20 rounded-full blur-2xl animate-pulse" />
            <div className="relative bg-electric-blue/10 p-5 sm:p-6 rounded-full border-2 border-electric-blue/30">
              <Mic size={40} className="text-electric-blue sm:hidden" />
              <Mic size={48} className="text-electric-blue hidden sm:block" />
            </div>
          </div>

          {/* Clear CTA text */}
          <div className="text-center space-y-2">
            <h3 className="text-lg sm:text-xl font-bold text-white">Ready to answer?</h3>
            <p className="text-sm text-white/60 max-w-xs">
              Click the button below to start recording your response
            </p>
          </div>

          {/* Prominent start button */}
          <button
            onClick={onStart}
            disabled={disabled}
            className="group relative flex items-center gap-3 px-6 sm:px-8 py-3 sm:py-4 bg-electric-blue hover:bg-sky-500 text-white rounded-xl font-semibold shadow-xl hover:shadow-electric-blue/40 hover:scale-105 active:scale-95 transition-all duration-200 min-h-[44px] disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label="Start recording"
          >
            <Mic size={20} className="sm:hidden" />
            <Mic size={24} className="hidden sm:block" />
            <span className="text-sm sm:text-base">Start Recording</span>

            {/* Shine effect on hover */}
            <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-1000 overflow-hidden" />
          </button>

          {/* Keyboard shortcut hint - hidden on mobile for space */}
          <p className="hidden sm:flex text-xs text-white/40 items-center gap-2">
            <kbd className="px-2 py-1 bg-white/10 rounded border border-white/20 text-[10px] font-mono">Space</kbd>
            <span>to start</span>
          </p>

          {/* Mobile-only Skip button - integrated for visibility without scroll */}
          {onSkip && (
            <button
              onClick={onSkip}
              disabled={disabled}
              className="sm:hidden mt-1 text-sm text-white/40 hover:text-white/60 flex items-center gap-1.5 py-2 min-h-[44px]"
            >
              <SkipForward size={14} />
              Skip Question
            </button>
          )}
        </div>
      ) : (
        /* Recording State */
        <>
          {/* Visualizer Area - Reduced height */}
          <div className="relative h-32 sm:h-40 bg-gradient-to-b from-slate-900 via-slate-800 to-slate-900 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950 flex items-center justify-center overflow-hidden">
            {mediaStream ? (
              <canvas
                ref={canvasRef}
                width={600}
                height={160}
                className="w-full h-full opacity-80"
                style={{ maxWidth: '100%', display: 'block' }}
                aria-hidden="true"
              />
            ) : (
              /* Animated placeholder when no audio stream */
              <WaveformPlaceholder isActive={isRecording} />
            )}

            {/* Live Transcript Overlay - Better positioning */}
            {isRecording && transcript && (
              <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/90 via-black/70 to-transparent p-3 sm:p-4 pt-6 sm:pt-8">
                <div className="flex items-start gap-2">
                  <div className="flex-shrink-0 mt-1">
                    <div className="w-2 h-2 bg-electric-blue rounded-full animate-pulse" />
                  </div>
                  <p className="text-white/90 text-xs sm:text-sm font-mono leading-relaxed line-clamp-2">
                    {transcript}
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Controls Area */}
          <div className="p-4 sm:p-6 bg-white dark:bg-surface-secondary/50 backdrop-blur-md">
            {/* Timer & Status */}
            <div className="flex justify-between items-center mb-5 sm:mb-6">
              <div className="flex items-center gap-2">
                {isRecording && (
                  <span className="relative flex h-3 w-3" aria-hidden="true">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-status-error opacity-75" />
                    <span className="relative inline-flex rounded-full h-3 w-3 bg-status-error" />
                  </span>
                )}
                <span
                  className={`font-mono text-lg sm:text-xl font-bold tabular-nums ${isRecording ? 'text-status-error' : 'text-text-primary'}`}
                  aria-label={`Recording duration: ${Math.floor(duration / 60)} minutes and ${duration % 60} seconds`}
                >
                  {formatTime(duration)}
                </span>
              </div>
              <div className="text-xs font-bold text-text-tertiary uppercase tracking-wider">
                {recordingState.toUpperCase()}
              </div>
            </div>

            {/* Screen reader status */}
            <div className="sr-only" aria-live="assertive">
              {recordingState === 'recording' && 'Recording in progress'}
              {recordingState === 'paused' && 'Recording paused'}
            </div>

            {/* Main Controls - WCAG compliant touch targets */}
            <div className="flex items-center justify-center gap-3 sm:gap-4">
              {/* Cancel - Tertiary action */}
              <button
                onClick={onCancel}
                className="p-3 sm:p-4 rounded-full text-text-tertiary hover:bg-status-error/10 hover:text-status-error transition-all min-w-[44px] min-h-[44px] flex items-center justify-center"
                aria-label="Cancel recording"
                title="Cancel"
              >
                <X size={20} className="sm:hidden" aria-hidden="true" />
                <X size={24} className="hidden sm:block" aria-hidden="true" />
              </button>

              {/* Pause/Resume - Secondary action */}
              <button
                onClick={recordingState === 'recording' ? onPause : onResume}
                className="p-4 sm:p-5 rounded-full bg-surface-tertiary dark:bg-white/5 text-text-primary hover:bg-surface-secondary dark:hover:bg-white/10 hover:scale-105 active:scale-95 transition-all shadow-md min-w-[44px] min-h-[44px] flex items-center justify-center"
                aria-label={recordingState === 'recording' ? 'Pause recording' : 'Resume recording'}
                title={recordingState === 'recording' ? 'Pause' : 'Resume'}
              >
                {recordingState === 'recording' ? (
                  <>
                    <Pause size={22} className="sm:hidden" aria-hidden="true" />
                    <Pause size={28} className="hidden sm:block" aria-hidden="true" />
                  </>
                ) : (
                  <>
                    <Play size={22} className="sm:hidden ml-0.5" aria-hidden="true" />
                    <Play size={28} className="hidden sm:block ml-0.5" aria-hidden="true" />
                  </>
                )}
              </button>

              {/* Stop - Primary action */}
              <button
                onClick={onStop}
                className="group relative flex items-center justify-center h-12 w-12 sm:h-16 sm:w-16 rounded-full bg-status-error text-white shadow-lg hover:shadow-xl hover:shadow-status-error/40 hover:scale-110 active:scale-95 transition-all duration-200 min-w-[48px] min-h-[48px]"
                aria-label="Stop and save recording"
                title="Stop & Save"
              >
                <Square size={18} className="sm:hidden" fill="currentColor" aria-hidden="true" />
                <Square size={24} className="hidden sm:block" fill="currentColor" aria-hidden="true" />
                <div className="absolute inset-0 rounded-full border-2 border-white/20 group-hover:border-white/40 transition-colors" />
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
