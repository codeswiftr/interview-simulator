import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

export interface UseSpeechSynthesisOptions {
  defaultRate?: number;
  defaultPitch?: number;
  defaultVolume?: number;
  defaultVoiceName?: string;
}

export interface UseSpeechSynthesisReturn {
  speak: (text: string) => void;
  stop: () => void;
  pause: () => void;
  resume: () => void;
  isSpeaking: boolean;
  isPaused: boolean;
  voices: SpeechSynthesisVoice[];
  selectedVoice: SpeechSynthesisVoice | null;
  setVoice: (voice: SpeechSynthesisVoice | null) => void;
  rate: number;
  setRate: (rate: number) => void;
  pitch: number;
  setPitch: (pitch: number) => void;
  volume: number;
  setVolume: (volume: number) => void;
  isSupported: boolean;
  error: string | null;
}

const isSpeechSynthesisSupported = () =>
  typeof window !== 'undefined' &&
  'speechSynthesis' in window &&
  typeof window.SpeechSynthesisUtterance !== 'undefined';

function selectDefaultVoice(
  voices: SpeechSynthesisVoice[],
  preferredName?: string,
  current?: SpeechSynthesisVoice | null
): SpeechSynthesisVoice | null {
  if (voices.length === 0) {
    return null;
  }

  if (current) {
    const match = voices.find((voice) => voice.name === current.name && voice.lang === current.lang);
    if (match) {
      return match;
    }
  }

  if (preferredName) {
    const preferred = voices.find((voice) => voice.name === preferredName);
    if (preferred) {
      return preferred;
    }
  }

  const englishVoice = voices.find((voice) => voice.lang?.toLowerCase().startsWith('en'));
  return englishVoice ?? voices[0];
}

export function useSpeechSynthesis(
  options: UseSpeechSynthesisOptions = {}
): UseSpeechSynthesisReturn {
  const {
    defaultRate = 1,
    defaultPitch = 1,
    defaultVolume = 1,
    defaultVoiceName,
  } = options;

  const [isSupported] = useState<boolean>(() => isSpeechSynthesisSupported());
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([]);
  const [selectedVoice, setSelectedVoice] = useState<SpeechSynthesisVoice | null>(null);
  const [rate, setRate] = useState(defaultRate);
  const [pitch, setPitch] = useState(defaultPitch);
  const [volume, setVolume] = useState(defaultVolume);
  const [error, setError] = useState<string | null>(null);

  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);
  const preferredVoiceName = useRef<string | undefined>(defaultVoiceName);
  const selectedVoiceRef = useRef<SpeechSynthesisVoice | null>(null);
  const rateRef = useRef(defaultRate);
  const pitchRef = useRef(defaultPitch);
  const volumeRef = useRef(defaultVolume);

  const setRateValue = useCallback((value: number) => {
    rateRef.current = value;
    setRate(value);
  }, []);

  const setPitchValue = useCallback((value: number) => {
    pitchRef.current = value;
    setPitch(value);
  }, []);

  const setVolumeValue = useCallback((value: number) => {
    volumeRef.current = value;
    setVolume(value);
  }, []);

  const setVoice = useCallback((voice: SpeechSynthesisVoice | null) => {
    selectedVoiceRef.current = voice;
    setSelectedVoice(voice);
  }, []);

  const loadVoices = useCallback(() => {
    if (!isSupported) return;

    const availableVoices = window.speechSynthesis.getVoices();
    setVoices(availableVoices);
    setSelectedVoice((current) => {
      const nextVoice = selectDefaultVoice(availableVoices, preferredVoiceName.current, current);
      selectedVoiceRef.current = nextVoice;
      return nextVoice;
    });
  }, [isSupported]);

  useEffect(() => {
    if (!isSupported) {
      setError('Speech synthesis is not supported in this browser');
      return;
    }

    loadVoices();
    const synthesis = window.speechSynthesis;
    const originalVoicesChanged = synthesis.onvoiceschanged;
    synthesis.onvoiceschanged = loadVoices;

    return () => {
      synthesis.onvoiceschanged = originalVoicesChanged ?? null;
      synthesis.cancel();
    };
  }, [isSupported, loadVoices]);

  const speak = useCallback(
    (text: string) => {
      if (!isSupported) {
        setError('Speech synthesis not supported');
        return;
      }

      if (!text) {
        return;
      }

      // Ensure we have voices loaded before speaking
      if (voices.length === 0) {
        loadVoices();
      }

      const utterance = new SpeechSynthesisUtterance(text);
      const voiceToUse = selectedVoiceRef.current ?? selectedVoice;
      utterance.voice = voiceToUse ?? null;
      utterance.rate = rateRef.current;
      utterance.pitch = pitchRef.current;
      utterance.volume = volumeRef.current;

      utterance.onstart = () => {
        setIsSpeaking(true);
        setIsPaused(false);
        setError(null);
      };

      utterance.onend = () => {
        setIsSpeaking(false);
        setIsPaused(false);
      };

      utterance.onpause = () => setIsPaused(true);
      utterance.onresume = () => setIsPaused(false);

      utterance.onerror = (event) => {
        // "canceled" is not a real error - it happens when speechSynthesis.cancel() is called
        if (event?.error === 'canceled') {
          setIsSpeaking(false);
          setIsPaused(false);
          return;
        }
        setError(event?.error || 'Speech synthesis error');
        setIsSpeaking(false);
        setIsPaused(false);
      };

      utteranceRef.current = utterance;
      window.speechSynthesis.cancel();
      window.speechSynthesis.speak(utterance);
    },
    [isSupported, loadVoices, selectedVoice, voices.length]
  );

  const stop = useCallback(() => {
    if (!isSupported) {
      return;
    }

    window.speechSynthesis.cancel();
    utteranceRef.current = null;
    selectedVoiceRef.current = selectedVoice;
    setIsSpeaking(false);
    setIsPaused(false);
  }, [isSupported, selectedVoice]);

  const pause = useCallback(() => {
    if (!isSupported || !isSpeaking) {
      return;
    }

    window.speechSynthesis.pause();
    setIsPaused(true);
  }, [isSpeaking, isSupported]);

  const resume = useCallback(() => {
    if (!isSupported || !isPaused) {
      return;
    }

    window.speechSynthesis.resume();
    setIsPaused(false);
  }, [isPaused, isSupported]);

  const api = useMemo<UseSpeechSynthesisReturn>(
    () => ({
      speak,
      stop,
      pause,
      resume,
      isSpeaking,
      isPaused,
      voices,
      selectedVoice,
      setVoice,
      rate,
      setRate: setRateValue,
      pitch,
      setPitch: setPitchValue,
      volume,
      setVolume: setVolumeValue,
      isSupported,
      error,
    }),
    [
      error,
      isPaused,
      isSpeaking,
      isSupported,
      pause,
      pitch,
      rate,
      resume,
      selectedVoice,
      setVoice,
      speak,
      stop,
      voices,
      volume,
      setPitchValue,
      setRateValue,
      setVolumeValue,
    ]
  );

  return api;
}
