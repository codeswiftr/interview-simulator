# CareerSwiftr Interview Simulator - Design System

## Brand Identity

### Brand Positioning
- **Product**: AI-powered interview simulator for software engineers
- **Parent Brand**: CodeSwiftr
- **Positioning**: "Simulator, not Copilot" - We train candidates, not cheat for them
- **Tone**: Technical, precise, trustworthy, encouraging

### Brand Values
1. **Technical Excellence** - Professional tools for professionals
2. **Honest Feedback** - Direct, actionable insights without sugar-coating
3. **Privacy First** - Your practice sessions are yours alone
4. **Continuous Improvement** - Track progress over time

---

## Color System

### Primary Palette (CodeSwiftr)
```css
/* Core Brand Colors */
--color-charcoal: #111827;        /* Primary dark - backgrounds, text */
--color-electric-blue: #38BDF8;   /* Primary accent - CTAs, highlights */
--color-clean-white: #F8FAFC;     /* Light backgrounds */

/* RGB variants for opacity */
--color-charcoal-rgb: 17, 24, 39;
--color-electric-blue-rgb: 56, 189, 248;
```

### Extended Palette
```css
/* Surface Colors */
--surface-primary: #F8FAFC;       /* Main background */
--surface-secondary: #F1F5F9;     /* Cards, sections */
--surface-tertiary: #E2E8F0;      /* Hover states */
--surface-dark: #111827;          /* Dark mode / headers */
--surface-dark-alt: #1F2937;      /* Dark mode cards */

/* Text Colors */
--text-primary: #111827;          /* Main text */
--text-secondary: #475569;        /* Subdued text */
--text-tertiary: #94A3B8;         /* Placeholder, hints */
--text-inverse: #F8FAFC;          /* Text on dark bg */

/* Border Colors */
--border-light: #E2E8F0;
--border-medium: #CBD5E1;
--border-focus: #38BDF8;
```

### Semantic Colors
```css
/* Feedback Scores */
--score-excellent: #10B981;       /* 90-100 - Emerald */
--score-good: #22C55E;            /* 75-89 - Green */
--score-average: #EAB308;         /* 60-74 - Yellow */
--score-needs-work: #F97316;      /* 40-59 - Orange */
--score-poor: #EF4444;            /* 0-39 - Red */

/* Status Colors */
--status-success: #10B981;
--status-warning: #F59E0B;
--status-error: #EF4444;
--status-info: #38BDF8;

/* Interview States */
--state-scheduled: #6366F1;       /* Indigo */
--state-in-progress: #38BDF8;     /* Electric Blue */
--state-completed: #10B981;       /* Emerald */
--state-cancelled: #94A3B8;       /* Slate */
```

### Gradients
```css
/* Primary Gradient - CTAs and highlights */
--gradient-primary: linear-gradient(135deg, #38BDF8 0%, #0EA5E9 100%);

/* Dark Gradient - Headers and hero */
--gradient-dark: linear-gradient(180deg, #111827 0%, #1F2937 100%);

/* Surface Gradient - Subtle depth */
--gradient-surface: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%);

/* Score Gradients - Visual feedback */
--gradient-excellent: linear-gradient(135deg, #10B981 0%, #059669 100%);
--gradient-poor: linear-gradient(135deg, #EF4444 0%, #DC2626 100%);

/* Glow Effects */
--glow-blue: 0 0 20px rgba(56, 189, 248, 0.3);
--glow-success: 0 0 20px rgba(16, 185, 129, 0.3);
```

---

## Typography

### Font Stack
```css
/* Headings - Modern, technical feel */
--font-heading: "Outfit", system-ui, -apple-system, BlinkMacSystemFont, sans-serif;

/* Body - Highly readable */
--font-body: "Inter", system-ui, -apple-system, BlinkMacSystemFont, sans-serif;

/* Code/Technical - For code snippets, scores */
--font-mono: "JetBrains Mono", "Fira Code", ui-monospace, monospace;
```

### Type Scale
```css
/* Headings */
--text-4xl: 2.25rem;    /* 36px - Hero headlines */
--text-3xl: 1.875rem;   /* 30px - Page titles */
--text-2xl: 1.5rem;     /* 24px - Section headers */
--text-xl: 1.25rem;     /* 20px - Card titles */
--text-lg: 1.125rem;    /* 18px - Subtitles */

/* Body */
--text-base: 1rem;      /* 16px - Body text */
--text-sm: 0.875rem;    /* 14px - Secondary text */
--text-xs: 0.75rem;     /* 12px - Captions, labels */

/* Line Heights */
--leading-tight: 1.25;
--leading-normal: 1.5;
--leading-relaxed: 1.75;

/* Font Weights */
--font-normal: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;
```

### Typography Classes (Tailwind)
```css
/* Preset typography styles */
.heading-hero { @apply font-heading text-4xl font-bold leading-tight; }
.heading-page { @apply font-heading text-3xl font-bold leading-tight; }
.heading-section { @apply font-heading text-2xl font-semibold leading-tight; }
.heading-card { @apply font-heading text-xl font-semibold leading-tight; }
.body-large { @apply font-body text-lg leading-relaxed; }
.body-default { @apply font-body text-base leading-normal; }
.body-small { @apply font-body text-sm leading-normal; }
.label { @apply font-body text-xs font-medium uppercase tracking-wide; }
.score-display { @apply font-mono text-3xl font-bold; }
```

---

## Spacing & Layout

### Spacing Scale (8px base)
```css
--space-0: 0;
--space-1: 0.25rem;   /* 4px */
--space-2: 0.5rem;    /* 8px */
--space-3: 0.75rem;   /* 12px */
--space-4: 1rem;      /* 16px */
--space-5: 1.25rem;   /* 20px */
--space-6: 1.5rem;    /* 24px */
--space-8: 2rem;      /* 32px */
--space-10: 2.5rem;   /* 40px */
--space-12: 3rem;     /* 48px */
--space-16: 4rem;     /* 64px */
--space-20: 5rem;     /* 80px */
--space-24: 6rem;     /* 96px */
```

### Container Widths
```css
--container-xs: 20rem;   /* 320px - Modals */
--container-sm: 24rem;   /* 384px - Small cards */
--container-md: 28rem;   /* 448px - Forms */
--container-lg: 32rem;   /* 512px - Standard cards */
--container-xl: 36rem;   /* 576px - Wide cards */
--container-2xl: 42rem;  /* 672px - Content area */
--container-3xl: 48rem;  /* 768px - Main content */
--container-4xl: 56rem;  /* 896px - Wide content */
--container-5xl: 64rem;  /* 1024px - Dashboard */
--container-max: 80rem;  /* 1280px - Maximum width */
```

### Grid System
```css
/* Interview Dashboard Grid */
.dashboard-grid {
  display: grid;
  grid-template-columns: 280px 1fr 320px;
  gap: var(--space-6);
}

/* Question Grid */
.question-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--space-4);
}

/* Feedback Grid */
.feedback-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-4);
}
```

### Responsive Breakpoints
```css
--breakpoint-sm: 640px;   /* Mobile landscape */
--breakpoint-md: 768px;   /* Tablets */
--breakpoint-lg: 1024px;  /* Small laptops */
--breakpoint-xl: 1280px;  /* Desktops */
--breakpoint-2xl: 1536px; /* Large screens */
```

---

## Components

### Buttons

#### Primary Button
```css
.btn-primary {
  @apply px-6 py-3 rounded-lg font-semibold text-white
         bg-gradient-to-r from-electric-blue to-sky-500
         hover:from-sky-400 hover:to-electric-blue
         active:scale-[0.98] transition-all duration-200
         shadow-md hover:shadow-lg hover:shadow-electric-blue/25;
}
```

#### Secondary Button
```css
.btn-secondary {
  @apply px-6 py-3 rounded-lg font-semibold
         bg-surface-secondary text-text-primary
         border border-border-light
         hover:bg-surface-tertiary hover:border-border-medium
         active:scale-[0.98] transition-all duration-200;
}
```

#### Ghost Button
```css
.btn-ghost {
  @apply px-6 py-3 rounded-lg font-semibold
         text-electric-blue hover:bg-electric-blue/10
         active:scale-[0.98] transition-all duration-200;
}
```

#### Button Sizes
```css
.btn-sm { @apply px-4 py-2 text-sm; }
.btn-md { @apply px-6 py-3 text-base; }
.btn-lg { @apply px-8 py-4 text-lg; }
```

### Cards

#### Base Card
```css
.card {
  @apply bg-white rounded-xl border border-border-light
         shadow-sm hover:shadow-md transition-shadow duration-200;
}
```

#### Glass Card (Premium feel)
```css
.card-glass {
  @apply rounded-xl backdrop-blur-lg
         bg-white/70 border border-white/50
         shadow-lg;
}
```

#### Interactive Card
```css
.card-interactive {
  @apply bg-white rounded-xl border border-border-light
         shadow-sm cursor-pointer
         hover:shadow-md hover:border-electric-blue/50
         hover:translate-y-[-2px] transition-all duration-200;
}
```

#### Score Card
```css
.card-score {
  @apply rounded-xl p-6 text-center
         bg-gradient-to-br from-surface-secondary to-white
         border border-border-light;
}
```

### Form Inputs

#### Text Input
```css
.input {
  @apply w-full px-4 py-3 rounded-lg
         bg-surface-primary border border-border-light
         text-text-primary placeholder:text-text-tertiary
         focus:outline-none focus:ring-2 focus:ring-electric-blue/50 focus:border-electric-blue
         transition-all duration-200;
}
```

#### Select
```css
.select {
  @apply w-full px-4 py-3 rounded-lg appearance-none
         bg-surface-primary border border-border-light
         text-text-primary cursor-pointer
         focus:outline-none focus:ring-2 focus:ring-electric-blue/50 focus:border-electric-blue
         transition-all duration-200
         bg-[url('data:image/svg+xml,...')] bg-no-repeat bg-[right_1rem_center];
}
```

### Badges & Tags

#### Category Badges
```css
.badge-behavioral { @apply bg-indigo-100 text-indigo-700 border border-indigo-200; }
.badge-technical { @apply bg-emerald-100 text-emerald-700 border border-emerald-200; }
.badge-system-design { @apply bg-amber-100 text-amber-700 border border-amber-200; }
```

#### Difficulty Badges
```css
.badge-easy { @apply bg-green-100 text-green-700; }
.badge-medium { @apply bg-yellow-100 text-yellow-700; }
.badge-hard { @apply bg-red-100 text-red-700; }
```

#### Status Badges
```css
.badge-status {
  @apply inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium;
}
.badge-scheduled { @apply bg-indigo-100 text-indigo-700; }
.badge-in-progress { @apply bg-blue-100 text-blue-700; }
.badge-completed { @apply bg-green-100 text-green-700; }
```

---

## Interview-Specific Components

### Recording Indicator
```css
.recording-indicator {
  @apply flex items-center gap-2 px-4 py-2 rounded-full
         bg-red-500 text-white font-medium;
}

.recording-indicator::before {
  content: '';
  @apply w-3 h-3 rounded-full bg-white animate-pulse;
}
```

### Timer Display
```css
.timer-display {
  @apply font-mono text-4xl font-bold text-text-primary
         tabular-nums tracking-tight;
}

.timer-warning { @apply text-amber-500; }
.timer-danger { @apply text-red-500; }
```

### Audio Waveform Container
```css
.waveform-container {
  @apply h-24 rounded-lg bg-surface-secondary
         border border-border-light overflow-hidden;
}
```

### Score Ring
```css
.score-ring {
  @apply relative w-32 h-32;
  /* SVG-based circular progress indicator */
}

.score-ring-excellent { --ring-color: var(--score-excellent); }
.score-ring-good { --ring-color: var(--score-good); }
.score-ring-average { --ring-color: var(--score-average); }
.score-ring-needs-work { --ring-color: var(--score-needs-work); }
.score-ring-poor { --ring-color: var(--score-poor); }
```

### Progress Bar
```css
.progress-bar {
  @apply h-2 rounded-full bg-surface-secondary overflow-hidden;
}

.progress-bar-fill {
  @apply h-full rounded-full transition-all duration-500 ease-out;
  background: var(--gradient-primary);
}
```

### Question Card (Interview Room)
```css
.question-card {
  @apply bg-gradient-to-br from-charcoal to-gray-800
         rounded-2xl p-8 text-white shadow-xl;
}

.question-card-header {
  @apply flex items-center justify-between mb-6;
}

.question-card-content {
  @apply text-xl font-medium leading-relaxed;
}
```

### Feedback Metric Card
```css
.metric-card {
  @apply bg-white rounded-xl p-6 border border-border-light;
}

.metric-card-header {
  @apply flex items-center justify-between mb-4;
}

.metric-card-value {
  @apply font-mono text-3xl font-bold;
}

.metric-card-label {
  @apply text-sm text-text-secondary mt-1;
}
```

---

## Page Layouts

### Landing Page
```
┌─────────────────────────────────────────────────────┐
│  Navigation (fixed, glass effect)                   │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Hero Section                                       │
│  - Headline + subheadline                           │
│  - CTA buttons                                      │
│  - Hero illustration                                │
│                                                     │
├─────────────────────────────────────────────────────┤
│  Features Grid (3 columns)                          │
├─────────────────────────────────────────────────────┤
│  How It Works (steps)                               │
├─────────────────────────────────────────────────────┤
│  Pricing Cards                                      │
├─────────────────────────────────────────────────────┤
│  Testimonials                                       │
├─────────────────────────────────────────────────────┤
│  Final CTA                                          │
├─────────────────────────────────────────────────────┤
│  Footer                                             │
└─────────────────────────────────────────────────────┘
```

### Dashboard Layout
```
┌─────────────────────────────────────────────────────┐
│  Top Bar (logo, search, user menu)                  │
├──────────┬──────────────────────────┬───────────────┤
│          │                          │               │
│  Sidebar │  Main Content            │  Quick Stats  │
│          │                          │               │
│  - Home  │  - Interview History     │  - Score avg  │
│  - Start │  - Recent Sessions       │  - Sessions   │
│  - History│  - Recommendations      │  - Streak     │
│  - Progress│                        │               │
│  - Settings│                        │               │
│          │                          │               │
└──────────┴──────────────────────────┴───────────────┘
```

### Interview Room Layout
```
┌─────────────────────────────────────────────────────┐
│  Timer                              Exit Button     │
├─────────────────────────────────────────────────────┤
│                                                     │
│                                                     │
│              Question Display Card                  │
│              (centered, prominent)                  │
│                                                     │
│                                                     │
├─────────────────────────────────────────────────────┤
│                                                     │
│              Waveform / Recording Area              │
│                                                     │
├─────────────────────────────────────────────────────┤
│  [Skip]              Status           [Submit/Next] │
└─────────────────────────────────────────────────────┘
```

### Feedback View Layout
```
┌─────────────────────────────────────────────────────┐
│  Back to Dashboard         Session Info             │
├──────────────────────┬──────────────────────────────┤
│                      │                              │
│  Overall Score       │  Detailed Breakdown          │
│  (large circular)    │                              │
│                      │  - Content Analysis          │
│  [Share] [Retry]     │  - Audio Analysis            │
│                      │  - Improvement Tips          │
│                      │                              │
├──────────────────────┴──────────────────────────────┤
│                                                     │
│  Transcript with Annotations                        │
│  (expandable)                                       │
│                                                     │
├─────────────────────────────────────────────────────┤
│  Similar Questions to Practice                      │
└─────────────────────────────────────────────────────┘
```

---

## Animations & Transitions

### Duration Scale
```css
--duration-instant: 0ms;
--duration-fast: 150ms;
--duration-normal: 200ms;
--duration-slow: 300ms;
--duration-slower: 500ms;
```

### Easing Functions
```css
--ease-default: cubic-bezier(0.4, 0, 0.2, 1);
--ease-in: cubic-bezier(0.4, 0, 1, 1);
--ease-out: cubic-bezier(0, 0, 0.2, 1);
--ease-bounce: cubic-bezier(0.68, -0.55, 0.265, 1.55);
```

### Standard Animations
```css
/* Fade In */
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* Slide Up */
@keyframes slideUp {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Scale In */
@keyframes scaleIn {
  from { opacity: 0; transform: scale(0.95); }
  to { opacity: 1; transform: scale(1); }
}

/* Recording Pulse */
@keyframes recordingPulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* Score Count Up */
@keyframes countUp {
  from { opacity: 0; transform: scale(0.5); }
  to { opacity: 1; transform: scale(1); }
}

/* Progress Fill */
@keyframes progressFill {
  from { width: 0; }
  to { width: var(--progress); }
}
```

### Utility Classes
```css
.animate-fade-in { animation: fadeIn var(--duration-normal) var(--ease-out); }
.animate-slide-up { animation: slideUp var(--duration-slow) var(--ease-out); }
.animate-scale-in { animation: scaleIn var(--duration-normal) var(--ease-bounce); }
.animate-recording { animation: recordingPulse 1.5s infinite; }
```

---

## Shadows & Effects

### Shadow Scale
```css
--shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
--shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
--shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
--shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1);
--shadow-2xl: 0 25px 50px -12px rgb(0 0 0 / 0.25);

/* Colored Shadows */
--shadow-blue: 0 10px 40px -10px rgba(56, 189, 248, 0.4);
--shadow-success: 0 10px 40px -10px rgba(16, 185, 129, 0.4);
```

### Glassmorphism
```css
.glass {
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.5);
}

.glass-dark {
  background: rgba(17, 24, 39, 0.8);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.1);
}
```

---

## Border Radius
```css
--radius-none: 0;
--radius-sm: 0.25rem;    /* 4px */
--radius-md: 0.5rem;     /* 8px */
--radius-lg: 0.75rem;    /* 12px */
--radius-xl: 1rem;       /* 16px */
--radius-2xl: 1.5rem;    /* 24px */
--radius-full: 9999px;   /* Pill shape */
```

---

## Icons

### Recommended Icon Set
**Lucide React** - Modern, consistent, MIT licensed
- Clean stroke-based icons
- Good technical/professional feel
- Excellent React integration

### Key Icons Needed
| Purpose | Icon Name | Usage |
|---------|-----------|-------|
| Recording | `Mic` / `MicOff` | Audio capture state |
| Timer | `Clock` | Session timing |
| Play/Pause | `Play` / `Pause` | Audio playback |
| Questions | `MessageSquare` | Question bank |
| Feedback | `BarChart2` | Analysis results |
| Progress | `TrendingUp` | Performance tracking |
| Settings | `Settings` | User preferences |
| User | `User` | Profile menu |
| Check | `Check` / `CheckCircle` | Success states |
| Warning | `AlertTriangle` | Warnings |
| Error | `XCircle` | Errors |
| Info | `Info` | Information |
| Categories | `Code` / `Users` / `Server` | Question types |

---

## Dark Mode Considerations

While MVP will be light mode only, design with dark mode in mind:

```css
/* CSS Variables for easy theming */
:root {
  --bg-primary: var(--surface-primary);
  --bg-secondary: var(--surface-secondary);
  --text-primary: var(--text-primary);
  --text-secondary: var(--text-secondary);
}

/* Dark mode (future) */
:root.dark {
  --bg-primary: #111827;
  --bg-secondary: #1F2937;
  --text-primary: #F8FAFC;
  --text-secondary: #94A3B8;
}
```

---

## Accessibility Guidelines

### Color Contrast
- Text on light bg: minimum 4.5:1 ratio (WCAG AA)
- Large text: minimum 3:1 ratio
- Interactive elements: clearly distinguishable

### Focus States
```css
*:focus-visible {
  outline: 2px solid var(--color-electric-blue);
  outline-offset: 2px;
}
```

### Touch Targets
- Minimum 44x44px for interactive elements
- Adequate spacing between clickable items

### Motion
```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## Tailwind Configuration

```javascript
// tailwind.config.js
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        charcoal: '#111827',
        'electric-blue': '#38BDF8',
        'clean-white': '#F8FAFC',
        surface: {
          primary: '#F8FAFC',
          secondary: '#F1F5F9',
          tertiary: '#E2E8F0',
        },
        score: {
          excellent: '#10B981',
          good: '#22C55E',
          average: '#EAB308',
          'needs-work': '#F97316',
          poor: '#EF4444',
        },
      },
      fontFamily: {
        heading: ['Outfit', 'system-ui', 'sans-serif'],
        body: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      animation: {
        'fade-in': 'fadeIn 0.2s ease-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'scale-in': 'scaleIn 0.2s cubic-bezier(0.68, -0.55, 0.265, 1.55)',
        'recording-pulse': 'recordingPulse 1.5s infinite',
      },
      boxShadow: {
        'blue-glow': '0 10px 40px -10px rgba(56, 189, 248, 0.4)',
        'success-glow': '0 10px 40px -10px rgba(16, 185, 129, 0.4)',
      },
    },
  },
  plugins: [],
}
```

---

## Component Library Recommendation

### Primary: shadcn/ui
- Accessible by default (Radix primitives)
- Tailwind-based, fully customizable
- Copy-paste model (no dependency lock-in)
- Professional look out of the box

### Components to Use
- `Button`, `Input`, `Select` - Forms
- `Card` - Content containers
- `Dialog`, `Sheet` - Modals
- `DropdownMenu` - Navigation
- `Progress` - Visual indicators
- `Tabs` - Section navigation
- `Tooltip` - Contextual help
- `Toast` - Notifications

---

## Implementation Priority

### Phase 1: Core Components
1. Button variants
2. Input/Select forms
3. Cards (base, interactive, score)
4. Navigation (header, sidebar)
5. Typography system

### Phase 2: Interview Components
1. Question display card
2. Timer display
3. Recording indicator
4. Waveform visualization
5. Submit/navigation buttons

### Phase 3: Feedback Components
1. Score ring/circle
2. Progress bars
3. Metric cards
4. Transcript viewer
5. Improvement tips

### Phase 4: Dashboard
1. Session history list
2. Quick stats cards
3. Progress charts
4. Recommendation cards

---

## File Structure

```
frontend/src/
├── styles/
│   ├── globals.css       # CSS variables, base styles
│   └── tailwind.css      # Tailwind imports
├── components/
│   ├── ui/               # Base components (shadcn)
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── input.tsx
│   │   └── ...
│   ├── interview/        # Interview-specific
│   │   ├── QuestionCard.tsx
│   │   ├── Timer.tsx
│   │   ├── RecordingIndicator.tsx
│   │   └── Waveform.tsx
│   ├── feedback/         # Feedback components
│   │   ├── ScoreRing.tsx
│   │   ├── MetricCard.tsx
│   │   └── TranscriptViewer.tsx
│   └── layout/           # Layout components
│       ├── Header.tsx
│       ├── Sidebar.tsx
│       └── PageContainer.tsx
└── lib/
    └── utils.ts          # cn() helper, etc.
```

---

## Design Review Checklist

Before shipping any screen:
- [ ] Colors match brand palette
- [ ] Typography follows scale
- [ ] Spacing is consistent (8px grid)
- [ ] Interactive elements have hover/focus states
- [ ] Loading states defined
- [ ] Error states designed
- [ ] Empty states considered
- [ ] Mobile responsive
- [ ] Accessible (contrast, focus, labels)
- [ ] Animations smooth and purposeful
