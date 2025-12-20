# Milestone: PWA + Native Experience + Micro-Animations

## Status: Ready
## Target: Jan 2025 Sprint

---

## Overview

Transform Interview Simulator into a **production-grade Progressive Web App** with near-native iPhone 14 Pro experience and premium micro-animations. This milestone addresses:

1. **PWA Foundation**: Manifest, service worker, offline capabilities
2. **iOS Native Experience**: Safe area handling, meta tags, status bar styling
3. **Micro-Animations**: Button feedback, card interactions, score reveals
4. **Performance Polish**: Image optimization, install prompt UX

The goal is to create an installable, offline-capable app that feels native on iPhone 14 Pro (notch/Dynamic Island support) while maintaining web flexibility.

## Success Criteria

- [ ] Lighthouse PWA score ≥90
- [ ] App installable on iOS and Android
- [ ] Works offline (cached content accessible)
- [ ] Safe area insets handle iPhone 14 Pro notch
- [ ] Button clicks have tactile feedback (ripple/scale)
- [ ] Cards have entrance animations with stagger
- [ ] Score displays animate on reveal
- [ ] Build size <2MB gzipped

---

## Technical Design

### Architecture Overview

```
PWA + Polish Implementation
├── PWA Core
│   ├── manifest.json (auto-generated via vite-plugin-pwa)
│   ├── Service Worker (Workbox strategies)
│   ├── Offline page fallback
│   └── Install prompt component
│
├── Native Experience
│   ├── index.html meta tags (iOS, viewport-fit)
│   ├── Safe area CSS (env() insets)
│   ├── BottomNav padding adjustments
│   └── Status bar styling (black-translucent)
│
├── Animations
│   ├── globals.css keyframes (new)
│   ├── Tailwind utility classes
│   ├── Component-level transitions
│   └── Reduced motion support
│
└── Assets
    ├── PWA icons (192, 512 maskable)
    ├── Splash screens (optional)
    └── Offline HTML page
```

### Caching Strategy

| Resource Type | Strategy | Cache Duration | Rationale |
|---------------|----------|----------------|-----------|
| HTML pages | Network First | 1 day | Fresh content priority |
| API calls | Stale While Revalidate | 1 hour | Fast + background refresh |
| Images | Cache First | 7 days | Static, rarely change |
| Fonts | Cache First | 30 days | Very stable |
| JS/CSS | Network First | 1 day | Code updates critical |

### Animation Tokens

```css
/* New keyframes to add */
--animate-press: press 0.15s ease-out;           /* Button click */
--animate-ripple: ripple 0.6s ease-out;          /* Touch ripple */
--animate-reveal: reveal 0.5s ease-out;          /* Score counter */
--animate-stagger-in: stagger-in 0.3s ease-out;  /* List items */
--animate-bounce-in: bounce-in 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55);
```

---

## Implementation Plan

### Phase 1: PWA Foundation (MUST HAVE)
**Goal**: Installable, cacheable app with offline fallback

| Task | Description | File | Agent | Est |
|------|-------------|------|-------|-----|
| 1.1 | Install vite-plugin-pwa + workbox deps | package.json | - | 5m |
| 1.2 | Configure VitePWA in vite.config.ts | vite.config.ts | frontend-builder | 30m |
| 1.3 | Add PWA meta tags to index.html | index.html | frontend-builder | 15m |
| 1.4 | Convert logo-512.jpeg to PNG | public/images/ | - | 5m |
| 1.5 | Create offline.html fallback page | public/offline.html | frontend-builder | 20m |
| 1.6 | Add SW registration to main.tsx | src/main.tsx | frontend-builder | 15m |
| 1.7 | Create useOnlineStatus hook | src/hooks/ | frontend-builder | 15m |
| 1.8 | Test PWA installation on mobile | - | - | 30m |

**Checkpoint**: App installable, shows offline page when disconnected

**Implementation Details**:

```bash
# Task 1.1: Dependencies
npm install vite-plugin-pwa workbox-window
```

```typescript
// Task 1.2: vite.config.ts
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      manifest: {
        name: 'Interview Simulator - CareerSwiftr',
        short_name: 'Interview Prep',
        description: 'AI-powered interview practice for software engineers',
        theme_color: '#1a1a1a',
        background_color: '#ffffff',
        display: 'standalone',
        orientation: 'portrait-primary',
        scope: '/',
        start_url: '/',
        icons: [
          { src: '/images/logo-192.png', sizes: '192x192', type: 'image/png', purpose: 'any maskable' },
          { src: '/images/logo-512.png', sizes: '512x512', type: 'image/png', purpose: 'any maskable' },
        ],
      },
      workbox: {
        runtimeCaching: [
          {
            urlPattern: /^https:\/\/interview-simulator-api.*\/api\/v1\/.*/,
            handler: 'StaleWhileRevalidate',
            options: { cacheName: 'api-cache', expiration: { maxEntries: 50, maxAgeSeconds: 3600 } },
          },
          {
            urlPattern: /\.(?:png|jpg|jpeg|svg|gif|webp)$/,
            handler: 'CacheFirst',
            options: { cacheName: 'image-cache', expiration: { maxEntries: 100, maxAgeSeconds: 604800 } },
          },
          {
            urlPattern: /^https:\/\/fonts\.(googleapis|gstatic)\.com\/.*/,
            handler: 'CacheFirst',
            options: { cacheName: 'font-cache', expiration: { maxEntries: 20, maxAgeSeconds: 2592000 } },
          },
        ],
        navigateFallback: '/offline.html',
      },
    }),
  ],
})
```

```html
<!-- Task 1.3: index.html additions -->
<meta name="theme-color" content="#1a1a1a" />
<meta name="apple-mobile-web-app-capable" content="yes" />
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
<meta name="apple-mobile-web-app-title" content="Interview Prep" />
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover" />
<link rel="manifest" href="/manifest.webmanifest" />
```

---

### Phase 2: iOS Native Experience (MUST HAVE)
**Goal**: iPhone 14 Pro feels native with proper safe area handling

| Task | Description | File | Agent | Est |
|------|-------------|------|-------|-----|
| 2.1 | Add safe area CSS custom properties | globals.css | frontend-builder | 15m |
| 2.2 | Update BottomNav with safe area insets | BottomNav.tsx | frontend-builder | 20m |
| 2.3 | Add touch-action CSS for mobile | globals.css | frontend-builder | 10m |
| 2.4 | Create InstallPrompt component | components/pwa/ | frontend-builder | 45m |
| 2.5 | Add offline indicator banner | components/pwa/ | frontend-builder | 30m |
| 2.6 | Test on iPhone 14 Pro simulator | - | - | 30m |

**Checkpoint**: No content hidden by notch, smooth touch interactions

**Implementation Details**:

```css
/* Task 2.1: Safe area CSS in globals.css */
:root {
  --safe-area-inset-top: env(safe-area-inset-top, 0px);
  --safe-area-inset-right: env(safe-area-inset-right, 0px);
  --safe-area-inset-bottom: env(safe-area-inset-bottom, 0px);
  --safe-area-inset-left: env(safe-area-inset-left, 0px);
}

/* Fixed elements need safe area padding */
.safe-area-bottom {
  padding-bottom: max(1rem, var(--safe-area-inset-bottom));
}

.safe-area-top {
  padding-top: max(0.5rem, var(--safe-area-inset-top));
}

/* Task 2.3: Touch optimizations */
button, a, [role="button"] {
  touch-action: manipulation;
  -webkit-tap-highlight-color: transparent;
}

/* Prevent text selection on interactive elements */
.no-select {
  user-select: none;
  -webkit-user-select: none;
}
```

```tsx
// Task 2.2: BottomNav.tsx update
<nav className="fixed inset-x-0 bottom-0 bg-surface-primary border-t border-border-light
                safe-area-bottom md:hidden z-50">
  {/* Navigation items */}
</nav>
```

---

### Phase 3: Micro-Animations (SHOULD HAVE)
**Goal**: Premium feel with tactile feedback and smooth transitions

| Task | Description | File | Agent | Est |
|------|-------------|------|-------|-----|
| 3.1 | Add new keyframes (press, ripple, reveal) | globals.css | frontend-builder | 30m |
| 3.2 | Create ButtonRipple component | components/ui/ | frontend-builder | 45m |
| 3.3 | Add scale feedback to Button.tsx | Button.tsx | frontend-builder | 20m |
| 3.4 | Add card entrance animation | Card.tsx | frontend-builder | 20m |
| 3.5 | Add score counter animation to ScoreRing | ScoreRing.tsx | frontend-builder | 30m |
| 3.6 | Add stagger animation to list components | QuestionCard, MetricCard | frontend-builder | 30m |
| 3.7 | Add icon rotation on hover (buttons) | Button.tsx | frontend-builder | 15m |
| 3.8 | Add modal entrance enhancement | Modal.tsx | frontend-builder | 20m |
| 3.9 | Test with prefers-reduced-motion | - | - | 15m |

**Checkpoint**: All primary interactions have visual feedback

**Implementation Details**:

```css
/* Task 3.1: New keyframes in globals.css */
@keyframes press {
  0% { transform: scale(1); }
  50% { transform: scale(0.97); }
  100% { transform: scale(1); }
}

@keyframes ripple {
  0% {
    transform: scale(0);
    opacity: 0.5;
  }
  100% {
    transform: scale(4);
    opacity: 0;
  }
}

@keyframes reveal {
  0% {
    opacity: 0;
    transform: scale(0.8);
  }
  50% {
    transform: scale(1.05);
  }
  100% {
    opacity: 1;
    transform: scale(1);
  }
}

@keyframes count-up {
  from { --num: 0; }
}

@keyframes stagger-in {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Animation utilities */
.animate-press {
  animation: press 0.15s ease-out;
}

.animate-ripple {
  animation: ripple 0.6s ease-out forwards;
}

.animate-reveal {
  animation: reveal 0.5s ease-out forwards;
}

/* Stagger delay utilities */
.stagger-1 { animation-delay: 0.05s; }
.stagger-2 { animation-delay: 0.1s; }
.stagger-3 { animation-delay: 0.15s; }
.stagger-4 { animation-delay: 0.2s; }
.stagger-5 { animation-delay: 0.25s; }
```

```tsx
// Task 3.2: ButtonRipple component
// src/components/ui/ButtonRipple.tsx
import { useState, useCallback } from 'react';

interface RippleProps {
  x: number;
  y: number;
  size: number;
}

export function useRipple() {
  const [ripples, setRipples] = useState<RippleProps[]>([]);

  const createRipple = useCallback((event: React.MouseEvent<HTMLElement>) => {
    const button = event.currentTarget;
    const rect = button.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    const x = event.clientX - rect.left - size / 2;
    const y = event.clientY - rect.top - size / 2;

    const newRipple = { x, y, size };
    setRipples((prev) => [...prev, newRipple]);

    setTimeout(() => {
      setRipples((prev) => prev.slice(1));
    }, 600);
  }, []);

  return { ripples, createRipple };
}

export function Ripples({ ripples }: { ripples: RippleProps[] }) {
  return (
    <>
      {ripples.map((ripple, i) => (
        <span
          key={i}
          className="absolute rounded-full bg-white/30 pointer-events-none animate-ripple"
          style={{
            left: ripple.x,
            top: ripple.y,
            width: ripple.size,
            height: ripple.size,
          }}
        />
      ))}
    </>
  );
}
```

```tsx
// Task 3.3: Button.tsx enhancement
export function Button({ children, onClick, ...props }) {
  const { ripples, createRipple } = useRipple();
  const [isPressed, setIsPressed] = useState(false);

  const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
    createRipple(e);
    setIsPressed(true);
    setTimeout(() => setIsPressed(false), 150);
    onClick?.(e);
  };

  return (
    <button
      onClick={handleClick}
      className={cn(
        'relative overflow-hidden transition-transform',
        isPressed && 'scale-[0.97]',
        // ... existing classes
      )}
      {...props}
    >
      <Ripples ripples={ripples} />
      {children}
    </button>
  );
}
```

```tsx
// Task 3.6: Stagger animation for lists
// Usage in DashboardPage or similar
{items.map((item, index) => (
  <Card
    key={item.id}
    className={cn(
      'opacity-0 animate-stagger-in',
      `stagger-${Math.min(index + 1, 5)}`
    )}
    style={{ animationFillMode: 'forwards' }}
  >
    {/* Card content */}
  </Card>
))}
```

---

### Phase 4: Performance & Polish (COULD HAVE)
**Goal**: Optimized assets and refined install experience

| Task | Description | File | Agent | Est |
|------|-------------|------|-------|-----|
| 4.1 | Add WebP versions of hero images | public/images/ | - | 20m |
| 4.2 | Add lazy loading to image components | Various | frontend-builder | 30m |
| 4.3 | Create install success toast | components/pwa/ | frontend-builder | 20m |
| 4.4 | Add update available prompt | components/pwa/ | frontend-builder | 30m |
| 4.5 | Run Lighthouse audit and fix issues | - | - | 1h |

**Checkpoint**: Lighthouse PWA ≥90, images optimized

---

## Testing Strategy

### PWA Tests
- **Manifest validation**: All required fields present
- **Service worker**: Registers successfully, caches work
- **Offline mode**: App displays offline page
- **Install prompt**: Shows on supported browsers

### Animation Tests
- **Reduced motion**: All animations respect preference
- **Performance**: No jank on 60fps devices
- **Touch feedback**: Buttons respond within 50ms

### Device Testing Matrix

| Device | Test Focus |
|--------|------------|
| iPhone 14 Pro | Safe areas, notch, Dynamic Island |
| iPhone SE | Small screen layout |
| Android Pixel | Install prompt, PWA |
| Desktop Chrome | Full experience baseline |

### Manual Testing Checklist
- [ ] Install app from Chrome/Safari
- [ ] Disconnect network, verify offline page
- [ ] Reconnect, verify content loads
- [ ] Test buttons for ripple/press feedback
- [ ] Verify BottomNav doesn't overlap home indicator
- [ ] Check animations with reduced motion enabled

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Service worker caching stale content | High | Use autoUpdate strategy, version cache keys |
| iOS Safari PWA limitations | Medium | Test thoroughly, document known issues |
| Animation performance on low-end | Medium | Use CSS animations (GPU accelerated) |
| Safe area not applied in dev | Low | Test in iOS simulator during development |

---

## Dependencies

**Required Packages**:
```bash
npm install vite-plugin-pwa workbox-window
```

**Required Assets**:
- `logo-192.png` (exists)
- `logo-512.png` (convert from JPEG)
- `offline.html` (create)

---

## Commit Strategy

```
feat(pwa): add vite-plugin-pwa configuration and manifest
feat(pwa): add iOS meta tags and viewport-fit support
feat(pwa): implement offline page and service worker
feat(pwa): add safe area CSS for iPhone notch support
feat(ui): add button ripple effect and press feedback
feat(ui): add card entrance stagger animations
feat(ui): add score counter reveal animation
feat(ui): add InstallPrompt and OfflineIndicator components
perf(images): convert to WebP and add lazy loading
docs: update PLAN.md with PWA milestone completion
```

---

## Summary by Priority

| Priority | Tasks | Est | Impact |
|----------|-------|-----|--------|
| Phase 1 (PWA Core) | 8 tasks | ~2.5h | Installable, cacheable |
| Phase 2 (iOS Native) | 6 tasks | ~2.5h | Native feel on iPhone |
| Phase 3 (Animations) | 9 tasks | ~3.5h | Premium interactions |
| Phase 4 (Polish) | 5 tasks | ~2.5h | Performance + UX |

**Total Estimated Effort**: ~11 hours

---

## References

- [vite-plugin-pwa Docs](https://vite-pwa-org.netlify.app/)
- [Workbox Strategies](https://developer.chrome.com/docs/workbox/modules/workbox-strategies/)
- [Apple PWA Guidelines](https://developer.apple.com/design/human-interface-guidelines/web-apps)
- [Safe Area Insets](https://webkit.org/blog/7929/designing-websites-for-iphone-x/)
- [CSS Animation Performance](https://web.dev/animations-guide/)
