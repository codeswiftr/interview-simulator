import { useEffect, useRef, useState, useCallback } from 'react';
import { Video, VideoOff, Square, RefreshCw, Check, AlertCircle } from 'lucide-react';

interface VideoRecorderProps {
  onVideoReady: (blob: Blob) => void;
  maxDurationSeconds?: number;
  disabled?: boolean;
}

type PermissionState = 'prompt' | 'granted' | 'denied' | 'unavailable';
type RecordingState = 'idle' | 'recording' | 'preview' | 'error';

/**
 * VideoRecorder Component
 * 
 * Captures webcam video during interview practice using MediaRecorder API.
 * Shows live preview, handles camera permissions, and produces a video Blob.
 * 
 * @example
 * ```tsx
 * <VideoRecorder 
 *   onVideoReady={(blob) => handleUpload(blob)}
 *   maxDurationSeconds={300}
 * />
 * ```
 */
export default function VideoRecorder({
  onVideoReady,
  maxDurationSeconds = 300,
  disabled = false,
}: VideoRecorderProps) {
  // Refs
  const videoRef = useRef<HTMLVideoElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const mimeTypeRef = useRef<string>('video/webm');

  // State
  const [permissionState, setPermissionState] = useState<PermissionState>('prompt');
  const [recordingState, setRecordingState] = useState<RecordingState>('idle');
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [recordedBlob, setRecordedBlob] = useState<Blob | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  // Get supported MIME type
  const getSupportedMimeType = useCallback((): string => {
    const types = [
      'video/webm;codecs=vp9,opus',
      'video/webm;codecs=vp9',
      'video/webm;codecs=vp8,opus',
      'video/webm;codecs=vp8',
      'video/webm',
      'video/mp4',
    ];
    
    for (const type of types) {
      if (MediaRecorder.isTypeSupported(type)) {
        return type;
      }
    }
    return 'video/webm';
  }, []);

  // Format time display (MM:SS)
  const formatTime = useCallback((seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  }, []);

  // Estimate file size (rough approximation)
  const estimateFileSize = useCallback((seconds: number): string => {
    // WebM VP9 roughly 1-2 MB per minute depending on quality
    const mbPerSecond = 0.025; // ~1.5 MB per minute
    const estimatedMB = (seconds * mbPerSecond).toFixed(1);
    return `~${estimatedMB} MB`;
  }, []);

  // Initialize camera stream
  const initCamera = useCallback(async () => {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setPermissionState('unavailable');
      setError('Camera not supported in this browser. Please use Chrome, Firefox, Safari, or Edge.');
      return false;
    }

    try {
      setError(null);
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 1280 },
          height: { ideal: 720 },
          facingMode: 'user',
        },
        audio: false, // Audio handled separately by RecordingDeck
      });

      streamRef.current = stream;
      setPermissionState('granted');

      // Attach stream to video element
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }

      return true;
    } catch (err) {
      const error = err as { name?: string };
      
      if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
        setPermissionState('denied');
        setError('Camera access denied. Please allow camera access in your browser settings and refresh the page.');
      } else if (error.name === 'NotFoundError') {
        setPermissionState('unavailable');
        setError('No camera found. Please connect a camera and try again.');
      } else {
        setPermissionState('denied');
        setError('Could not access camera. Please check your device settings.');
      }
      
      return false;
    }
  }, []);

  // Start recording
  const startRecording = useCallback(async () => {
    if (disabled) return;

    // Initialize camera if not already done
    if (!streamRef.current) {
      const success = await initCamera();
      if (!success) return;
    }

    try {
      setError(null);
      chunksRef.current = [];
      
      const mimeType = getSupportedMimeType();
      mimeTypeRef.current = mimeType;

      const mediaRecorder = new MediaRecorder(streamRef.current!, { mimeType });
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: mimeTypeRef.current });
        setRecordedBlob(blob);
        
        // Create preview URL
        const url = URL.createObjectURL(blob);
        setPreviewUrl(url);
        
        setRecordingState('preview');
      };

      mediaRecorder.start(1000); // Collect data every second
      setRecordingState('recording');
      setElapsedSeconds(0);

      // Start timer
      timerRef.current = setInterval(() => {
        setElapsedSeconds((prev) => {
          const next = prev + 1;
          // Auto-stop at max duration
          if (next >= maxDurationSeconds) {
            stopRecording();
          }
          return next;
        });
      }, 1000);
    } catch (err) {
      const error = err as { message?: string };
      setError(error.message || 'Failed to start recording');
      setRecordingState('error');
    }
  }, [disabled, initCamera, getSupportedMimeType, maxDurationSeconds]);

  // Stop recording
  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }

    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  // Cancel recording and reset
  const cancelRecording = useCallback(() => {
    stopRecording();
    
    // Clear recorded data
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
    
    setRecordedBlob(null);
    setPreviewUrl(null);
    setElapsedSeconds(0);
    setRecordingState('idle');
    setError(null);
  }, [stopRecording, previewUrl]);

  // Confirm and submit video
  const confirmVideo = useCallback(() => {
    if (recordedBlob) {
      onVideoReady(recordedBlob);
      
      // Reset after submission
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
      setRecordedBlob(null);
      setPreviewUrl(null);
      setElapsedSeconds(0);
      setRecordingState('idle');
    }
  }, [recordedBlob, onVideoReady, previewUrl]);

  // Re-record (discard current and start fresh)
  const reRecord = useCallback(() => {
    cancelRecording();
    // Small delay to ensure cleanup before restart
    setTimeout(() => {
      startRecording();
    }, 100);
  }, [cancelRecording, startRecording]);

  // Initialize camera on mount
  useEffect(() => {
    initCamera();

    return () => {
      // Cleanup: stop all tracks
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
      }
      
      // Revoke preview URL
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
      
      // Clear timer
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    };
  }, [initCamera, previewUrl]);

  // Cleanup stream on unmount
  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
      }
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, []);

  // ===== RENDER =====

  // Error / Permission denied state
  if (permissionState === 'denied' || permissionState === 'unavailable' || recordingState === 'error') {
    return (
      <div className="w-full rounded-2xl bg-surface-primary dark:bg-surface-dark border border-border-light dark:border-dark-border-light p-6 sm:p-10 flex flex-col items-center justify-center gap-4 min-h-[240px] sm:min-h-[280px]">
        <div className="p-4 rounded-full bg-status-error/10">
          <AlertCircle size={40} className="text-status-error" />
        </div>
        <div className="text-center space-y-2">
          <h3 className="text-lg sm:text-xl font-bold text-text-primary dark:text-dark-text-primary">
            Camera Unavailable
          </h3>
          <p className="text-sm text-text-secondary dark:text-dark-text-secondary max-w-sm">
            {error || 'Please allow camera access to record video.'}
          </p>
        </div>
        <button
          onClick={() => {
            setError(null);
            setPermissionState('prompt');
            initCamera();
          }}
          className="mt-2 px-6 py-3 bg-electric-blue hover:bg-sky-500 text-white rounded-xl font-semibold transition-colors min-h-[44px]"
        >
          Try Again
        </button>
      </div>
    );
  }

  // Preview state - show recorded video
  if (recordingState === 'preview' && previewUrl) {
    return (
      <div className="w-full rounded-2xl bg-surface-primary dark:bg-surface-dark border border-border-light dark:border-dark-border-light overflow-hidden">
        {/* Video Preview */}
        <div className="relative aspect-video bg-black">
          <video
            src={previewUrl}
            controls
            className="w-full h-full object-contain"
            aria-label="Recorded video preview"
          />
        </div>

        {/* Preview Controls */}
        <div className="p-4 sm:p-6 bg-white dark:bg-surface-secondary/50">
          {/* Info Bar */}
          <div className="flex justify-between items-center mb-4">
            <div className="flex items-center gap-2">
              <Check size={18} className="text-status-success" />
              <span className="text-sm font-medium text-text-primary dark:text-dark-text-primary">
                Recording Complete
              </span>
            </div>
            <div className="flex items-center gap-3 text-sm text-text-secondary dark:text-dark-text-secondary">
              <span className="font-mono">{formatTime(elapsedSeconds)}</span>
              <span className="text-text-tertiary dark:text-dark-text-tertiary">
                {estimateFileSize(elapsedSeconds)}
              </span>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-center gap-3 sm:gap-4">
            <button
              onClick={reRecord}
              disabled={disabled}
              className="flex items-center gap-2 px-4 sm:px-6 py-3 rounded-xl bg-surface-tertiary dark:bg-white/10 text-text-primary dark:text-dark-text-primary hover:bg-surface-secondary dark:hover:bg-white/20 transition-colors min-h-[44px] disabled:opacity-50 disabled:cursor-not-allowed"
              aria-label="Re-record video"
            >
              <RefreshCw size={18} />
              <span className="text-sm sm:text-base">Re-record</span>
            </button>

            <button
              onClick={confirmVideo}
              disabled={disabled || !recordedBlob}
              className="flex items-center gap-2 px-6 sm:px-8 py-3 rounded-xl bg-electric-blue hover:bg-sky-500 text-white font-semibold transition-colors min-h-[44px] disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-blue-glow"
              aria-label="Use this video"
            >
              <Check size={18} />
              <span className="text-sm sm:text-base">Use Video</span>
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Recording state - show live camera with controls
  if (recordingState === 'recording') {
    return (
      <div className="w-full rounded-2xl bg-surface-primary dark:bg-surface-dark border border-border-light dark:border-dark-border-light overflow-hidden">
        {/* Live Video */}
        <div className="relative aspect-video bg-black">
          <video
            ref={videoRef}
            autoPlay
            muted
            playsInline
            className="w-full h-full object-cover mirror"
            aria-label="Live camera preview"
          />

          {/* Recording Indicator Overlay */}
          <div className="absolute top-4 left-4 flex items-center gap-2 px-3 py-1.5 rounded-full bg-black/60 backdrop-blur-sm">
            <span className="relative flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-status-error opacity-75" />
              <span className="relative inline-flex rounded-full h-3 w-3 bg-status-error" />
            </span>
            <span className="text-white text-sm font-semibold">
              REC {formatTime(elapsedSeconds)}
            </span>
          </div>

          {/* Timer & Size Overlay */}
          <div className="absolute bottom-4 right-4 flex items-center gap-3 px-3 py-1.5 rounded-full bg-black/60 backdrop-blur-sm">
            <span className="text-white/80 text-xs font-mono">
              {estimateFileSize(elapsedSeconds)}
            </span>
            <span className="text-white/60 text-xs">|</span>
            <span className="text-white/80 text-xs">
              Max {formatTime(maxDurationSeconds)}
            </span>
          </div>
        </div>

        {/* Recording Controls */}
        <div className="p-4 sm:p-6 bg-white dark:bg-surface-secondary/50">
          {/* Timer Display */}
          <div className="flex justify-between items-center mb-5">
            <div className="flex items-center gap-2">
              <span className="relative flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-status-error opacity-75" />
                <span className="relative inline-flex rounded-full h-3 w-3 bg-status-error" />
              </span>
              <span className="font-mono text-xl sm:text-2xl font-bold text-status-error tabular-nums">
                {formatTime(elapsedSeconds)}
              </span>
            </div>
            <div className="text-xs font-bold text-text-tertiary dark:text-dark-text-tertiary uppercase tracking-wider">
              Recording
            </div>
          </div>

          {/* Stop Button */}
          <div className="flex items-center justify-center gap-3 sm:gap-4">
            <button
              onClick={cancelRecording}
              className="p-3 sm:p-4 rounded-full text-text-tertiary hover:bg-status-error/10 hover:text-status-error transition-all min-w-[44px] min-h-[44px] flex items-center justify-center"
              aria-label="Cancel recording"
            >
              <VideoOff size={20} className="sm:hidden" />
              <VideoOff size={24} className="hidden sm:block" />
            </button>

            <button
              onClick={stopRecording}
              className="group relative flex items-center justify-center h-14 w-14 sm:h-16 sm:w-16 rounded-full bg-status-error text-white shadow-lg hover:shadow-xl hover:shadow-status-error/40 hover:scale-110 active:scale-95 transition-all duration-200 min-w-[48px] min-h-[48px]"
              aria-label="Stop recording"
            >
              <Square size={20} className="sm:hidden" fill="currentColor" />
              <Square size={24} className="hidden sm:block" fill="currentColor" />
              <div className="absolute inset-0 rounded-full border-2 border-white/20 group-hover:border-white/40 transition-colors" />
            </button>

            {/* Spacer for balance */}
            <div className="w-[44px] sm:w-[56px]" />
          </div>
        </div>
      </div>
    );
  }

  // Idle state - show camera preview with start button
  return (
    <div className="w-full rounded-2xl bg-surface-primary dark:bg-surface-dark border border-border-light dark:border-dark-border-light overflow-hidden">
      {/* Camera Preview */}
      <div className="relative aspect-video bg-gradient-to-b from-slate-900 via-slate-800 to-slate-900 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950">
        {streamRef.current ? (
          <video
            ref={videoRef}
            autoPlay
            muted
            playsInline
            className="w-full h-full object-cover mirror opacity-90"
            aria-label="Camera preview"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <div className="animate-pulse">
              <Video size={48} className="text-white/30" />
            </div>
          </div>
        )}

        {/* Ready indicator */}
        <div className="absolute bottom-4 left-4 px-3 py-1.5 rounded-full bg-black/40 backdrop-blur-sm">
          <span className="text-white/80 text-sm">Camera Ready</span>
        </div>
      </div>

      {/* Start Controls */}
      <div className="p-4 sm:p-6 bg-white dark:bg-surface-secondary/50">
        <div className="flex flex-col items-center justify-center gap-4">
          <div className="text-center space-y-1">
            <h3 className="text-lg sm:text-xl font-bold text-text-primary dark:text-dark-text-primary">
              Ready to Record Video
            </h3>
            <p className="text-sm text-text-secondary dark:text-dark-text-secondary">
              Click to start recording your video response
            </p>
          </div>

          <button
            onClick={startRecording}
            disabled={disabled || !streamRef.current}
            className="group relative flex items-center gap-3 px-6 sm:px-8 py-3 sm:py-4 bg-electric-blue hover:bg-sky-500 text-white rounded-xl font-semibold shadow-xl hover:shadow-blue-glow hover:scale-105 active:scale-95 transition-all duration-200 min-h-[44px] disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label="Start video recording"
          >
            <Video size={20} className="sm:hidden" />
            <Video size={24} className="hidden sm:block" />
            <span className="text-sm sm:text-base">Start Recording</span>
            
            {/* Shine effect on hover */}
            <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-1000 overflow-hidden" />
          </button>

          <p className="text-xs text-text-tertiary dark:text-dark-text-tertiary">
            Max duration: {formatTime(maxDurationSeconds)}
          </p>
        </div>
      </div>
    </div>
  );
}
