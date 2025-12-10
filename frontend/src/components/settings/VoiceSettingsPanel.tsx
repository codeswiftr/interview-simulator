import type { VoiceSettings } from '../../hooks/useVoicePreferences';

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
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <label className="inline-flex items-center gap-2 text-sm font-medium text-text-primary">
          <input
            type="checkbox"
            checked={settings.enabled}
            onChange={(e) => onChange({ enabled: e.target.checked })}
            className="h-4 w-4"
          />
          Enable mentor voice (TTS)
        </label>
        {!isSupported && (
          <span className="text-xs text-text-secondary">Not supported in this browser</span>
        )}
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-2">
          <label className="label">Voice</label>
          <select
            className="input w-full"
            value={settings.voiceName ?? ''}
            onChange={(e) => onChange({ voiceName: e.target.value || null })}
            disabled={!isSupported || voices.length === 0}
          >
            {voices.length === 0 && <option value="">Loading voices...</option>}
            {voices.length > 0 && <option value="">System default</option>}
            {voices.map((voice) => (
              <option key={`${voice.name}-${voice.lang}`} value={voice.name}>
                {voice.name} ({voice.lang})
              </option>
            ))}
          </select>
          <p className="text-xs text-text-tertiary">
            Voice availability depends on the OS and browser.
          </p>
        </div>

        <div className="space-y-2">
          <label className="label flex items-center justify-between">
            Rate
            <span className="text-xs text-text-tertiary">{settings.rate.toFixed(2)}x</span>
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
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-2">
          <label className="label flex items-center justify-between">
            Pitch
            <span className="text-xs text-text-tertiary">{settings.pitch.toFixed(2)}</span>
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
          <label className="label flex items-center justify-between">
            Volume
            <span className="text-xs text-text-tertiary">{settings.volume.toFixed(2)}</span>
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

      <div className="flex items-center justify-between">
        <label className="inline-flex items-center gap-2 text-sm font-medium text-text-primary">
          <input
            type="checkbox"
            checked={settings.autoListen}
            onChange={(e) => onChange({ autoListen: e.target.checked })}
            className="h-4 w-4"
          />
          Auto-listen after mentor speaks
        </label>
        <div className="flex items-center gap-2">
          <button
            type="button"
            className="btn-ghost text-sm"
            onClick={onReset}
          >
            Reset
          </button>
          <button
            type="button"
            className="btn-secondary text-sm"
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
