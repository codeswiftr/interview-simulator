import { useEffect, useRef, useState, useCallback } from 'react';
import { Mic, Square, Play, Pause, X } from 'lucide-react';
import type { RecordingState } from '../../hooks/useAudioRecording';
import type { SpeechRecognition, SpeechRecognitionEvent } from '../../types/speech';
import { getSpeechRecognitionConstructor } from '../../types/speech';

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
    <div className="w-full bg-surface-primary dark:bg-surface-tertiary rounded-2xl shadow-xl overflow-hidden border border-border-light relative">
      {/* Visualizer Area */}
      <div className="relative h-48 bg-gradient-to-b from-slate-900 to-slate-800 flex items-center justify-center overflow-hidden">
        {mediaStream ? (
          <canvas
            ref={canvasRef}
            width={600}
            height={192}
            className="w-full h-full opacity-80"
          />
        ) : (
          <div className="text-white/20 flex flex-col items-center gap-2">
            <Mic size={48} />
            <span className="text-sm font-medium uppercase tracking-wider">Ready to Record</span>
          </div>
        )}

        {/* Live Transcript Overlay */}
        {isRecording && transcript && (
          <div className="absolute bottom-4 left-4 right-4 bg-black/60 backdrop-blur-sm p-3 rounded-lg border border-white/10">
            <p className="text-white/90 text-sm font-mono truncate animate-pulse">
              &gt; {transcript}
            </p>
          </div>
        )}
      </div>

      {/* Controls Area */}
      <div className="p-6 bg-surface-secondary/50 backdrop-blur-md">
        {/* Timer & Status */}
        <div className="flex justify-between items-center mb-6">
          <div className="flex items-center gap-2">
            {isRecording && (
              <span className="relative flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-status-error opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3 w-3 bg-status-error"></span>
              </span>
            )}
            <span className={`font-mono text-xl font-bold ${isRecording ? 'text-status-error' : 'text-text-primary'}`}>
              {formatTime(duration)}
            </span>
          </div>
          <div className="text-xs font-bold text-text-tertiary uppercase tracking-wider">
            {recordingState === 'idle' ? 'STANDBY' : recordingState.toUpperCase()}
          </div>
        </div>

        {/* Main Controls */}
        <div className="flex items-center justify-center gap-6">
          {recordingState === 'idle' ? (
            <button
              onClick={onStart}
              disabled={disabled}
              className="group relative flex items-center justify-center h-16 w-16 rounded-full bg-electric-blue text-white shadow-lg hover:bg-sky-500 hover:scale-110 active:scale-95 transition-all duration-200"
              title="Start recording"
            >
              <Mic size={28} />
              <div className="absolute inset-0 rounded-full border-2 border-white/20 group-hover:border-white/40 transition-colors"></div>
            </button>
          ) : (
            <>
              <button
                onClick={onCancel}
                className="p-3 rounded-full text-text-tertiary hover:bg-status-error/10 hover:text-status-error transition-colors"
                title="Cancel"
              >
                <X size={24} />
              </button>

              {recordingState === 'recording' ? (
                <button
                  onClick={onPause}
                  className="p-4 rounded-full bg-surface-tertiary text-text-primary hover:bg-surface-tertiary/80 transition-colors"
                  title="Pause"
                >
                  <Pause size={28} />
                </button>
              ) : (
                <button
                  onClick={onResume}
                  className="p-4 rounded-full bg-surface-tertiary text-text-primary hover:bg-surface-tertiary/80 transition-colors"
                  title="Resume"
                >
                  <Play size={28} />
                </button>
              )}

              <button
                onClick={onStop}
                className="group relative flex items-center justify-center h-16 w-16 rounded-full bg-status-error text-white shadow-lg hover:bg-red-600 hover:scale-110 active:scale-95 transition-all duration-200"
                title="Stop & Save"
              >
                <Square size={24} fill="currentColor" />
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
