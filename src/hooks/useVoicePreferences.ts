import { useCallback, useEffect, useState } from 'react';

export interface VoiceSettings {
  enabled: boolean;
  voiceName: string | null;
  rate: number; // 0.5 - 2.0
  pitch: number; // 0.5 - 2.0
  volume: number; // 0 - 1
  autoListen: boolean;
}

const STORAGE_KEY = 'voicePreferences';

const defaultSettings: VoiceSettings = {
  enabled: true,
  voiceName: null,
  rate: 1,
  pitch: 1,
  volume: 1,
  autoListen: false,
};

function loadFromStorage(): VoiceSettings {
  if (typeof window === 'undefined') return defaultSettings;
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return defaultSettings;
    const parsed = JSON.parse(raw) as Partial<VoiceSettings>;
    return {
      enabled: parsed.enabled ?? defaultSettings.enabled,
      voiceName: parsed.voiceName ?? defaultSettings.voiceName,
      rate: typeof parsed.rate === 'number' ? parsed.rate : defaultSettings.rate,
      pitch: typeof parsed.pitch === 'number' ? parsed.pitch : defaultSettings.pitch,
      volume: typeof parsed.volume === 'number' ? parsed.volume : defaultSettings.volume,
      autoListen: parsed.autoListen ?? defaultSettings.autoListen,
    };
  } catch {
    return defaultSettings;
  }
}

export function useVoicePreferences() {
  const [settings, setSettings] = useState<VoiceSettings>(() => loadFromStorage());

  // Persist to localStorage when settings change
  useEffect(() => {
    if (typeof window === 'undefined') return;
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
    } catch {
      // Ignore storage failures (e.g., private mode)
    }
  }, [settings]);

  const updateSettings = useCallback((partial: Partial<VoiceSettings>) => {
    setSettings((prev) => ({ ...prev, ...partial }));
  }, []);

  const resetSettings = useCallback(() => {
    setSettings(defaultSettings);
  }, []);

  return {
    settings,
    updateSettings,
    resetSettings,
    defaultSettings,
  };
}
