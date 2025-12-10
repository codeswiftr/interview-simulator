# Milestone: Conversational Voice Mentor

## Status: ✅ COMPLETE
## Target: Sprint 9

---

## Overview

Transform the text-based mentor Q&A into a conversational voice experience, like a phone call with a career coach. The mentor will speak questions aloud, listen to user responses, and guide the conversation naturally.

**Current State**:
- Detective stage: Text-based Q&A with voice INPUT only (user can speak, mentor displays text)
- No Text-to-Speech (TTS) - mentor never "speaks"
- Disconnected feel - reading text breaks conversational flow

**Target State**:
- Mentor speaks questions aloud using Web Speech API
- Continuous conversation flow: mentor speaks → user responds → mentor processes → mentor speaks
- Phone-call-like experience with turn-taking indicators
- Premium voice options for enhanced experience

---

## Success Criteria

- [x] Mentor questions are spoken aloud using TTS
- [x] Conversation flows naturally with clear turn indicators
- [x] User can interrupt mentor while speaking
- [x] Voice settings persist in user preferences
- [x] Works across Chrome, Firefox, Safari, Edge
- [x] Graceful fallback for unsupported browsers
- [x] Free tier users can access basic preparation (Epic 4)
- [x] All tests passing, no TypeScript errors

---

## Technical Design

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     Conversational Voice Flow                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  User enters Detective Stage                                                 │
│       │                                                                      │
│       v                                                                      │
│  ┌─────────────┐     ┌──────────────┐     ┌─────────────┐                   │
│  │ MENTOR      │ --> │ USER         │ --> │ PROCESSING  │                   │
│  │ SPEAKING    │     │ TURN         │     │             │                   │
│  │             │     │              │     │             │                   │
│  │ TTS plays   │     │ Mic active   │     │ AI thinking │                   │
│  │ question    │     │ User speaks  │     │ Next Q      │                   │
│  │ Animated    │     │ STT captures │     │ Streaming   │                   │
│  └─────────────┘     └──────────────┘     └─────────────┘                   │
│       ^                                          │                           │
│       └──────────────────────────────────────────┘                           │
│                                                                              │
│  State Machine: mentor_speaking → user_turn → processing → mentor_speaking   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Data Models

**ConversationState** (React state):
```typescript
type ConversationMode = 'mentor_speaking' | 'user_turn' | 'processing' | 'idle';

interface VoiceSettings {
  enabled: boolean;
  voiceName: string;         // Selected voice identifier
  rate: number;              // Speech rate (0.5 - 2.0)
  pitch: number;             // Voice pitch (0.5 - 2.0)
  volume: number;            // Volume (0 - 1)
  autoListen: boolean;       // Auto-start listening after mentor speaks
}

interface ConversationState {
  mode: ConversationMode;
  isMentorSpeaking: boolean;
  isUserSpeaking: boolean;
  canInterrupt: boolean;
  transcript: string;
}
```

**User Preferences** (localStorage + API):
```typescript
interface UserPreferences {
  voiceSettings: VoiceSettings;
  preferConversationalMode: boolean;
}
```

### API Contracts

No new backend endpoints required for TTS (browser-native).

**Optional Enhancement** (Epic 3 - Premium Voices):
```
POST /api/tts/generate
Body: { text: string, voice_id: string }
Response: { audio_url: string } // Signed URL to audio file
```

### New Hooks

**useSpeechSynthesis** (Epic 1):
```typescript
interface UseSpeechSynthesisReturn {
  speak: (text: string) => void;
  stop: () => void;
  pause: () => void;
  resume: () => void;
  isSpeaking: boolean;
  isPaused: boolean;
  voices: SpeechSynthesisVoice[];
  selectedVoice: SpeechSynthesisVoice | null;
  setVoice: (voice: SpeechSynthesisVoice) => void;
  rate: number;
  setRate: (rate: number) => void;
  pitch: number;
  setPitch: (pitch: number) => void;
  isSupported: boolean;
  error: string | null;
}
```

**useConversationMode** (Epic 2):
```typescript
interface UseConversationModeReturn {
  mode: ConversationMode;
  startConversation: () => void;
  endConversation: () => void;
  transitionTo: (mode: ConversationMode) => void;
  mentorSay: (text: string) => Promise<void>;  // Speaks and waits
  onUserResponse: (callback: (text: string) => void) => void;
  interrupt: () => void;
  isActive: boolean;
}
```

### Dependencies

**Existing Components to Modify**:
| Component | Location | Changes |
|-----------|----------|---------|
| `PreparationPage` | `pages/PreparationPage.tsx` | Add conversational mode, TTS integration |
| `VoiceInputButton` | `components/common/VoiceInputButton.tsx` | Add auto-listen mode |
| `useSettings` | `hooks/useSettings.ts` | Add voice preferences |

**New Components to Create**:
| Component | Purpose |
|-----------|---------|
| `ConversationIndicator` | Visual feedback for who's turn (mentor/user) |
| `VoiceSettingsPanel` | Configure voice preferences |
| `MentorAvatar` | Animated avatar showing mentor state |

**New Hooks to Create**:
| Hook | Purpose |
|------|---------|
| `useSpeechSynthesis` | Text-to-Speech wrapper |
| `useConversationMode` | Conversation state machine |
| `useVoicePreferences` | Persist voice settings |

---

## Implementation Plan

### Epic 1: Voice Mentor - TTS Integration (ICE 8.4/10)

**Priority: HIGH** - Core feature enabling mentor to speak

#### Phase 1.1: useSpeechSynthesis Hook

| Task | Description | Est |
|------|-------------|-----|
| 1.1.1 | Create `useSpeechSynthesis` hook with speak/stop/pause | 1h |
| 1.1.2 | Add voice selection and listing | 0.5h |
| 1.1.3 | Add rate/pitch/volume controls | 0.5h |
| 1.1.4 | Add browser support detection | 0.5h |
| 1.1.5 | Write unit tests for hook | 0.5h |

**Implementation**:
```typescript
// frontend/src/hooks/useSpeechSynthesis.ts
import { useState, useEffect, useCallback, useRef } from 'react';

export function useSpeechSynthesis() {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([]);
  const [selectedVoice, setSelectedVoice] = useState<SpeechSynthesisVoice | null>(null);
  const [rate, setRate] = useState(1);
  const [pitch, setPitch] = useState(1);
  const [error, setError] = useState<string | null>(null);
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);

  const isSupported = typeof window !== 'undefined' && 'speechSynthesis' in window;

  useEffect(() => {
    if (!isSupported) return;

    const loadVoices = () => {
      const available = speechSynthesis.getVoices();
      setVoices(available);
      // Default to first English voice
      const englishVoice = available.find(v => v.lang.startsWith('en'));
      if (englishVoice && !selectedVoice) {
        setSelectedVoice(englishVoice);
      }
    };

    loadVoices();
    speechSynthesis.onvoiceschanged = loadVoices;

    return () => {
      speechSynthesis.onvoiceschanged = null;
    };
  }, [isSupported]);

  const speak = useCallback((text: string) => {
    if (!isSupported) {
      setError('Speech synthesis not supported');
      return;
    }

    // Cancel any ongoing speech
    speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.voice = selectedVoice;
    utterance.rate = rate;
    utterance.pitch = pitch;

    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => {
      setIsSpeaking(false);
      setIsPaused(false);
    };
    utterance.onerror = (e) => {
      setError(e.error);
      setIsSpeaking(false);
    };

    utteranceRef.current = utterance;
    speechSynthesis.speak(utterance);
  }, [isSupported, selectedVoice, rate, pitch]);

  const stop = useCallback(() => {
    speechSynthesis.cancel();
    setIsSpeaking(false);
    setIsPaused(false);
  }, []);

  const pause = useCallback(() => {
    speechSynthesis.pause();
    setIsPaused(true);
  }, []);

  const resume = useCallback(() => {
    speechSynthesis.resume();
    setIsPaused(false);
  }, []);

  return {
    speak,
    stop,
    pause,
    resume,
    isSpeaking,
    isPaused,
    voices,
    selectedVoice,
    setVoice: setSelectedVoice,
    rate,
    setRate,
    pitch,
    setPitch,
    isSupported,
    error,
  };
}
```

**Checkpoint**: Hook can speak text with configurable voice

---

#### Phase 1.2: Integrate TTS into Detective Stage

| Task | Description | Est |
|------|-------------|-----|
| 1.2.1 | Import useSpeechSynthesis in PreparationPage | 0.5h |
| 1.2.2 | Auto-speak questions when displayed | 0.5h |
| 1.2.3 | Add mute/unmute toggle button | 0.5h |
| 1.2.4 | Show speaking indicator animation | 0.5h |
| 1.2.5 | Test TTS in detective flow | 0.5h |

**Integration Point** (PreparationPage.tsx):
```typescript
// In detective stage rendering
const { speak, stop, isSpeaking, isSupported } = useSpeechSynthesis();
const [voiceEnabled, setVoiceEnabled] = useState(true);

useEffect(() => {
  if (currentQuestion && voiceEnabled && isSupported) {
    speak(currentQuestion);
  }
}, [currentQuestion, voiceEnabled]);
```

**Checkpoint**: Mentor speaks questions in detective stage

---

#### Phase 1.3: Voice Settings Panel

| Task | Description | Est |
|------|-------------|-----|
| 1.3.1 | Create VoiceSettingsPanel component | 1h |
| 1.3.2 | Add voice selection dropdown | 0.5h |
| 1.3.3 | Add rate/pitch sliders | 0.5h |
| 1.3.4 | Add "Test Voice" button | 0.5h |
| 1.3.5 | Persist settings to localStorage | 0.5h |
| 1.3.6 | Add to Settings page | 0.5h |

**Component Design**:
```typescript
interface VoiceSettingsPanelProps {
  onSettingsChange?: (settings: VoiceSettings) => void;
}
```

**Checkpoint**: Users can customize mentor voice

---

### Epic 2: Conversational Mode - Phone-like Experience (ICE 7.2/10)

**Priority: HIGH** - Transforms from Q&A to conversation

#### Phase 2.1: Conversation State Machine

| Task | Description | Est |
|------|-------------|-----|
| 2.1.1 | Create useConversationMode hook | 1.5h |
| 2.1.2 | Implement state transitions | 1h |
| 2.1.3 | Add interrupt handling | 0.5h |
| 2.1.4 | Write state machine tests | 0.5h |

**State Machine Implementation**:
```typescript
// frontend/src/hooks/useConversationMode.ts
type ConversationMode = 'idle' | 'mentor_speaking' | 'user_turn' | 'processing';

interface ConversationActions {
  mentorStartSpeaking: () => void;
  mentorFinishSpeaking: () => void;
  userStartSpeaking: () => void;
  userFinishSpeaking: (transcript: string) => void;
  startProcessing: () => void;
  finishProcessing: () => void;
  interrupt: () => void;
  reset: () => void;
}

export function useConversationMode(
  tts: ReturnType<typeof useSpeechSynthesis>,
  stt: ReturnType<typeof useSpeechRecognition>
): [ConversationMode, ConversationActions] {
  const [mode, setMode] = useState<ConversationMode>('idle');

  const actions: ConversationActions = useMemo(() => ({
    mentorStartSpeaking: () => setMode('mentor_speaking'),
    mentorFinishSpeaking: () => setMode('user_turn'),
    userStartSpeaking: () => { /* already in user_turn */ },
    userFinishSpeaking: () => setMode('processing'),
    startProcessing: () => setMode('processing'),
    finishProcessing: () => setMode('mentor_speaking'),
    interrupt: () => {
      tts.stop();
      setMode('user_turn');
    },
    reset: () => {
      tts.stop();
      stt.stopListening();
      setMode('idle');
    },
  }), [tts, stt]);

  return [mode, actions];
}
```

**Checkpoint**: State machine manages conversation flow

---

#### Phase 2.2: Conversation UI Indicators

| Task | Description | Est |
|------|-------------|-----|
| 2.2.1 | Create ConversationIndicator component | 1h |
| 2.2.2 | Add pulsing animation for mentor speaking | 0.5h |
| 2.2.3 | Add microphone animation for user turn | 0.5h |
| 2.2.4 | Add processing spinner | 0.5h |
| 2.2.5 | Integrate indicators into PreparationPage | 0.5h |

**Component Design**:
```typescript
// frontend/src/components/interview/ConversationIndicator.tsx
interface ConversationIndicatorProps {
  mode: ConversationMode;
  mentorName?: string;
}

export function ConversationIndicator({ mode, mentorName = 'Mentor' }: ConversationIndicatorProps) {
  return (
    <div className="flex items-center gap-3 p-4 bg-surface-secondary rounded-lg">
      {mode === 'mentor_speaking' && (
        <>
          <div className="w-10 h-10 rounded-full bg-electric-blue animate-pulse" />
          <span className="text-text-primary">{mentorName} is speaking...</span>
        </>
      )}
      {mode === 'user_turn' && (
        <>
          <Mic className="w-10 h-10 text-green-500 animate-pulse" />
          <span className="text-text-primary">Your turn to speak</span>
        </>
      )}
      {mode === 'processing' && (
        <>
          <Loader2 className="w-10 h-10 text-electric-blue animate-spin" />
          <span className="text-text-primary">Thinking...</span>
        </>
      )}
    </div>
  );
}
```

**Checkpoint**: Visual feedback shows conversation state

---

#### Phase 2.3: Auto-Listen Mode

| Task | Description | Est |
|------|-------------|-----|
| 2.3.1 | Add auto-listen after TTS completes | 1h |
| 2.3.2 | Add silence detection to end turn | 0.5h |
| 2.3.3 | Add manual "I'm done" button fallback | 0.5h |
| 2.3.4 | Test end-to-end conversation flow | 0.5h |

**Integration**:
```typescript
// In PreparationPage
useEffect(() => {
  if (mode === 'user_turn' && autoListen && !isListening) {
    startListening();
  }
}, [mode, autoListen]);

// When TTS ends, transition to user turn
useEffect(() => {
  if (!isSpeaking && mode === 'mentor_speaking') {
    actions.mentorFinishSpeaking();
  }
}, [isSpeaking, mode]);
```

**Checkpoint**: Conversation flows automatically

---

#### Phase 2.4: Interrupt Handling

| Task | Description | Est |
|------|-------------|-----|
| 2.4.1 | Detect user starting to speak during mentor | 0.5h |
| 2.4.2 | Stop TTS when interrupt detected | 0.5h |
| 2.4.3 | Add visual feedback for interrupt | 0.5h |
| 2.4.4 | Test interrupt scenarios | 0.5h |

**Checkpoint**: User can interrupt mentor naturally

---

### Epic 3: Premium Voice Quality (ICE 5.4/10)

**Priority: MEDIUM** - Enhancement for paid tiers

#### Phase 3.1: Voice Quality Assessment

| Task | Description | Est |
|------|-------------|-----|
| 3.1.1 | Analyze available browser voices | 0.5h |
| 3.1.2 | Rank voices by quality/naturalness | 0.5h |
| 3.1.3 | Create voice recommendation system | 1h |
| 3.1.4 | Add "Premium Voice" badge in settings | 0.5h |

**Voice Ranking Logic**:
```typescript
const PREMIUM_VOICES = [
  'Google UK English Female',
  'Google UK English Male',
  'Microsoft Zira',
  'Microsoft David',
  'Samantha',  // macOS
  'Daniel',    // macOS
];

function getVoiceQuality(voice: SpeechSynthesisVoice): 'premium' | 'standard' {
  return PREMIUM_VOICES.some(name => voice.name.includes(name))
    ? 'premium'
    : 'standard';
}
```

**Checkpoint**: Users see voice quality indicators

---

#### Phase 3.2: External TTS Integration (Optional)

| Task | Description | Est |
|------|-------------|-----|
| 3.2.1 | Research ElevenLabs/Google Cloud TTS APIs | 1h |
| 3.2.2 | Add backend endpoint for TTS generation | 2h |
| 3.2.3 | Implement audio streaming to frontend | 1h |
| 3.2.4 | Gate behind Pro subscription | 0.5h |

**Note**: This phase is optional and can be deferred. Browser TTS is sufficient for MVP.

**Checkpoint**: Premium users get high-quality voices

---

### Epic 4: Enable Prepare for Free Tier (ICE 7.0/10)

**Priority: HIGH** - Removes friction for new users

#### Phase 4.1: Update Subscription Gating

| Task | Description | Est |
|------|-------------|-----|
| 4.1.1 | Modify QuestionsPage canPrepare logic | 0.5h |
| 4.1.2 | Add usage limits for free tier | 1h |
| 4.1.3 | Create upgrade prompt component | 1h |
| 4.1.4 | Test free tier preparation flow | 0.5h |

**Implementation**:
```typescript
// QuestionsPage.tsx - Before:
const canPrepare = user?.subscription_tier === 'pro' || user?.subscription_tier === 'team';

// After:
const canPrepare = true;  // All users can prepare

// Add usage tracking
const FREE_TIER_PREP_LIMIT = 3;  // 3 preparations per month
const { prepCount, isLimitReached } = usePrepUsage();

// Show upgrade prompt when approaching limit
{isLimitReached && <UpgradePrompt feature="preparation" />}
```

---

#### Phase 4.2: Usage Tracking

| Task | Description | Est |
|------|-------------|-----|
| 4.2.1 | Add preparation_count to user model | 0.5h |
| 4.2.2 | Create API endpoint to track usage | 1h |
| 4.2.3 | Reset count monthly (cron/scheduled task) | 0.5h |
| 4.2.4 | Display usage in dashboard | 0.5h |

**Backend Changes**:
```python
# backend/app/models/user.py
class User:
    preparation_count: int = 0
    preparation_reset_date: datetime

# backend/app/api/preparation.py
@router.post("/sessions/{session_id}/prepare")
async def start_preparation(...):
    user = await get_current_user(...)
    if user.subscription_tier == 'free':
        if user.preparation_count >= FREE_TIER_LIMIT:
            raise HTTPException(402, "Upgrade to Pro for unlimited preparations")
        user.preparation_count += 1
        await user.save()
    # ... rest of logic
```

**Checkpoint**: Free users can try preparation with limits

---

## Testing Strategy

### Unit Tests
- **useSpeechSynthesis**: Mock speechSynthesis API, test speak/stop/pause
- **useConversationMode**: Test state transitions, interrupt handling
- **VoiceSettingsPanel**: Test voice selection, settings persistence
- **ConversationIndicator**: Test rendering for each mode

### Integration Tests
- Full conversation flow: mentor speaks → user responds → processing → mentor speaks
- Voice settings persistence across sessions
- Interrupt handling during mentor speech
- Free tier usage limits and upgrade prompts

### E2E Tests
- Complete detective stage with voice enabled
- Voice settings configuration and persistence
- Conversation mode toggle and flow

### Cross-Browser Testing
| Browser | TTS Support | Notes |
|---------|-------------|-------|
| Chrome | ✅ Full | Best voice selection |
| Firefox | ✅ Full | Limited voices |
| Safari | ✅ Full | Good macOS voices |
| Edge | ✅ Full | Microsoft voices |
| Mobile Safari | ⚠️ Limited | May require user gesture |
| Mobile Chrome | ✅ Full | Works well |

---

## Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| TTS not supported in some browsers | Medium | Low | Graceful fallback to text mode |
| Voice quality varies by OS/browser | Medium | High | Recommend best voices, allow customization |
| Interrupts cause state confusion | High | Medium | Debounce transitions, clear state machine |
| Auto-listen privacy concerns | Medium | Low | Default off, clear indicators |
| Mobile TTS requires gesture | Medium | Medium | Add "Start Conversation" button |
| Free tier abuse | Low | Medium | Rate limiting, monthly reset |

---

## Open Questions

- [x] Should conversation mode be opt-in or default? → **Opt-in with prominent toggle**
- [ ] Show transcript of what mentor said? → Recommend yes for accessibility
- [ ] Allow text input as alternative during conversation? → Yes, always fallback
- [ ] Voice settings: per-session or global? → Global in user preferences

---

## Files Summary

### New Files (7)
1. `frontend/src/hooks/useSpeechSynthesis.ts` - TTS hook
2. `frontend/src/hooks/useConversationMode.ts` - State machine
3. `frontend/src/hooks/useVoicePreferences.ts` - Settings persistence
4. `frontend/src/components/interview/ConversationIndicator.tsx` - Turn indicator
5. `frontend/src/components/settings/VoiceSettingsPanel.tsx` - Voice config UI
6. `frontend/src/components/common/UpgradePrompt.tsx` - Upsell component
7. `frontend/src/hooks/__tests__/useSpeechSynthesis.test.ts` - Tests

### Modified Files (5)
1. `frontend/src/pages/PreparationPage.tsx` - Add TTS, conversation mode
2. `frontend/src/pages/QuestionsPage.tsx` - Enable prepare for free tier
3. `frontend/src/pages/SettingsPage.tsx` - Add voice settings section
4. `frontend/src/hooks/useSettings.ts` - Add voice preferences
5. `backend/app/api/preparation.py` - Add usage tracking (Epic 4)

---

## Phase Summary

| Phase | Epic | Focus | Tasks | Dependencies |
|-------|------|-------|-------|--------------|
| 1.1 | 1 | useSpeechSynthesis Hook | 5 | None |
| 1.2 | 1 | TTS in Detective Stage | 5 | Phase 1.1 |
| 1.3 | 1 | Voice Settings Panel | 6 | Phase 1.1 |
| 2.1 | 2 | Conversation State Machine | 4 | Phase 1.2 |
| 2.2 | 2 | Conversation UI Indicators | 5 | Phase 2.1 |
| 2.3 | 2 | Auto-Listen Mode | 4 | Phase 2.2 |
| 2.4 | 2 | Interrupt Handling | 4 | Phase 2.3 |
| 3.1 | 3 | Voice Quality Assessment | 4 | Phase 1.3 |
| 3.2 | 3 | External TTS (Optional) | 4 | Phase 3.1 |
| 4.1 | 4 | Update Subscription Gating | 4 | None |
| 4.2 | 4 | Usage Tracking | 4 | Phase 4.1 |

---

## Execution Order (Recommended)

**Week 1: Core TTS**
1. Phase 1.1: useSpeechSynthesis Hook
2. Phase 1.2: TTS in Detective Stage
3. Phase 1.3: Voice Settings Panel

**Week 2: Conversation Mode**
4. Phase 2.1: Conversation State Machine
5. Phase 2.2: Conversation UI Indicators
6. Phase 2.3: Auto-Listen Mode
7. Phase 2.4: Interrupt Handling

**Week 3: Polish & Free Tier**
8. Phase 3.1: Voice Quality Assessment
9. Phase 4.1: Update Subscription Gating
10. Phase 4.2: Usage Tracking

**Optional (Future)**
- Phase 3.2: External TTS Integration

---

## Appendix: ICE-Scored Epic Priorities

| Epic | Impact | Confidence | Ease | ICE Score |
|------|--------|------------|------|-----------|
| Epic 1: Voice Mentor TTS | 9 | 9 | 8 | **8.4** |
| Epic 2: Conversational Mode | 9 | 8 | 7 | **7.2** |
| Epic 4: Free Tier Prepare | 8 | 9 | 7 | **7.0** |
| Epic 3: Premium Voice Quality | 6 | 6 | 6 | **5.4** |

---

## Previous Sprint Reference

### Sprint 8: Onboarding & Mentor Enhancement ✅ COMPLETE
- CoachOverlay props fix ✅
- Draft Voice Dictation ✅
- FirstSessionPrompt onboarding ✅
- ContextualTooltip component ✅
- HintHistoryPanel for coach hints ✅

### Sprint 7: Voice-Enabled Practice Mode ✅ COMPLETE
- Speech recognition hook ✅
- VoiceInputButton component ✅
- Detective Q&A voice integration ✅
- Practice coaching voice integration ✅

### Sprint 9: Conversational Voice Mentor ✅ COMPLETE (Dec 2025)

#### Epic 1: Voice Mentor TTS Integration ✅
- Phase 1.1: useSpeechSynthesis hook ✅
- Phase 1.2: TTS integrated into Detective Stage ✅
- Phase 1.3: VoiceSettingsPanel with voice selection ✅

#### Epic 2: Conversational Mode ✅
- Phase 2.1: useConversationMode state machine ✅
- Phase 2.2: ConversationIndicator UI component ✅
- Phase 2.3: Auto-listen mode after mentor speaks ✅
- Phase 2.4: Interrupt handling (stop TTS when user speaks) ✅

#### Epic 3: Premium Voice Quality ✅
- Phase 3.1: Voice quality assessment (premium badges) ✅
- voice-quality.ts with ranking utilities ✅
- VoiceSettingsPanel shows premium indicators ✅

#### Epic 4: Free Tier Prepare Access ✅
- Phase 4.1: Updated subscription gating ✅
- Phase 4.2: usePrepUsage hook (3/month limit, localStorage) ✅
- QuestionCard shows remaining preparations ✅

#### New Files Created:
- `frontend/src/hooks/useSpeechSynthesis.ts`
- `frontend/src/hooks/useConversationMode.ts`
- `frontend/src/hooks/useVoicePreferences.ts`
- `frontend/src/hooks/usePrepUsage.ts`
- `frontend/src/lib/voice-quality.ts`
- `frontend/src/components/interview/ConversationIndicator.tsx`
- `frontend/src/components/settings/VoiceSettingsPanel.tsx`

#### Files Modified:
- `frontend/src/pages/PreparationPage.tsx` - TTS + conversation mode
- `frontend/src/pages/QuestionsPage.tsx` - Free tier prepare access
- `frontend/src/pages/SettingsPage.tsx` - Voice settings section
- `frontend/src/components/questions/QuestionCard.tsx` - Usage badge
