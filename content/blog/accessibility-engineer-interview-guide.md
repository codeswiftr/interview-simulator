---
title: "Accessibility Engineer Interview Guide: WCAG, ARIA & Inclusive Design"
description: "Land accessibility engineering roles — WCAG 2.2 compliance, ARIA implementation, assistive technology testing, accessibility testing automation, and building accessibility-first engineering culture."
date: "2026-03-20"
category: "Specialty Engineering Roles"
---

# Accessibility Engineer Interview Guide: WCAG, ARIA & Inclusive Design

Web accessibility engineering is a growing specialization as companies face legal requirements (ADA, Section 508, EN 301 549), business pressure from disability advocates, and genuine commitment to inclusive design. Dedicated accessibility engineers are hired at large product companies (Apple, Microsoft, Google, Shopify) and accessibility consulting firms. This guide covers what accessibility engineering interviews test.

## WCAG 2.2 Compliance Framework

Accessibility engineers must know WCAG (Web Content Accessibility Guidelines) at a depth beyond checklist compliance:

**The four principles (POUR)**: Perceivable (information must be presentable to all users), Operable (all UI components must be navigable/usable), Understandable (information and UI operation must be comprehensible), Robust (content must be interpreted reliably by assistive technologies). WCAG success criteria fall under these principles.

**Conformance levels**: A (minimum), AA (standard target for most legal compliance), AAA (aspirational, rarely required for entire sites). Key AA criteria that appear in interviews:
- **1.4.3**: Text contrast ratio 4.5:1 (3:1 for large text)
- **1.4.11**: Non-text contrast 3:1 for UI components and graphical objects
- **2.4.3**: Focus order must be logical and meaningful
- **2.4.7**: Focus visible — keyboard focus indicator must be visible
- **1.4.4**: Text must be resizable to 200% without loss of content
- **2.5.3**: Label in Name — visible label text must be included in accessible name

**WCAG 2.2 new criteria**: Several additions specifically addressing mobile and cognitive accessibility. Know `2.4.11` (Focus Appearance — focus indicator requirements), `2.5.7` (Dragging Movements — alternatives for drag operations), and `3.2.6` (Consistent Help — help mechanisms must be consistent).

**Beyond checklists**: True accessibility requires usability testing with disabled users, not just automated scanner compliance. Engineers who understand the lived experience of screen reader, keyboard, and magnification users provide deeper value than those who only use automated tools.

## ARIA Implementation Best Practices

ARIA (Accessible Rich Internet Applications) extends HTML semantics for complex UI patterns:

**The ARIA prime directive**: "No ARIA is better than bad ARIA." ARIA overrides native semantics — incorrectly applied ARIA creates accessibility barriers worse than no ARIA. First principle: use native HTML elements with built-in semantics (button, input, nav, main) before reaching for ARIA.

**When ARIA is required**: Custom widgets that lack native HTML equivalents — datepickers, sliders, tabs, accordions, comboboxes, tree views. These require specific ARIA roles, states, and properties to be understandable by screen readers.

**ARIA roles, states, properties**: Roles define what the element is (`role="dialog"`, `role="combobox"`). States reflect current condition (`aria-expanded="true"`, `aria-selected="false"`). Properties provide additional context (`aria-label`, `aria-labelledby`, `aria-describedby`).

**Live regions**: Announce dynamic content changes to screen readers. `aria-live="polite"` (announce when user is idle), `aria-live="assertive"` (interrupt immediately), `role="status"` (polite), `role="alert"` (assertive). Misuse causes constant interruptions; absence means users miss important updates.

**Focus management**: Custom components must manage focus explicitly. Modals must trap focus when open (all Tab navigation stays within the modal) and return focus to the trigger when closed. Menu buttons open menus and focus first item on Arrow Down. Know the ARIA Authoring Practices Guide (APG) keyboard interaction patterns for each widget type.

Interview question: "Walk me through how you'd make a custom autocomplete search component accessible. What ARIA attributes are needed, how does keyboard interaction work, and how would you test it?" Strong answers cover `role="combobox"`, `aria-expanded`, `aria-activedescendant`, ARIA listbox/option structure, keyboard patterns (arrow navigation, Enter to select, Escape to close), and screen reader announcement of results count.

## Assistive Technology Testing

True accessibility requires testing with real tools:

**Screen readers**: VoiceOver (macOS/iOS — built-in, free), NVDA (Windows — most used by blind users, free), JAWS (Windows — enterprise standard, licensed), TalkBack (Android — built-in). Each behaves differently for the same HTML. Test with at least VoiceOver+Safari (iPhone users) and NVDA+Chrome (most common combination).

**Keyboard-only navigation**: Navigate your entire application using only Tab, Shift-Tab, Enter, Space, and arrow keys. Every interactive element must be reachable and operable. Focus indicator must be visible throughout. Skip navigation links are essential for long pages.

**Browser zoom and text sizing**: Test at 200% browser zoom and 200% text-only zoom (Firefox). Responsive designs usually handle browser zoom; text-only zoom breaks layouts that use px for font sizes (use rem/em instead).

**Color contrast checkers**: axe DevTools browser extension (most comprehensive automated checker), WebAIM Contrast Checker for manual verification, Lighthouse a11y audit for CI integration.

## Accessibility Testing Automation

Production accessibility engineering requires automated testing in CI/CD:

**axe-core**: The most widely used accessibility testing engine, available as browser extension, axe-playwright, axe-jest, and axe-selenium. Catches ~30-40% of WCAG issues automatically (the rule of thumb for automated a11y testing). Cannot catch issues requiring human judgment (meaningful alt text, logical focus order, error message clarity).

**Playwright accessibility testing**: `@playwright/test` with `AxeBuilder` for automated WCAG testing. Combine with visual regression testing (screenshots) to catch layout issues that affect cognitive accessibility.

**Jest + testing-library a11y queries**: `getByRole`, `getByLabelText`, `getByAltText` queries in React Testing Library test semantic HTML structure. Tests that only find elements by accessible roles/labels enforce accessible markup.

**CI integration**: Run axe-playwright on critical user flows in every PR. Set up accessibility violation thresholds (fail on WCAG AA critical violations, warn on minor issues). Generate a11y reports alongside test coverage reports.

## Interview Preparation

- Use NVDA+Chrome for one full week — use it as your primary way to navigate sites you use daily
- Audit an open-source project using only keyboard navigation and axe DevTools
- Implement an accessible modal, dropdown menu, and data table from scratch (no ARIA libraries)
- Read the ARIA Authoring Practices Guide thoroughly — it's the authoritative ARIA usage reference
- Study the WebAIM Million report — annual analysis of the top 1M website homepages for a11y issues

Accessibility engineering rewards genuine empathy for disabled users, technical depth in web standards, and the organizational change skills to move entire engineering teams toward accessible-by-default practices. It's increasingly important legally and commercially — and meaningfully improves the lives of the ~1.3 billion people with disabilities worldwide.
