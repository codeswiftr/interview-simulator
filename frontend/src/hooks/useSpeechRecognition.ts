import { useState, useEffect, useRef, useCallback } from 'react';
import type { SpeechRecognition, SpeechRecognitionEvent, SpeechRecognitionErrorEvent } from '../types/speech';
import { isSpeechRecognitionSupported, getSpeechRecognitionConstructor } from '../types/speech';

export interface UseSpeechRecognitionOptions {
  lang?: string;              // Default: 'en-US'
  continuous?: boolean;       // Default: true
  interimResults?: boolean;   // Default: true
  onResult?: (transcript: string, isFinal: boolean) => void;
  onError?: (error: string) => void;
}

export interface UseSpeechRecognitionReturn {
  isListening: boolean;
  transcript: string;
  finalTranscript: string;
  error: string | null;
  isSupported: boolean;
  startListening: () => void;
  stopListening: () => void;
  resetTranscript: () => void;
}

/**
 * Hook for using Web Speech API for speech recognition
 * 
 * @example
 * ```tsx
 * const { isListening, transcript, startListening, stopListening } = useSpeechRecognition({
 *   onResult: (text, isFinal) => {
 *     if (isFinal) {
 *       console.log('Final transcript:', text);
 *     }
 *   }
 * });
 * ```
 */
export function useSpeechRecognition(
  options: UseSpeechRecognitionOptions = {}
): UseSpeechRecognitionReturn {
  const {
    lang = 'en-US',
    continuous = true,
    interimResults = true,
    onResult,
    onError,
  } = options;

  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [finalTranscript, setFinalTranscript] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSupported] = useState(() => isSpeechRecognitionSupported());

  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const finalTranscriptRef = useRef<string>('');
  const lastProcessedIndexRef = useRef<number>(-1);

  // Initialize recognition instance
  useEffect(() => {
    if (!isSupported) {
      setError('Speech recognition is not supported in this browser');
      return;
    }

    const SpeechRecognitionClass = getSpeechRecognitionConstructor();
    if (!SpeechRecognitionClass) {
      setError('Speech recognition constructor not available');
      return;
    }

    const recognition = new SpeechRecognitionClass();
    recognition.continuous = continuous;
    recognition.interimResults = interimResults;
    recognition.lang = lang;

    // Reset tracking when recognition starts
    recognition.onstart = () => {
      finalTranscriptRef.current = '';
      lastProcessedIndexRef.current = -1;
    };

    // Handle results
    recognition.onresult = (event: SpeechRecognitionEvent) => {
      let currentTranscript = '';
      let hasFinal = false;

      // Process all results from resultIndex to end
      // Note: The results array contains ALL results, not just new ones
      // resultIndex tells us where new results start
      // We track lastProcessedIndex to avoid re-processing results
      const startIndex = Math.max(event.resultIndex, lastProcessedIndexRef.current + 1);
      
      for (let i = startIndex; i < event.results.length; i++) {
        const result = event.results[i];
        const alternative = result[0];
        
        if (result.isFinal) {
          hasFinal = true;
          finalTranscriptRef.current += alternative.transcript;
        } else {
          currentTranscript += alternative.transcript;
        }
        
        lastProcessedIndexRef.current = i;
      }

      // Combine final transcript with interim results
      const fullTranscript = finalTranscriptRef.current + currentTranscript;
      setTranscript(fullTranscript);

      // Update final transcript if we have new final results
      if (hasFinal) {
        setFinalTranscript(finalTranscriptRef.current);
      }

      // Call callback if provided
      if (onResult) {
        onResult(fullTranscript, hasFinal);
      }
    };

    // Handle errors
    recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      const errorMessage = `Speech recognition error: ${event.error} - ${event.message}`;
      setError(errorMessage);
      setIsListening(false);
      
      if (onError) {
        onError(errorMessage);
      }
    };

    // Handle end
    recognition.onend = () => {
      setIsListening(false);
    };

    recognitionRef.current = recognition;

    return () => {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop();
        } catch (e) {
          // Ignore errors when stopping
        }
        recognitionRef.current = null;
      }
    };
  }, [isSupported, lang, continuous, interimResults, onResult, onError]);

  // Start listening
  const startListening = useCallback(() => {
    if (!isSupported) {
      setError('Speech recognition is not supported');
      return;
    }

    if (!recognitionRef.current) {
      setError('Speech recognition not initialized');
      return;
    }

    if (isListening) {
      return; // Already listening
    }

    try {
      recognitionRef.current.start();
      setIsListening(true);
      setError(null);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to start speech recognition';
      setError(errorMessage);
      setIsListening(false);
      
      if (onError) {
        onError(errorMessage);
      }
    }
  }, [isSupported, isListening, onError]);

  // Stop listening
  const stopListening = useCallback(() => {
    if (!recognitionRef.current || !isListening) {
      return;
    }

    try {
      recognitionRef.current.stop();
      setIsListening(false);
    } catch (err) {
      // Ignore errors when stopping
      setIsListening(false);
    }
  }, [isListening]);

  // Reset transcript
  const resetTranscript = useCallback(() => {
    setTranscript('');
    setFinalTranscript('');
    finalTranscriptRef.current = '';
    lastProcessedIndexRef.current = -1;
  }, []);

  return {
    isListening,
    transcript,
    finalTranscript,
    error,
    isSupported,
    startListening,
    stopListening,
    resetTranscript,
  };
}
