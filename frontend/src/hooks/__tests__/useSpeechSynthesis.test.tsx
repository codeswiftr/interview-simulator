import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useSpeechSynthesis } from '../useSpeechSynthesis';

type MockVoice = SpeechSynthesisVoice & { name: string; lang: string };

class MockSpeechSynthesisUtterance {
  text: string;
  voice: SpeechSynthesisVoice | null = null;
  rate = 1;
  pitch = 1;
  volume = 1;
  onstart: (() => void) | null = null;
  onend: (() => void) | null = null;
  onerror: ((event: { error?: string; message?: string }) => void) | null = null;
  onpause: (() => void) | null = null;
  onresume: (() => void) | null = null;

  constructor(text: string) {
    this.text = text;
  }
}

class MockSpeechSynthesis {
  voices: SpeechSynthesisVoice[] = [];
  lastUtterance: MockSpeechSynthesisUtterance | null = null;
  onvoiceschanged: (() => void) | null = null;
  speakMock = vi.fn();
  cancel = vi.fn(() => {
    this.lastUtterance = null;
  });
  pause = vi.fn(() => {
    this.lastUtterance?.onpause?.();
  });
  resume = vi.fn(() => {
    this.lastUtterance?.onresume?.();
  });

  getVoices = vi.fn(() => this.voices);

  speak = (utterance: MockSpeechSynthesisUtterance) => {
    this.lastUtterance = utterance;
    this.speakMock(utterance);
    utterance.onstart?.();
  };

  triggerVoicesChanged = () => {
    this.onvoiceschanged?.();
  };

  finish = () => {
    this.lastUtterance?.onend?.();
    this.lastUtterance = null;
  };

  triggerError = (error: string) => {
    this.lastUtterance?.onerror?.({ error, message: error });
  };

  setVoices(voices: SpeechSynthesisVoice[]) {
    this.voices = voices;
  }
}

const createVoice = (name: string, lang: string): MockVoice => ({
  name,
  lang,
  default: false,
  voiceURI: name,
  localService: true,
});

describe('useSpeechSynthesis', () => {
  let mockSpeech: MockSpeechSynthesis;
  let originalSpeechSynthesis: SpeechSynthesis | undefined;
  let originalUtterance: typeof SpeechSynthesisUtterance | undefined;

  beforeEach(() => {
    vi.clearAllMocks();
    mockSpeech = new MockSpeechSynthesis();
    originalSpeechSynthesis = (window as any).speechSynthesis;
    originalUtterance = (window as any).SpeechSynthesisUtterance;

    (window as any).speechSynthesis = mockSpeech;
    (window as any).SpeechSynthesisUtterance = MockSpeechSynthesisUtterance;
  });

  afterEach(() => {
    (window as any).speechSynthesis = originalSpeechSynthesis;
    (window as any).SpeechSynthesisUtterance = originalUtterance;
  });

  it('detects support when speech synthesis is available', () => {
    const { result } = renderHook(() => useSpeechSynthesis());
    expect(result.current.isSupported).toBe(true);
    expect(result.current.error).toBeNull();
  });

  it('detects lack of support when APIs are missing', () => {
    (window as any).speechSynthesis = undefined;
    (window as any).SpeechSynthesisUtterance = undefined;

    const { result } = renderHook(() => useSpeechSynthesis());
    expect(result.current.isSupported).toBe(false);
    expect(result.current.error).toContain('not supported');
  });

  it('loads voices and picks an English default', async () => {
    mockSpeech.setVoices([
      createVoice('Français', 'fr-FR'),
      createVoice('English US', 'en-US'),
    ]);

    const { result } = renderHook(() => useSpeechSynthesis());

    await waitFor(() => {
      expect(result.current.voices).toHaveLength(2);
    });

    expect(result.current.selectedVoice?.name).toBe('English US');
  });

  it('updates voices when voiceschanged fires', async () => {
    mockSpeech.setVoices([createVoice('Temp', 'es-ES')]);
    const { result } = renderHook(() => useSpeechSynthesis());

    await waitFor(() => {
      expect(result.current.voices).toHaveLength(1);
    });

    mockSpeech.setVoices([
      createVoice('New English', 'en-GB'),
      createVoice('Another', 'de-DE'),
    ]);
    act(() => {
      mockSpeech.triggerVoicesChanged();
    });

    await waitFor(() => {
      expect(result.current.voices).toHaveLength(2);
    });
    expect(result.current.selectedVoice?.name).toBe('New English');
  });

  it('speaks text with selected voice and updates state', async () => {
    mockSpeech.setVoices([createVoice('English', 'en-US')]);
    const { result } = renderHook(() => useSpeechSynthesis());

    await waitFor(() => {
      expect(result.current.selectedVoice).not.toBeNull();
    });

    act(() => {
      result.current.speak('Hello world');
    });

    expect(mockSpeech.speakMock).toHaveBeenCalledTimes(1);
    expect(result.current.isSpeaking).toBe(true);
    expect(mockSpeech.lastUtterance?.voice?.name).toBe('English');
    expect(mockSpeech.lastUtterance?.text).toBe('Hello world');

    act(() => {
      mockSpeech.finish();
    });

    expect(result.current.isSpeaking).toBe(false);
    expect(result.current.isPaused).toBe(false);
  });

  it('applies rate, pitch, volume, and manual voice selection', async () => {
    const voices = [createVoice('English', 'en-US'), createVoice('Premium', 'en-GB')];
    mockSpeech.setVoices(voices);
    const { result } = renderHook(() => useSpeechSynthesis());

    await waitFor(() => {
      expect(result.current.voices).toHaveLength(2);
    });

    act(() => {
      result.current.setRate(1.5);
      result.current.setPitch(0.8);
      result.current.setVolume(0.6);
      result.current.setVoice(voices[1]);
      result.current.speak('Testing settings');
    });

    expect(mockSpeech.lastUtterance?.voice?.name).toBe('Premium');
    expect(mockSpeech.lastUtterance?.rate).toBe(1.5);
    expect(mockSpeech.lastUtterance?.pitch).toBe(0.8);
    expect(mockSpeech.lastUtterance?.volume).toBe(0.6);
  });

  it('supports pause and resume controls', async () => {
    mockSpeech.setVoices([createVoice('English', 'en-US')]);
    const { result } = renderHook(() => useSpeechSynthesis());

    await waitFor(() => {
      expect(result.current.selectedVoice).not.toBeNull();
    });

    act(() => {
      result.current.speak('Pause me');
    });

    act(() => {
      result.current.pause();
    });
    expect(mockSpeech.pause).toHaveBeenCalled();
    expect(result.current.isPaused).toBe(true);

    act(() => {
      result.current.resume();
    });
    expect(mockSpeech.resume).toHaveBeenCalled();
    expect(result.current.isPaused).toBe(false);
  });

  it('stops speaking and clears state', async () => {
    mockSpeech.setVoices([createVoice('English', 'en-US')]);
    const { result } = renderHook(() => useSpeechSynthesis());

    await waitFor(() => {
      expect(result.current.selectedVoice).not.toBeNull();
    });

    act(() => {
      result.current.speak('Stop me');
    });

    act(() => {
      result.current.stop();
    });

    expect(mockSpeech.cancel).toHaveBeenCalled();
    expect(result.current.isSpeaking).toBe(false);
    expect(result.current.isPaused).toBe(false);
  });

  it('captures errors from utterance events', async () => {
    mockSpeech.setVoices([createVoice('English', 'en-US')]);
    const { result } = renderHook(() => useSpeechSynthesis());

    await waitFor(() => {
      expect(result.current.selectedVoice).not.toBeNull();
    });

    act(() => {
      result.current.speak('Error case');
    });

    act(() => {
      mockSpeech.triggerError('network');
    });

    expect(result.current.error).toContain('network');
    expect(result.current.isSpeaking).toBe(false);
  });
});
