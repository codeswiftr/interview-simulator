import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useVoicePreferences, type VoiceSettings } from '../useVoicePreferences';

const STORAGE_KEY = 'voicePreferences';

const getStored = () => {
  const raw = window.localStorage.getItem(STORAGE_KEY);
  return raw ? (JSON.parse(raw) as VoiceSettings) : null;
};

describe('useVoicePreferences', () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it('returns defaults when storage empty', () => {
    const { result } = renderHook(() => useVoicePreferences());
    expect(result.current.settings.enabled).toBe(true);
    expect(result.current.settings.voiceName).toBeNull();
    expect(result.current.settings.rate).toBe(1);
    expect(result.current.settings.pitch).toBe(1);
    expect(result.current.settings.volume).toBe(1);
  });

  it('loads settings from localStorage', () => {
    const stored: VoiceSettings = {
      enabled: false,
      voiceName: 'Samantha',
      rate: 1.2,
      pitch: 0.9,
      volume: 0.7,
      autoListen: true,
    };
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(stored));

    const { result } = renderHook(() => useVoicePreferences());

    expect(result.current.settings).toEqual(stored);
  });

  it('updates and persists partial changes', () => {
    const { result } = renderHook(() => useVoicePreferences());

    act(() => {
      result.current.updateSettings({ enabled: false, rate: 1.5 });
    });

    expect(result.current.settings.enabled).toBe(false);
    expect(result.current.settings.rate).toBe(1.5);

    const persisted = getStored();
    expect(persisted?.enabled).toBe(false);
    expect(persisted?.rate).toBe(1.5);
  });

  it('resets to defaults', () => {
    const { result } = renderHook(() => useVoicePreferences());

    act(() => {
      result.current.updateSettings({ voiceName: 'Google', volume: 0.4 });
    });

    act(() => {
      result.current.resetSettings();
    });

    expect(result.current.settings.voiceName).toBeNull();
    expect(result.current.settings.volume).toBe(1);
  });

  it('handles invalid JSON gracefully', () => {
    window.localStorage.setItem(STORAGE_KEY, '{invalid json');
    const { result } = renderHook(() => useVoicePreferences());
    expect(result.current.settings.rate).toBe(1);
  });

  it('ignores storage errors when persisting', () => {
    const setItemSpy = vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new Error('quota exceeded');
    });

    const { result } = renderHook(() => useVoicePreferences());

    act(() => {
      result.current.updateSettings({ pitch: 1.3 });
    });

    expect(result.current.settings.pitch).toBe(1.3);
    setItemSpy.mockRestore();
  });
});
