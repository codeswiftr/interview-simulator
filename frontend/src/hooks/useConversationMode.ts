import { useCallback, useEffect, useRef, useState } from 'react';
import type { UseSpeechSynthesisReturn } from './useSpeechSynthesis';
import type { UseSpeechRecognitionReturn } from './useSpeechRecognition';

export type ConversationMode = 'idle' | 'mentor_speaking' | 'user_turn' | 'processing';

export interface UseConversationModeOptions {
  tts: UseSpeechSynthesisReturn;
  stt: UseSpeechRecognitionReturn;
  autoListen?: boolean;
  onMentorFinish?: () => void;
  onUserFinish?: (transcript: string) => void;
  enabled?: boolean;
}

export interface UseConversationModeReturn {
  mode: ConversationMode;
  isActive: boolean;
  startConversation: () => void;
  endConversation: () => void;
  mentorSay: (text: string) => Promise<void>;
  interrupt: () => void;
  transitionTo: (mode: ConversationMode) => void;
}

/**
 * Hook for managing conversational flow between mentor (TTS) and user (STT)
 *
 * State machine: idle -> mentor_speaking -> user_turn -> processing -> mentor_speaking
 *
 * @example
 * ```tsx
 * const conversation = useConversationMode({
 *   tts: speechSynthesis,
 *   stt: speechRecognition,
 *   autoListen: true,
 *   onUserFinish: (transcript) => handleUserResponse(transcript),
 * });
 *
 * // Start conversation with mentor speaking
 * await conversation.mentorSay("What's your biggest achievement?");
 * // Auto-transitions to user_turn if autoListen is true
 * ```
 */
export function useConversationMode({
  tts,
  stt,
  autoListen = false,
  onMentorFinish,
  onUserFinish,
  enabled = true,
}: UseConversationModeOptions): UseConversationModeReturn {
  const [mode, setMode] = useState<ConversationMode>('idle');
  const [isActive, setIsActive] = useState(false);

  const pendingSpeechRef = useRef<string | null>(null);
  const resolveRef = useRef<(() => void) | null>(null);

  // Watch TTS state for mentor speaking transitions
  useEffect(() => {
    if (!enabled || !isActive) return;

    // Mentor finished speaking
    if (mode === 'mentor_speaking' && !tts.isSpeaking && pendingSpeechRef.current === null) {
      setMode('user_turn');
      onMentorFinish?.();

      // Auto-start listening if enabled
      if (autoListen && stt.isSupported) {
        stt.startListening();
      }

      // Resolve pending promise
      if (resolveRef.current) {
        resolveRef.current();
        resolveRef.current = null;
      }
    }
  }, [tts.isSpeaking, mode, isActive, enabled, autoListen, stt, onMentorFinish]);

  // Watch STT state for user turn transitions
  useEffect(() => {
    if (!enabled || !isActive) return;

    // User finished speaking (stopped listening with a transcript)
    if (mode === 'user_turn' && !stt.isListening && stt.finalTranscript) {
      setMode('processing');
      onUserFinish?.(stt.finalTranscript);
    }
  }, [stt.isListening, stt.finalTranscript, mode, isActive, enabled, onUserFinish]);

  // Start conversation mode
  // Note: Does NOT reset transcript - caller should reset when appropriate (after answer is submitted)
  const startConversation = useCallback(() => {
    if (!enabled) return;
    setIsActive(true);
    setMode('idle');
  }, [enabled]);

  // End conversation mode
  const endConversation = useCallback(() => {
    tts.stop();
    stt.stopListening();
    stt.resetTranscript();
    setIsActive(false);
    setMode('idle');
    pendingSpeechRef.current = null;
    if (resolveRef.current) {
      resolveRef.current();
      resolveRef.current = null;
    }
  }, [tts, stt]);

  // Have mentor speak (returns promise that resolves when done)
  const mentorSay = useCallback(
    (text: string): Promise<void> => {
      if (!enabled || !tts.isSupported) {
        return Promise.resolve();
      }

      return new Promise((resolve) => {
        pendingSpeechRef.current = text;
        resolveRef.current = resolve;
        setMode('mentor_speaking');

        // Small delay to ensure state updates before speaking
        setTimeout(() => {
          tts.speak(text);
          pendingSpeechRef.current = null;
        }, 50);
      });
    },
    [enabled, tts]
  );

  // Interrupt mentor (user wants to speak)
  const interrupt = useCallback(() => {
    if (!enabled || !isActive) return;

    if (mode === 'mentor_speaking') {
      tts.stop();
      setMode('user_turn');

      // Resolve pending promise
      if (resolveRef.current) {
        resolveRef.current();
        resolveRef.current = null;
      }

      // Start listening immediately
      if (stt.isSupported) {
        stt.startListening();
      }
    }
  }, [enabled, isActive, mode, tts, stt]);

  // Manual mode transition
  const transitionTo = useCallback((newMode: ConversationMode) => {
    if (!enabled) return;
    setMode(newMode);

    // Handle side effects for each mode
    switch (newMode) {
      case 'idle':
        tts.stop();
        stt.stopListening();
        break;
      case 'mentor_speaking':
        stt.stopListening();
        break;
      case 'user_turn':
        tts.stop();
        if (autoListen && stt.isSupported) {
          stt.startListening();
        }
        break;
      case 'processing':
        stt.stopListening();
        break;
    }
  }, [enabled, tts, stt, autoListen]);

  return {
    mode,
    isActive,
    startConversation,
    endConversation,
    mentorSay,
    interrupt,
    transitionTo,
  };
}
