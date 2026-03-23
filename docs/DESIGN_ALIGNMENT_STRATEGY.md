# Design Alignment Strategy: CodeSwiftr Brand → Product Landing → Application

**Date**: 2025-12-09
**Status**: Living Strategy
**Purpose**: Align design system across CodeSwiftr marketing site, product landing page, and application frontend

---

## Executive Summary

This document establishes a unified design strategy to align three distinct touchpoints which currently exhibit design drift.

1.  **Marketing Site** (`codeswiftr.localhost`) - Currently using "Legacy Deep Dark" theme with `Space Grotesk`.
2.  **Product Landing** (`localhost:5173`) - Currently using "Modern Clean" theme.
3.  **App Frontend** (`dashboard`) - Currently using `shadcn/ui` default styles.

**Goal**: Unify these into a single "CodeSwiftr Identity" that feels coherent while respecting the unique needs of each context (Marketing = Impact, App = Utility).

---

## 1. Discrepancy Analysis (Audit Findings)

We analyzed `marketing-template/src/styles/design-tokens.css` (Marketing) vs `DESIGN_SYSTEM.md` (Product/App).

| Feature | Marketing Site (Legacy/Current) | Product/App (Target/New) | **Decision / Action** |
| :--- | :--- | :--- | :--- |
| **Primary Color** | `#3B82F6` (Royal Blue) | `#38BDF8` (Electric Blue) | **Adopt `#38BDF8` (Electric Blue)**. It is more vibrant and modern. |
| **Brand Color** | `#E11D48` (Rose Red) accents | `#FF6B9D` (Pink/Magenta) | **Adopt `#FF6B9D` (Pink)**. Differentiates from generic tech red/blue. |
| **Headings Font** | `Space Grotesk` | `Outfit` | **Adopt `Outfit`**. It is cleaner and versatile for both display and UI. |
| **Body Font** | `Plus Jakarta Sans` | `Inter` | **Adopt `Inter`**. Standard for readability in complex UIs. |
| **Code Font** | `JetBrains Mono` | `JetBrains Mono` | **Keep**. Consistent! |
| **Dark Bg** | `#050505` (Pitch Black) | `#0F172A` (Slate 900) | **Context Dependent**. Marketing stays Pitch Black (`#050505`) for impact. App stays Slate (`#0F172A`) for reduced eye strain. |

---

## 2. Unified Design Strategy

### Core Identity Tokens ("The Winning Standards")

These tokens replace all legacy conflicting values.

```css
:root {
  /* BRAND IDENTITY */
  --color-brand-primary: #FF6B9D;    /* Pink/Magenta - The "Soul" */
  --color-brand-product: #38BDF8;    /* Electric Blue - The "Utility" */
  --color-brand-accent:  #00D9FF;    /* Cyan/Teal - The "Future/AI" */

  /* TYPOGRAPHY */
  --font-heading: "Outfit", system-ui, sans-serif;
  --font-body:    "Inter", system-ui, sans-serif;
  --font-mono:    "JetBrains Mono", monospace;
  
  /* NEUTRALS (Shared) */
  --color-charcoal-900: #111827;
  --color-slate-900:    #0F172A;
  --color-black-pure:   #050505;
}
```

### Theme Strategy by Context

We do NOT force one background color everywhere. Navigation and "feel" unifies them, not identical backgrounds.

*   **Marketing Context**: "The Stage"
    *   **Theme**: Always Dark (`#050505`).
    *   **Vibe**: High contrast, glowing, brave.
    *   **Action**: Update Primary Blue to `#38BDF8` and Fonts to `Outfit`/`Inter`.
*   **Product Context**: "The Workshop"
    *   **Theme**: User Choice (Light Default / Dark `#0F172A`).
    *   **Vibe**: Clean, low-distraction, functional.
    *   **Action**: Inject `#FF6B9D` (Pink) into brand moments (logo, success states).

---

## 3. Technical Implementation Strategy

To prevent future drift, we will align the technical implementation.

### Step 1: Centralize Tokens
Create a "Truth" definition (likely in the Product codebase's `globals.css` or a shared package) that defines the CSS variables above.

### Step 2: Marketing Site Update (`design-tokens.css`)
Update the `codeswiftr` domain block in `marketing-template/src/styles/design-tokens.css`:

```css
/* codeswiftr-com/interview-simulator/docs/FIXED_DESIGN_TOKENS.css */
[data-domain="codeswiftr"] {
    /* Fonts */
    --font-heading: 'Outfit', sans-serif; /* WAS: Space Grotesk */
    --font-body: 'Inter', sans-serif;     /* WAS: Plus Jakarta Sans */
    
    /* Colors */
    --palette-accent: #38BDF8;            /* WAS: #3B82F6 */
    --palette-accent-rgb: 56, 189, 248;
    
    /* New Brand Token */
    --brand-pink: #FF6B9D;
}
```

### Step 3: Product App Update (`tailwind.config.js`)
Ensure the Tailwind config references these CSS variables rather than hardcoded hex values where possible, or clearly defines the extended palette to match.

---

## 4. Implementation Roadmap

### Phase 1: Quick Wins (The "Visual Patch")
- [ ] **Marketing**: Update `design-tokens.css` to switch codeswiftr to `Outfit`/`Inter` and Electric Blue `#38BDF8`.
- [ ] **Marketing**: Fix the low-contrast "Secondary Button" issue (black text on dark bg).
- [ ] **Product**: Add small "Brand Pink" accents to the Dashboard (e.g., the Logo or a "Pro" badge).

### Phase 2: Design System Hardening
- [ ] Update `DESIGN_SYSTEM.md` to formally deprecate `Space Grotesk`.
- [ ] Refactor Product App to use CSS variables for primary colors (allowing easier theming).

### Phase 3: Alignment Verification
- [ ] **Visual Regresion**: Check if changing the marketing font broke any layouts (line-height differences).
- [ ] **Accessibility**: Verify `#38BDF8` text contrast on white backgrounds (might need a darker shade for text, e.g., `#0284C7`).

---

## Success Metrics

1.  **Font Consistency**: 0 occurrences of `Space Grotesk` on the `codeswiftr` marketing page.
2.  **Color Consistency**: Primary Action buttons on Marketing and App share the exact same Hex (`#38BDF8`).
3.  **Brand Presence**: The "Brand Pink" (`#FF6B9D`) is visible on the landing page (e.g., logo or hero graphic) and the app (logo).

