import { useMemo, useEffect } from 'react';
import type { VoiceSettings } from '../../hooks/useVoicePreferences';
import { getRecommendedVoice } from '../../lib/voice-quality';

interface VoiceSettingsPanelProps {
  settings: VoiceSettings;
  voices: SpeechSynthesisVoice[];
  isSupported: boolean;
  onChange: (partial: Partial<VoiceSettings>) => void;
  onTestVoice?: () => void;
  onReset?: () => void;
}

export function VoiceSettingsPanel({
  settings,
  voices,
  isSupported,
  onChange,
  onTestVoice,
  onReset,
}: VoiceSettingsPanelProps) {
  // Automatically select the best neural voice when voices are loaded
  const recommendedVoice = useMemo(() => getRecommendedVoice(voices), [voices]);

  // Auto-select recommended voice if no voice is set and voices are available
  useEffect(() => {
    if (recommendedVoice && !settings.voiceName && voices.length > 0) {
      onChange({ voiceName: recommendedVoice.name });
    }
  }, [recommendedVoice, settings.voiceName, voices.length, onChange]);

  return (
    <div className="space-y-3 sm:space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <label className="inline-flex items-center gap-2 text-sm font-medium text-text-primary">
          <input
            type="checkbox"
            checked={settings.enabled}
            onChange={(e) => onChange({ enabled: e.target.checked })}
            className="h-4 w-4"
          />
          <span className="text-xs sm:text-sm">Enable mentor voice (TTS)</span>
        </label>
        {!isSupported && (
          <span className="text-xs text-text-secondary">Not supported</span>
        )}
      </div>

      <div className="space-y-3 sm:space-y-4">
        {recommendedVoice && (
          <div className="p-2.5 sm:p-3 bg-electric-blue/5 dark:bg-electric-blue/10 rounded-lg border border-electric-blue/20">
            <p className="text-xs sm:text-sm text-text-secondary">
              <span className="font-medium text-text-primary">Using premium neural voice:</span>{' '}
              <span className="break-all">{recommendedVoice.name}</span> ({recommendedVoice.lang})
            </p>
            <p className="text-xs text-text-tertiary mt-1 hidden sm:block">
              Automatically selected for the best interview coaching experience
            </p>
          </div>
        )}

        {/* Rate - Full width on mobile, half on desktop */}
        <div className="space-y-2">
          <label className="label flex items-center justify-between text-sm">
            <span>Rate</span>
            <span className="text-xs text-text-tertiary font-mono">{settings.rate.toFixed(2)}x</span>
          </label>
          <input
            type="range"
            min={0.5}
            max={2}
            step={0.05}
            value={settings.rate}
            onChange={(e) => onChange({ rate: Number(e.target.value) })}
            className="w-full"
          />
          <p className="text-xs text-text-tertiary">1.0 is normal speed.</p>
        </div>

        {/* Pitch & Volume - Stack on mobile, side-by-side on desktop */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
          <div className="space-y-2">
            <label className="label flex items-center justify-between text-sm">
              <span>Pitch</span>
              <span className="text-xs text-text-tertiary font-mono">{settings.pitch.toFixed(2)}</span>
            </label>
            <input
              type="range"
              min={0.5}
              max={2}
              step={0.05}
              value={settings.pitch}
              onChange={(e) => onChange({ pitch: Number(e.target.value) })}
              className="w-full"
            />
          </div>

          <div className="space-y-2">
            <label className="label flex items-center justify-between text-sm">
              <span>Volume</span>
              <span className="text-xs text-text-tertiary font-mono">{settings.volume.toFixed(2)}</span>
            </label>
            <input
              type="range"
              min={0}
              max={1}
              step={0.05}
              value={settings.volume}
              onChange={(e) => onChange({ volume: Number(e.target.value) })}
              className="w-full"
            />
          </div>
        </div>
      </div>

      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 pt-2 border-t border-[hsl(var(--border))]">
        <label className="inline-flex items-center gap-2 text-sm font-medium text-text-primary">
          <input
            type="checkbox"
            checked={settings.autoListen}
            onChange={(e) => onChange({ autoListen: e.target.checked })}
            className="h-4 w-4"
          />
          <span className="text-xs sm:text-sm">Auto-listen after mentor speaks</span>
        </label>
        <div className="flex items-center gap-2">
          <button
            type="button"
            className="btn-ghost text-xs sm:text-sm px-3 sm:px-4 py-1.5 sm:py-2"
            onClick={onReset}
          >
            Reset
          </button>
          <button
            type="button"
            className="btn-secondary text-xs sm:text-sm px-3 sm:px-4 py-1.5 sm:py-2"
            onClick={onTestVoice}
            disabled={!isSupported || !settings.enabled}
          >
            Test Voice
          </button>
        </div>
      </div>
    </div>
  );
}

export default VoiceSettingsPanel;
