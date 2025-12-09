import { useEffect } from 'react';
import { Mic, MicOff } from 'lucide-react';
import { useSpeechRecognition } from '../../hooks/useSpeechRecognition';
import { cn } from '../../lib/utils';

export interface VoiceInputButtonProps {
  onTranscript: (text: string) => void;  // Called with final transcript
  onInterim?: (text: string) => void;      // Called with interim results
  disabled?: boolean;
  className?: string;
  placeholder?: string;                   // Shown when listening
  size?: 'sm' | 'md' | 'lg';
  autoStart?: boolean;                     // Auto-start on mount (for testing)
}

/**
 * VoiceInputButton - Compact microphone button with speech recognition
 * 
 * @example
 * ```tsx
 * <VoiceInputButton
 *   onTranscript={(text) => setAnswer(text)}
 *   onInterim={(text) => setPreview(text)}
 *   placeholder="Listening..."
 * />
 * ```
 */
export function VoiceInputButton({
  onTranscript,
  onInterim,
  disabled = false,
  className,
  placeholder = 'Listening...',
  size = 'md',
  autoStart = false,
}: VoiceInputButtonProps) {
  const {
    isListening,
    transcript,
    finalTranscript,
    error,
    isSupported,
    startListening,
    stopListening,
    resetTranscript,
  } = useSpeechRecognition({
    onResult: (text, isFinal) => {
      if (isFinal) {
        onTranscript(text);
        resetTranscript();
      } else if (onInterim) {
        onInterim(text);
      }
    },
    onError: (err) => {
      console.error('Speech recognition error:', err);
    },
  });

  // Auto-start for testing (optional)
  useEffect(() => {
    if (autoStart && isSupported && !disabled) {
      startListening();
    }
  }, [autoStart, isSupported, disabled, startListening]);

  // Handle final transcript
  useEffect(() => {
    if (finalTranscript) {
      onTranscript(finalTranscript);
      resetTranscript();
    }
  }, [finalTranscript, onTranscript, resetTranscript]);

  const handleToggle = () => {
    if (isListening) {
      stopListening();
      // If we have a transcript when stopping, send it
      if (transcript) {
        onTranscript(transcript);
        resetTranscript();
      }
    } else {
      resetTranscript();
      startListening();
    }
  };

  const sizeClasses = {
    sm: 'h-8 w-8',
    md: 'h-10 w-10',
    lg: 'h-12 w-12',
  };

  const iconSizes = {
    sm: 16,
    md: 20,
    lg: 24,
  };

  if (!isSupported) {
    return (
      <button
        disabled
        className={cn(
          'inline-flex items-center justify-center rounded-full',
          'bg-surface-tertiary text-text-tertiary',
          'cursor-not-allowed opacity-50',
          sizeClasses[size],
          className
        )}
        title="Speech recognition not supported in this browser"
      >
        <MicOff size={iconSizes[size]} />
      </button>
    );
  }

  return (
    <div className="inline-flex flex-col items-center gap-1">
      <button
        type="button"
        onClick={handleToggle}
        disabled={disabled || !!error}
        className={cn(
          'relative inline-flex items-center justify-center rounded-full',
          'transition-all duration-200',
          'focus:outline-none focus-visible:ring-2 focus-visible:ring-electric-blue focus-visible:ring-offset-2',
          'disabled:opacity-50 disabled:cursor-not-allowed',
          // Active/listening state
          isListening
            ? 'bg-status-error text-white shadow-lg hover:bg-red-600'
            : 'bg-surface-tertiary text-text-primary hover:bg-surface-tertiary/80 hover:scale-105',
          sizeClasses[size],
          className
        )}
        title={isListening ? 'Stop listening' : 'Start voice input'}
        aria-label={isListening ? 'Stop voice input' : 'Start voice input'}
        aria-pressed={isListening}
      >
        {/* Pulsing animation when listening */}
        {isListening && (
          <span className="absolute inset-0 rounded-full bg-status-error opacity-75 animate-ping" />
        )}

        {/* Microphone icon */}
        {isListening ? (
          <Mic size={iconSizes[size]} className="relative z-10" />
        ) : (
          <Mic size={iconSizes[size]} />
        )}
      </button>

      {/* Placeholder/status text */}
      {isListening && placeholder && (
        <span className="text-xs text-text-tertiary font-medium animate-pulse">
          {placeholder}
        </span>
      )}

      {/* Error message */}
      {error && (
        <span className="text-xs text-status-error font-medium max-w-[200px] text-center">
          {error}
        </span>
      )}
    </div>
  );
}
