import { useState, useRef, useCallback, useEffect } from 'react';
import { getSupportedMimeType } from '../lib/audio-utils';

export type RecordingState = 'idle' | 'recording' | 'paused' | 'stopped' | 'preview';

export interface UseAudioRecordingReturn {
  recordingState: RecordingState;
  audioBlob: Blob | null;
  audioUrl: string | null;
  duration: number;
  isRecording: boolean;
  isPreviewMode: boolean;
  isPlaying: boolean;
  currentTime: number;
  audioDuration: number;
  startRecording: () => Promise<void>;
  stopRecording: () => void;
  pauseRecording: () => void;
  resumeRecording: () => void;
  resetRecording: () => void;
  playPreview: () => void;
  pausePreview: () => void;
  clearPreview: () => void;
  confirmRecording: () => Blob | null;
  error: string | null;
  mediaStream: MediaStream | null;
  mimeType: string | null;
}

export function useAudioRecording(): UseAudioRecordingReturn {
  const [recordingState, setRecordingState] = useState<RecordingState>('idle');
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [duration, setDuration] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [audioDuration, setAudioDuration] = useState(0);
  const [mediaStream, setMediaStream] = useState<MediaStream | null>(null);
  const [mimeType, setMimeType] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const mimeTypeRef = useRef<string>('audio/webm');
  const startTimeRef = useRef<number>(0);
  const pausedTimeRef = useRef<number>(0);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const audioElementRef = useRef<HTMLAudioElement | null>(null);
  const audioUrlRef = useRef<string | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  // Start recording
  const startRecording = useCallback(async () => {
    try {
      setError(null);

      // Check browser support for MediaRecorder
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        setError('Your browser does not support audio recording. Please use Chrome, Firefox, Safari, or Edge.');
        return;
      }

      if (typeof MediaRecorder === 'undefined') {
        setError('Your browser does not support MediaRecorder. Please update your browser or try Chrome/Firefox.');
        return;
      }

      // Request microphone permission
      let stream: MediaStream;
      try {
        stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      } catch (permissionError) {
        const err = permissionError as { name?: string };
        if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
          setError('Microphone access denied. Please allow microphone access in your browser settings and refresh the page.');
        } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
          setError('No microphone found. Please connect a microphone and try again.');
        } else {
          setError('Could not access microphone. Please check your device settings.');
        }
        setRecordingState('idle');
        return;
      }
      streamRef.current = stream;
      setMediaStream(stream);

      // Get supported MIME type for cross-browser compatibility (Safari needs MP4/WAV)
      const mimeType = getSupportedMimeType();
      mimeTypeRef.current = mimeType;
      setMimeType(mimeType);

      // Create MediaRecorder
      const mediaRecorder = new MediaRecorder(stream, { mimeType });
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      // Handle data available
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      // Handle recording stop
      mediaRecorder.onstop = () => {
        const blob = new Blob(audioChunksRef.current, { type: mimeTypeRef.current });
        setAudioBlob(blob);

        // Revoke previous URL if exists
        if (audioUrlRef.current) {
          URL.revokeObjectURL(audioUrlRef.current);
        }

        // Create object URL for preview
        const url = URL.createObjectURL(blob);
        audioUrlRef.current = url;
        setAudioUrl(url);

        // Stop all tracks
        stream.getTracks().forEach(track => track.stop());
        streamRef.current = null;
        setMediaStream(null);

        // Enter preview mode instead of stopped
        setRecordingState('preview');
      };

      // Start recording
      mediaRecorder.start();
      startTimeRef.current = Date.now();
      setRecordingState('recording');

      // Start timer
      timerRef.current = setInterval(() => {
        setDuration(Math.floor((Date.now() - startTimeRef.current - pausedTimeRef.current) / 1000));
      }, 100);
    } catch (err) {
      const error = err as { message?: string };
      setError(error.message || 'Failed to start recording. Please check microphone permissions.');
      setRecordingState('idle');
    }
  }, []);

  // Stop recording
  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && recordingState === 'recording') {
      mediaRecorderRef.current.stop();

      // Clear timer
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }
  }, [recordingState]);

  // Pause recording
  const pauseRecording = useCallback(() => {
    if (mediaRecorderRef.current && recordingState === 'recording') {
      mediaRecorderRef.current.pause();
      setRecordingState('paused');

      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }
  }, [recordingState]);

  // Resume recording
  const resumeRecording = useCallback(() => {
    if (mediaRecorderRef.current && recordingState === 'paused') {
      const pauseStart = Date.now();
      mediaRecorderRef.current.resume();
      setRecordingState('recording');

      // Update paused time
      pausedTimeRef.current += pauseStart - startTimeRef.current;

      // Restart timer
      timerRef.current = setInterval(() => {
        setDuration(Math.floor((Date.now() - startTimeRef.current - pausedTimeRef.current) / 1000));
      }, 100);
    }
  }, [recordingState]);

  // Reset recording
  const resetRecording = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }

    if (mediaRecorderRef.current) {
      if (mediaRecorderRef.current.state !== 'inactive') {
        mediaRecorderRef.current.stop();
      }
      mediaRecorderRef.current = null;
    }

    // Stop any active stream tracks
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
      setMediaStream(null);
    }

    if (audioElementRef.current) {
      audioElementRef.current.pause();
      audioElementRef.current = null;
    }

    // Use ref for cleanup to avoid stale closure
    if (audioUrlRef.current) {
      URL.revokeObjectURL(audioUrlRef.current);
      audioUrlRef.current = null;
    }

    setRecordingState('idle');
    setAudioBlob(null);
    setAudioUrl(null);
    setDuration(0);
    setError(null);
    setIsPlaying(false);
    setCurrentTime(0);
    setAudioDuration(0);
    audioChunksRef.current = [];
    startTimeRef.current = 0;
    pausedTimeRef.current = 0;
  }, []);

  // Play preview
  const playPreview = useCallback(() => {
    if (audioElementRef.current) {
      audioElementRef.current.play().catch((err) => {
        const error = err as { message?: string };
        setError(error.message || 'Failed to play audio preview');
      });
      setIsPlaying(true);
    }
  }, []);

  // Pause preview
  const pausePreview = useCallback(() => {
    if (audioElementRef.current) {
      audioElementRef.current.pause();
      setIsPlaying(false);
    }
  }, []);

  // Clear preview and return to idle
  const clearPreview = useCallback(() => {
    if (audioElementRef.current) {
      audioElementRef.current.pause();
      audioElementRef.current = null;
    }

    // Use ref for cleanup to avoid stale closure
    if (audioUrlRef.current) {
      URL.revokeObjectURL(audioUrlRef.current);
      audioUrlRef.current = null;
    }

    setRecordingState('idle');
    setAudioBlob(null);
    setAudioUrl(null);
    setDuration(0);
    setIsPlaying(false);
    setCurrentTime(0);
    setAudioDuration(0);
  }, []);

  // Confirm recording and return blob
  const confirmRecording = useCallback(() => {
    if (audioElementRef.current) {
      audioElementRef.current.pause();
      audioElementRef.current = null;
    }
    return audioBlob;
  }, [audioBlob]);

  // Setup audio element for preview
  useEffect(() => {
    if (recordingState === 'preview' && audioUrl && !audioElementRef.current) {
      const audio = new Audio(audioUrl);
      audioElementRef.current = audio;

      audio.onloadedmetadata = () => {
        setAudioDuration(audio.duration);
      };

      audio.ontimeupdate = () => {
        setCurrentTime(audio.currentTime);
      };

      audio.onended = () => {
        setIsPlaying(false);
        setCurrentTime(0);
      };

      audio.onerror = () => {
        setError('Failed to load audio preview');
      };
    }

    return () => {
      if (audioElementRef.current) {
        audioElementRef.current.pause();
        audioElementRef.current = null;
      }
    };
  }, [recordingState, audioUrl]);

  // Cleanup on unmount - using refs to avoid stale closures
  useEffect(() => {
    return () => {
      // Clear timer
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }

      // Stop recording if in progress
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
        mediaRecorderRef.current.stop();
        mediaRecorderRef.current = null;
      }

      // Stop any active stream tracks (important for releasing microphone)
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
        streamRef.current = null;
        setMediaStream(null);
      }

      // Clean up audio element
      if (audioElementRef.current) {
        audioElementRef.current.pause();
        audioElementRef.current = null;
      }

      // Revoke object URL to prevent memory leak
      if (audioUrlRef.current) {
        URL.revokeObjectURL(audioUrlRef.current);
        audioUrlRef.current = null;
      }
    };
  }, []); // Empty deps - cleanup should always work with refs

  return {
    recordingState,
    audioBlob,
    audioUrl,
    duration,
    isRecording: recordingState === 'recording',
    isPreviewMode: recordingState === 'preview',
    isPlaying,
    currentTime,
    audioDuration,
    startRecording,
    stopRecording,
    pauseRecording,
    resumeRecording,
    resetRecording,
    playPreview,
    pausePreview,
    clearPreview,
    confirmRecording,
    error,
    mediaStream,
    mimeType,
  };
}
