# Milestone: Interview UI Polish & Theme Fixes

## Status: Ready
## Target: Dec 2025 Sprint

---

## Overview

Address UI issues identified during visual testing with Playwright across mobile/desktop and light/dark themes. The Interview Page has a "recording studio" aesthetic that works well, but needs refinement for:

1. **Theme Consistency**: Cards use hardcoded dark gradients - intentional for focus but needs refinement
2. **Empty Visualizer State**: Blank dark rectangle without audio needs visual feedback
3. **Mobile Layout**: Skip Question button below fold, needs better positioning
4. **Recording Feedback**: Visualizer empty without audio stream needs placeholder animation

**Design Direction**: Tech Professional aesthetic with dark recording studio cards against adaptive backgrounds. The dark cards create focus and immersion regardless of system theme.

## Success Criteria

- [ ] QuestionDisplay and RecordingDeck have subtle light mode adaptation (lighter borders/glows)
- [ ] Empty visualizer shows animated waveform placeholder
- [ ] Skip Question visible on mobile without scrolling
- [ ] Recording deck shows activity indicator when awaiting audio
- [ ] All changes respect `prefers-reduced-motion`
- [ ] Lighthouse score maintained ≥90

---

## Technical Design

### Design Decision: Keep Dark Cards

After analysis, the dark "recording studio" cards are **intentional** and should remain dark in both themes. This creates:
- Visual focus on the interview content
- Immersive recording environment feel
- Professional appearance consistent with the "Tech Professional" aesthetic

However, we'll add subtle adaptations:
- Light mode: Add subtle colored glow/ring to cards
- Both modes: Animated placeholder for empty visualizer
- Mobile: Restructure layout for better content visibility

### Component Architecture

```
UI Polish Implementation
├── Theme Adaptations
│   ├── question-card CSS variations for light mode
│   ├── RecordingDeck border glow in light mode
│   └── Subtle background gradient adjustments
│
├── Visualizer Fallback
│   ├── WaveformPlaceholder component (CSS animation)
│   ├── Idle state pulse animation
│   └── "Microphone access required" indicator
│
├── Mobile Layout
│   ├── Sticky Skip Question on mobile
│   ├── Reduced vertical spacing
│   └── RecordingSection layout restructure
│
└── Recording Feedback
    ├── Audio level indicator placeholder
    ├── "Connecting..." state
    └── Error state styling
```

### Animation Tokens

```css
/* New animations for visualizer */
--animate-waveform: waveform 1.5s ease-in-out infinite;
--animate-pulse-soft: pulse-soft 2s ease-in-out infinite;
--animate-bar-bounce: bar-bounce 1s ease-in-out infinite;
```

---

## Implementation Plan

### Phase 1: Theme Adaptations (Light Mode Polish)
**Goal**: Dark cards feel intentional in light mode with subtle enhancements

| Task | Description | File | Agent | Est |
|------|-------------|------|-------|-----|
| 1.1 | Add light mode glow ring to question-card | globals.css | frontend-builder | 20m |
| 1.2 | Add ambient gradient background in light mode | InterviewPage.tsx | frontend-builder | 15m |
| 1.3 | Update RecordingDeck with light mode border enhancement | RecordingDeck.tsx | frontend-builder | 15m |
| 1.4 | Add subtle drop shadow variation for light mode | globals.css | frontend-builder | 10m |

**Checkpoint**: Dark cards look intentional and premium in light mode

**Implementation Details**:

```css
/* Task 1.1: Light mode glow ring for question-card */
.question-card {
  background: linear-gradient(145deg, #1F2937 0%, #111827 100%);
  border-radius: 1.5rem;
  padding: 3rem;
  color: white;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  border: 1px solid rgba(255,255,255,0.1);
  position: relative;
  overflow: hidden;
}

/* Light mode: Add colored glow to make dark card feel intentional */
:root:not(.dark) .question-card {
  box-shadow:
    0 25px 50px -12px rgba(0, 0, 0, 0.15),
    0 0 0 1px rgba(56, 189, 248, 0.1),
    0 0 60px -15px rgba(56, 189, 248, 0.2);
}

/* Task 1.4: Enhanced shadow in light mode */
:root:not(.dark) .recording-deck {
  box-shadow:
    0 20px 40px -12px rgba(0, 0, 0, 0.1),
    0 0 0 1px rgba(56, 189, 248, 0.15);
}
```

```tsx
// Task 1.2: InterviewPage.tsx ambient background
<div className="min-h-screen bg-surface-primary flex flex-col relative">
  {/* Ambient gradient for light mode - creates depth behind dark cards */}
  <div className="absolute inset-0 bg-gradient-to-b from-surface-primary via-surface-secondary/50 to-surface-primary dark:from-transparent dark:via-transparent dark:to-transparent pointer-events-none" />

  {/* Subtle radial glow behind content in light mode */}
  <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-electric-blue/5 via-transparent to-transparent dark:from-transparent pointer-events-none" />

  {/* Content */}
  <InterviewHeader />
  {/* ... rest of content with relative z-10 */}
</div>
```

---

### Phase 2: Visualizer Fallback Animation
**Goal**: Show animated placeholder when no audio stream

| Task | Description | File | Agent | Est |
|------|-------------|------|-------|-----|
| 2.1 | Create WaveformPlaceholder component | components/interview/WaveformPlaceholder.tsx | frontend-builder | 30m |
| 2.2 | Add waveform keyframes to globals.css | globals.css | frontend-builder | 15m |
| 2.3 | Integrate placeholder into RecordingDeck | RecordingDeck.tsx | frontend-builder | 15m |
| 2.4 | Add "awaiting microphone" state styling | RecordingDeck.tsx | frontend-builder | 15m |

**Checkpoint**: Visualizer area shows animated bars when idle/waiting

**Implementation Details**:

```tsx
// Task 2.1: WaveformPlaceholder.tsx
interface WaveformPlaceholderProps {
  isActive?: boolean;
  barCount?: number;
  className?: string;
}

export function WaveformPlaceholder({
  isActive = false,
  barCount = 40,
  className
}: WaveformPlaceholderProps) {
  return (
    <div
      className={cn(
        "flex items-end justify-center gap-[2px] h-full w-full px-4",
        className
      )}
      aria-hidden="true"
    >
      {Array.from({ length: barCount }).map((_, i) => {
        const baseHeight = 20 + Math.sin(i * 0.3) * 15;
        const delay = i * 0.05;

        return (
          <div
            key={i}
            className={cn(
              "w-1.5 rounded-full transition-all duration-300",
              isActive
                ? "bg-gradient-to-t from-electric-blue to-indigo-500 animate-bar-bounce"
                : "bg-gradient-to-t from-slate-600 to-slate-500 opacity-30"
            )}
            style={{
              height: `${baseHeight}%`,
              animationDelay: isActive ? `${delay}s` : undefined,
            }}
          />
        );
      })}
    </div>
  );
}
```

```css
/* Task 2.2: Waveform keyframes in globals.css */
@keyframes bar-bounce {
  0%, 100% {
    transform: scaleY(0.3);
    opacity: 0.5;
  }
  50% {
    transform: scaleY(1);
    opacity: 1;
  }
}

@keyframes pulse-soft {
  0%, 100% {
    opacity: 0.3;
    transform: scale(1);
  }
  50% {
    opacity: 0.6;
    transform: scale(1.02);
  }
}

.animate-bar-bounce {
  animation: bar-bounce 1s ease-in-out infinite;
}

/* Stagger the bars for wave effect */
.animate-bar-bounce:nth-child(even) {
  animation-delay: 0.1s;
}

/* Reduced motion support */
@media (prefers-reduced-motion: reduce) {
  .animate-bar-bounce {
    animation: none;
    transform: scaleY(0.5);
    opacity: 0.4;
  }
}
```

```tsx
// Task 2.3: RecordingDeck.tsx integration
{/* Visualizer Area */}
<div className="relative h-32 sm:h-40 bg-gradient-to-b from-slate-900 via-slate-800 to-slate-900 ...">
  {mediaStream ? (
    <canvas ref={canvasRef} ... />
  ) : (
    /* Placeholder when no stream */
    <WaveformPlaceholder isActive={isRecording} />
  )}

  {/* Awaiting mic overlay */}
  {isRecording && !mediaStream && (
    <div className="absolute inset-0 flex items-center justify-center bg-black/30">
      <div className="flex items-center gap-2 text-white/70 text-sm">
        <Loader2 className="w-4 h-4 animate-spin" />
        <span>Connecting microphone...</span>
      </div>
    </div>
  )}
</div>
```

---

### Phase 3: Mobile Layout Optimization
**Goal**: Skip Question visible without scroll, better mobile experience

| Task | Description | File | Agent | Est |
|------|-------------|------|-------|-----|
| 3.1 | Add sticky Skip Question for mobile | RecordingSection.tsx | frontend-builder | 20m |
| 3.2 | Reduce vertical spacing on mobile | InterviewPage.tsx, globals.css | frontend-builder | 15m |
| 3.3 | Compact question card padding on mobile | globals.css | frontend-builder | 10m |
| 3.4 | Move Skip inside RecordingDeck on mobile | RecordingDeck.tsx | frontend-builder | 25m |

**Checkpoint**: Full interview interface visible on mobile without scroll

**Implementation Details**:

```tsx
// Task 3.4: RecordingDeck with integrated Skip on mobile
{recordingState === 'idle' ? (
  <div className="p-6 sm:p-10 flex flex-col items-center justify-center gap-4 sm:gap-6 bg-gradient-to-b from-slate-900 via-slate-800 to-slate-900 min-h-[240px] sm:min-h-[280px]">
    {/* ... existing idle state content ... */}

    {/* Mobile-only Skip button integrated into idle deck */}
    <button
      onClick={onSkip}
      className="sm:hidden mt-2 text-sm text-white/40 hover:text-white/60 flex items-center gap-1.5"
    >
      <SkipForward size={14} />
      Skip Question
    </button>
  </div>
) : (
  /* Recording state */
)}
```

```css
/* Task 3.3: Compact question card on mobile */
.question-card {
  padding: 1.5rem;
}

@media (min-width: 640px) {
  .question-card {
    padding: 3rem;
  }
}

/* Task 3.2: Reduced spacing on mobile */
@media (max-width: 639px) {
  .interview-content {
    padding-top: 1rem;
    padding-bottom: 1rem;
    gap: 1rem;
  }

  .question-card h2 {
    font-size: 1.5rem;
    line-height: 1.3;
  }
}
```

---

### Phase 4: Recording State Feedback
**Goal**: Clear visual feedback during all recording states

| Task | Description | File | Agent | Est |
|------|-------------|------|-------|-----|
| 4.1 | Add microphone permission state indicator | RecordingDeck.tsx | frontend-builder | 20m |
| 4.2 | Add error state styling for failed recording | RecordingDeck.tsx | frontend-builder | 15m |
| 4.3 | Add connection/buffering state | RecordingDeck.tsx | frontend-builder | 15m |
| 4.4 | Update DevPreviewPage with new states | DevPreviewPage.tsx | frontend-builder | 10m |

**Checkpoint**: Users always know recording status

**Implementation Details**:

```tsx
// Task 4.1 & 4.3: Connection states in RecordingDeck
type ConnectionState = 'idle' | 'requesting' | 'connected' | 'error';

const [connectionState, setConnectionState] = useState<ConnectionState>('idle');

// In idle state render:
{connectionState === 'requesting' && (
  <div className="absolute inset-0 bg-black/60 flex flex-col items-center justify-center gap-3 z-10">
    <div className="w-12 h-12 rounded-full border-2 border-electric-blue/30 border-t-electric-blue animate-spin" />
    <p className="text-white/70 text-sm">Requesting microphone access...</p>
    <p className="text-white/40 text-xs">Allow access in your browser</p>
  </div>
)}

{connectionState === 'error' && (
  <div className="absolute inset-0 bg-black/60 flex flex-col items-center justify-center gap-3 z-10">
    <div className="p-3 rounded-full bg-status-error/20">
      <MicOff className="w-8 h-8 text-status-error" />
    </div>
    <p className="text-white/90 text-sm font-medium">Microphone access denied</p>
    <p className="text-white/50 text-xs text-center max-w-xs">
      Please allow microphone access in your browser settings to record
    </p>
    <button
      onClick={onRetryPermission}
      className="mt-2 px-4 py-2 bg-electric-blue text-white text-sm rounded-lg"
    >
      Try Again
    </button>
  </div>
)}
```

---

## Testing Strategy

### Visual Tests (Playwright)
- [ ] Desktop light theme - question card has subtle glow
- [ ] Desktop dark theme - maintains existing appearance
- [ ] Mobile light theme - compact layout, skip visible
- [ ] Mobile dark theme - same as above
- [ ] Visualizer placeholder animates when idle
- [ ] Recording states show correct feedback

### Accessibility Tests
- [ ] `prefers-reduced-motion` disables all animations
- [ ] Screen reader announces recording states
- [ ] Touch targets remain ≥44px

### Device Matrix

| Device | Test Focus |
|--------|------------|
| iPhone 14 Pro | Mobile layout, safe areas |
| iPhone SE | Small screen, compact mode |
| Desktop 1280px | Full experience |
| Desktop 1920px | Max width constraints |

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Dark cards jarring in light mode | Medium | Add subtle glow/ambient gradient |
| Animation performance on mobile | Low | CSS-only animations, reduce bar count |
| Layout shift on mobile | Medium | Fixed heights, skeleton states |
| Microphone permission UX | High | Clear feedback, retry option |

---

## Summary by Priority

| Phase | Tasks | Est | Impact |
|-------|-------|-----|--------|
| Phase 1 (Theme Polish) | 4 tasks | ~1h | Premium light mode feel |
| Phase 2 (Visualizer) | 4 tasks | ~1.25h | No empty states |
| Phase 3 (Mobile Layout) | 4 tasks | ~1.25h | Better mobile UX |
| Phase 4 (States) | 4 tasks | ~1h | Clear feedback |

**Total Estimated Effort**: ~4.5 hours

---

## Files to Modify

| File | Changes |
|------|---------|
| `globals.css` | New keyframes, light mode card styles |
| `RecordingDeck.tsx` | Visualizer fallback, connection states, mobile skip |
| `InterviewPage.tsx` | Ambient background, reduced mobile spacing |
| `RecordingSection.tsx` | Pass onSkip to RecordingDeck |
| `DevPreviewPage.tsx` | New state testing controls |
| **NEW** `WaveformPlaceholder.tsx` | Animated placeholder component |

---

## References

- Visual testing screenshots: `.playwright-mcp/interview-*.png`
- Existing PWA plan: `docs/PLAN.md`
- Design system: `globals.css`, `design-tokens.css`
- Frontend Design Skill: `.claude/skills/frontend-design/`
