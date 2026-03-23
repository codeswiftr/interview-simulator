import { useState, useEffect, useRef, useCallback } from 'react';
import api from '../lib/api';
import { analytics, Events } from '../lib/analytics';

export interface UseCoachingHintOptions {
  question: string;
  questionType: 'behavioral' | 'technical' | 'system_design';
  transcript: string;
  enabled?: boolean;
}

export interface UseCoachingHintReturn {
  hint: string | null;
  isLoading: boolean;
  isStreaming: boolean;
  error: string | null;
  triggerHint: () => void;
}

/**
 * Hook for generating contextual coaching hints with debouncing.
 * 
 * Triggers hint generation when:
 * - 2 seconds of silence (no new transcript words)
 * - OR 50+ new words added to transcript
 * 
 * Uses streaming endpoint for low latency.
 */
export function useCoachingHint({
  question,
  questionType,
  transcript,
  enabled = true,
}: UseCoachingHintOptions): UseCoachingHintReturn {
  const [hint, setHint] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const transcriptRef = useRef(transcript);
  const wordCountRef = useRef(0);
  const debounceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const lastHintRef = useRef<string | null>(null);

  // Count words in transcript
  const countWords = useCallback((text: string): number => {
    return text.trim().split(/\s+/).filter(word => word.length > 0).length;
  }, []);

  // Generate hint from API
  const generateHint = useCallback(async () => {
    if (!enabled || !question || !questionType) {
      return;
    }

    // Don't regenerate if transcript hasn't changed
    if (transcriptRef.current === transcript && lastHintRef.current) {
      return;
    }

    // Cancel any pending request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

        abortControllerRef.current = new AbortController();
        setIsLoading(true);
        setIsStreaming(false);
        setError(null);

    try {
      // Use streaming endpoint for real-time hints
      const response = await fetch(`${api.defaults.baseURL}/coaching/hint/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: JSON.stringify({
          question,
          question_type: questionType,
          transcript,
        }),
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        if (response.status === 429) {
          throw new Error('Rate limit exceeded. Please wait a moment.');
        }
        throw new Error(`Failed to generate hint: ${response.statusText}`);
      }

      // Read streaming response
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error('No response body');
      }

      let accumulatedHint = '';

      while (true) {
        const { done, value } = await reader.read();

        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.hint) {
                accumulatedHint = data.hint;
                setHint(data.hint);
                setIsStreaming(!data.done); // Track streaming state

                if (data.done) {
                  lastHintRef.current = data.hint;
                  transcriptRef.current = transcript;
                  setIsLoading(false);
                  setIsStreaming(false);
                  return;
                }
              }
            } catch {
              // Ignore JSON parse errors for incomplete chunks
            }
          }
        }
      }

      if (accumulatedHint) {
        lastHintRef.current = accumulatedHint;
        transcriptRef.current = transcript;
        setIsStreaming(false);

        // Track coaching hint usage
        analytics.track(Events.COACHING_HINT_USED, {
          question_type: questionType,
          transcript_word_count: countWords(transcript),
        });
      }
    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') {
        // Request was cancelled, ignore
        return;
      }
      const errorMessage = err instanceof Error ? err.message : 'Failed to generate hint';
      setError(errorMessage);
      setHint(null);
    } finally {
      setIsLoading(false);
      setIsStreaming(false);
      abortControllerRef.current = null;
    }
  }, [question, questionType, transcript, enabled, countWords]);

  // Debounced hint generation
  useEffect(() => {
    if (!enabled || !question || !questionType) {
      return;
    }

    // Clear existing timer
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    const currentWordCount = countWords(transcript);
    const previousWordCount = wordCountRef.current;
    const newWords = currentWordCount - previousWordCount;

    // Don't generate hints for very short transcripts (less than 10 words)
    if (currentWordCount < 10) {
      return;
    }

    // Update word count
    wordCountRef.current = currentWordCount;

    // Trigger immediately if 50+ new words
    if (newWords >= 50) {
      generateHint();
      return;
    }

    // Otherwise, debounce for 2 seconds of silence
    debounceTimerRef.current = setTimeout(() => {
      // Only generate if transcript has changed
      if (transcriptRef.current !== transcript) {
        generateHint();
      }
    }, 2000);

    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, [transcript, question, questionType, enabled, generateHint, countWords]);

  // Manual trigger function
  const triggerHint = useCallback(() => {
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }
    generateHint();
  }, [generateHint]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  return {
    hint,
    isLoading,
    isStreaming,
    error,
    triggerHint,
  };
}
