import { useEffect, useRef, useState, useCallback } from 'react';
import { Video, Square, X } from 'lucide-react';
import { videoAPI } from '../../lib/api';

type VideoRecordingState =
  | 'idle'
  | 'requesting'
  | 'ready'
  | 'recording'
  | 'stopped'
  | 'uploading'
  | 'done'
  | 'error'
  | 'denied';

interface VideoRecordingDeckProps {
  responseId: string;
  onUploadComplete: (videoUrl: string) => void;
  onUploadError: (error: string) => void;
  onCancel: () => void;
  disabled?: boolean;
  className?: string;
}

// Format seconds as M:SS (matches RecordingDeck pattern)
function formatTime(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

export default function VideoRecordingDeck({
  responseId,
  onUploadComplete,
  onUploadError,
  onCancel,
  disabled = false,
  className = '',
}: VideoRecordingDeckProps) {
  const [state, setState] = useState<VideoRecordingState>('idle');
  const [duration, setDuration] = useState(0);
  const [errorMessage, setErrorMessage] = useState('');

  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<ReturnType<typeof setInterval> | undefined>(undefined);

  // Cleanup on unmount: stop stream + stop recorder (discard chunks by not handling onstop)
  useEffect(() => {
    return () => {
      clearInterval(timerRef.current);
      if (recorderRef.current && recorderRef.current.state !== 'inactive') {
        // Remove onstop so upload is not triggered during unmount cleanup
        recorderRef.current.onstop = null;
        recorderRef.current.stop();
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop());
      }
    };
  }, []);

  // Attach stream to video element when state changes to ready/recording
  useEffect(() => {
    if ((state === 'ready' || state === 'recording') && videoRef.current && streamRef.current) {
      videoRef.current.srcObject = streamRef.current;
    }
  }, [state]);

  const requestCamera = useCallback(async () => {
    setState('requesting');
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
      streamRef.current = stream;
      setState('ready');
    } catch {
      setState('denied');
    }
  }, []);

  const startRecording = useCallback(() => {
    if (!streamRef.current) return;

    chunksRef.current = [];
    const recorder = new MediaRecorder(streamRef.current);

    recorder.ondataavailable = (e) => {
      if (e.data.size > 0) {
        chunksRef.current.push(e.data);
      }
    };

    recorder.onstop = async () => {
      const blob = new Blob(chunksRef.current, { type: 'video/webm' });
      setState('uploading');
      try {
        const result = await videoAPI.uploadVideo(responseId, blob);
        setState('done');
        onUploadComplete(result.video_url);
      } catch (err) {
        const message =
          err instanceof Error ? err.message : 'Upload failed. Please try again.';
        setErrorMessage(message);
        setState('error');
        onUploadError(message);
      }
    };

    recorderRef.current = recorder;
    recorder.start();
    setState('recording');

    // Start duration timer
    setDuration(0);
    timerRef.current = setInterval(() => {
      setDuration((d) => d + 1);
    }, 1000);
  }, [responseId, onUploadComplete, onUploadError]);

  const stopRecording = useCallback(() => {
    clearInterval(timerRef.current);
    setState('stopped');
    if (recorderRef.current && recorderRef.current.state !== 'inactive') {
      recorderRef.current.stop();
    }
  }, []);

  const handleCancel = useCallback(() => {
    clearInterval(timerRef.current);
    if (recorderRef.current && recorderRef.current.state !== 'inactive') {
      // Detach onstop so upload is never triggered after cancel
      recorderRef.current.onstop = null;
      recorderRef.current.stop();
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    onCancel();
  }, [onCancel]);

  const retryUpload = useCallback(() => {
    setErrorMessage('');
    setState('ready');
  }, []);

  return (
    <div
      className={`w-full rounded-2xl shadow-xl overflow-hidden relative ${className}`}
      role="region"
      aria-label="Video recording interface"
    >
      {/* ── IDLE ────────────────────────────────────────────────── */}
      {state === 'idle' && (
        <div className="p-6 sm:p-10 flex flex-col items-center justify-center gap-4 sm:gap-6 bg-gradient-to-b from-slate-900 via-slate-800 to-slate-900 min-h-[240px] sm:min-h-[280px]">
          <div className="relative">
            <div className="absolute inset-0 bg-emerald-400/20 rounded-full blur-2xl animate-pulse" />
            <div className="relative bg-emerald-400/10 p-5 sm:p-6 rounded-full border-2 border-emerald-400/30">
              <Video size={40} className="text-emerald-400 sm:hidden" aria-hidden="true" />
              <Video size={48} className="text-emerald-400 hidden sm:block" aria-hidden="true" />
            </div>
          </div>

          <div className="text-center space-y-2">
            <h3 className="text-lg sm:text-xl font-bold text-white">Record with camera</h3>
            <p className="text-sm text-white/60 max-w-xs">
              Enable your camera to record a video response
            </p>
          </div>

          <button
            onClick={requestCamera}
            disabled={disabled}
            className="flex items-center gap-3 px-6 sm:px-8 py-3 sm:py-4 bg-emerald-500 hover:bg-emerald-400 text-white rounded-xl font-semibold shadow-xl hover:shadow-emerald-500/40 hover:scale-105 active:scale-95 transition-all duration-200 min-h-[44px] disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label="Enable camera"
          >
            <Video size={20} className="sm:hidden" aria-hidden="true" />
            <Video size={24} className="hidden sm:block" aria-hidden="true" />
            <span className="text-sm sm:text-base">Enable Camera</span>
          </button>
        </div>
      )}

      {/* ── REQUESTING ──────────────────────────────────────────── */}
      {state === 'requesting' && (
        <div className="p-6 sm:p-10 flex flex-col items-center justify-center gap-4 bg-gradient-to-b from-slate-900 via-slate-800 to-slate-900 min-h-[240px]">
          <div className="w-8 h-8 border-2 border-emerald-400 border-t-transparent rounded-full animate-spin" aria-hidden="true" />
          <p className="text-sm text-white/60">Requesting camera access…</p>
        </div>
      )}

      {/* ── DENIED ──────────────────────────────────────────────── */}
      {state === 'denied' && (
        <div className="p-6 sm:p-10 flex flex-col items-center justify-center gap-4 bg-gradient-to-b from-slate-900 via-slate-800 to-slate-900 min-h-[240px]">
          <div className="text-center space-y-2">
            <h3 className="text-lg font-bold text-white">Camera access denied</h3>
            <p className="text-sm text-white/60 max-w-xs">
              Camera permission was denied. Continue with audio-only recording instead?
            </p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={requestCamera}
              className="px-5 py-2.5 bg-emerald-500 hover:bg-emerald-400 text-white rounded-xl font-semibold text-sm transition-all min-h-[44px]"
              aria-label="Try again to enable camera"
            >
              Try Again
            </button>
            <button
              onClick={onCancel}
              className="px-5 py-2.5 text-white/60 hover:text-white hover:bg-white/10 rounded-xl font-semibold text-sm transition-all min-h-[44px]"
              aria-label="Continue without video"
            >
              Continue without video
            </button>
          </div>
        </div>
      )}

      {/* ── READY ───────────────────────────────────────────────── */}
      {state === 'ready' && (
        <>
          <div className="relative bg-slate-900">
            {/* Live camera preview */}
            <video
              ref={videoRef}
              muted
              autoPlay
              playsInline
              className="w-full aspect-video object-cover rounded-t-2xl"
              aria-label="Camera preview"
            />
            {/* Live indicator */}
            <div className="absolute top-3 left-3 flex items-center gap-1.5 bg-black/60 rounded-full px-2.5 py-1">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-400" />
              </span>
              <span className="text-xs font-bold text-emerald-400 uppercase tracking-wider">Live</span>
            </div>
          </div>

          <div className="p-4 sm:p-6 bg-white dark:bg-surface-secondary/50 backdrop-blur-md">
            <div className="flex items-center justify-between mb-4">
              <div className="text-xs font-bold text-text-tertiary uppercase tracking-wider">
                Camera Ready
              </div>
            </div>
            <div className="flex items-center justify-center gap-3">
              <button
                onClick={handleCancel}
                className="p-3 sm:p-4 rounded-full text-text-tertiary hover:bg-status-error/10 hover:text-status-error transition-all min-w-[44px] min-h-[44px] flex items-center justify-center"
                aria-label="Cancel and go back"
                title="Cancel"
              >
                <X size={20} className="sm:hidden" aria-hidden="true" />
                <X size={24} className="hidden sm:block" aria-hidden="true" />
              </button>
              <button
                onClick={startRecording}
                disabled={disabled}
                className="flex items-center gap-3 px-6 py-3 bg-status-error hover:bg-red-600 text-white rounded-xl font-semibold shadow-lg hover:shadow-red-500/40 hover:scale-105 active:scale-95 transition-all duration-200 min-h-[44px] disabled:opacity-50 disabled:cursor-not-allowed"
                aria-label="Start recording"
              >
                <span className="relative flex h-3 w-3" aria-hidden="true">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-white opacity-75" />
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-white" />
                </span>
                <span>Start Recording</span>
              </button>
            </div>
          </div>
        </>
      )}

      {/* ── RECORDING ───────────────────────────────────────────── */}
      {state === 'recording' && (
        <>
          <div className="relative bg-slate-900">
            <video
              ref={videoRef}
              muted
              autoPlay
              playsInline
              className="w-full aspect-video object-cover rounded-t-2xl"
              aria-label="Camera preview"
            />
            {/* Live indicator */}
            <div className="absolute top-3 left-3 flex items-center gap-1.5 bg-black/60 rounded-full px-2.5 py-1">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-400" />
              </span>
              <span className="text-xs font-bold text-emerald-400 uppercase tracking-wider">Live</span>
            </div>
          </div>

          <div className="p-4 sm:p-6 bg-white dark:bg-surface-secondary/50 backdrop-blur-md">
            {/* Timer & status */}
            <div className="flex justify-between items-center mb-5 sm:mb-6">
              <div className="flex items-center gap-2">
                <span className="relative flex h-3 w-3" aria-hidden="true">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-status-error opacity-75" />
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-status-error" />
                </span>
                <span
                  className="font-mono text-lg sm:text-xl font-bold tabular-nums text-status-error"
                  aria-label={`Recording duration: ${Math.floor(duration / 60)} minutes and ${duration % 60} seconds`}
                >
                  {formatTime(duration)}
                </span>
              </div>
              <div className="text-xs font-bold text-text-tertiary uppercase tracking-wider">
                Recording
              </div>
            </div>

            {/* Screen reader live region */}
            <div className="sr-only" aria-live="assertive">Recording in progress</div>

            {/* Controls */}
            <div className="flex items-center justify-center gap-3 sm:gap-4">
              <button
                onClick={handleCancel}
                className="p-3 sm:p-4 rounded-full text-text-tertiary hover:bg-status-error/10 hover:text-status-error transition-all min-w-[44px] min-h-[44px] flex items-center justify-center"
                aria-label="Cancel recording"
                title="Cancel"
              >
                <X size={20} className="sm:hidden" aria-hidden="true" />
                <X size={24} className="hidden sm:block" aria-hidden="true" />
              </button>

              {/* Stop button — red square, matches RecordingDeck */}
              <button
                onClick={stopRecording}
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

      {/* ── UPLOADING ───────────────────────────────────────────── */}
      {(state === 'uploading' || state === 'stopped') && (
        <div className="p-6 sm:p-10 flex flex-col items-center justify-center gap-4 bg-gradient-to-b from-slate-900 via-slate-800 to-slate-900 min-h-[240px]">
          <div className="w-8 h-8 border-2 border-emerald-400 border-t-transparent rounded-full animate-spin" aria-hidden="true" />
          <p className="text-sm text-white/60" aria-live="polite">Uploading video…</p>
        </div>
      )}

      {/* ── DONE ────────────────────────────────────────────────── */}
      {state === 'done' && (
        <div className="p-6 sm:p-10 flex flex-col items-center justify-center gap-4 bg-gradient-to-b from-slate-900 via-slate-800 to-slate-900 min-h-[240px]">
          <div className="bg-emerald-500/20 p-4 rounded-full border-2 border-emerald-500/40">
            <Video size={36} className="text-emerald-400" aria-hidden="true" />
          </div>
          <p className="text-sm text-emerald-400 font-semibold" aria-live="polite">Video uploaded successfully</p>
        </div>
      )}

      {/* ── ERROR ───────────────────────────────────────────────── */}
      {state === 'error' && (
        <div className="p-6 sm:p-10 flex flex-col items-center justify-center gap-4 bg-gradient-to-b from-slate-900 via-slate-800 to-slate-900 min-h-[240px]">
          <div className="text-center space-y-2">
            <h3 className="text-lg font-bold text-white">Upload failed</h3>
            <p className="text-sm text-white/60 max-w-xs" role="alert">
              {errorMessage || 'Something went wrong. Please try again.'}
            </p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={retryUpload}
              className="px-5 py-2.5 bg-emerald-500 hover:bg-emerald-400 text-white rounded-xl font-semibold text-sm transition-all min-h-[44px]"
              aria-label="Retry recording"
            >
              Try Again
            </button>
            <button
              onClick={onCancel}
              className="px-5 py-2.5 text-white/60 hover:text-white hover:bg-white/10 rounded-xl font-semibold text-sm transition-all min-h-[44px]"
              aria-label="Cancel and use audio only"
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
