# Homepage UI/UX Refresh Plan

## Overview
This plan outlines improvements to refresh the homepage (`HomePage.tsx`) to better match the rest of the app's design system, improve mobile responsiveness, and ensure proper theme support (light/dark mode).

## Current Issues Identified

### 1. Mobile Responsiveness
- **Hero Section**: Uses `pt-32 pb-20 lg:pt-48 lg:pb-32` - excessive padding on mobile
- **Feature Cards**: Uses `p-8` - too much padding on mobile screens
- **CTA Section**: Uses `py-24` - excessive vertical padding on mobile
- **Hero Heading**: `heading-hero` class is 3.5rem - too large for mobile
- **Container Padding**: `px-6` might be too much on very small screens
- **Hero Image**: Large image with floating elements may not scale well on mobile

### 2. Design System Consistency
- **CTA Section**: Uses hardcoded colors (`bg-charcoal`, `text-white`, `text-gray-300`) instead of HSL tokens
- **Badge**: Uses hardcoded `bg-[#FF6B9D]` instead of HSL tokens
- **Feature Cards**: Uses `variant="glass"` which may not match other Card usage in the app
- **Colors**: Some direct color references instead of HSL design tokens

### 3. Typography
- **Hero Heading**: Needs responsive sizing (smaller on mobile)
- **Body Text**: Should use responsive text sizes
- **Section Headings**: Need responsive sizing

### 4. Spacing & Layout
- **Section Spacing**: All sections need responsive spacing
- **Feature Grid**: Needs better mobile layout (currently 2x2 on desktop, should stack on mobile)
- **Button Spacing**: Button groups need responsive gap sizing

### 5. Dark Mode Support
- **CTA Section**: Background doesn't properly adapt to dark mode
- **Text Colors**: Some text colors don't use HSL tokens for theme support
- **Badge Background**: Hardcoded color doesn't adapt to theme

## Implementation Plan

### Phase 1: Mobile Responsiveness

#### 1.1 Hero Section
- [ ] Reduce top padding: `pt-16 sm:pt-24 lg:pt-48` (from `pt-32 lg:pt-48`)
- [ ] Reduce bottom padding: `pb-12 sm:pb-16 lg:pb-32` (from `pb-20 lg:pb-32`)
- [ ] Make hero heading responsive: Add `text-3xl sm:text-4xl lg:text-6xl xl:text-7xl` to override `heading-hero` on mobile
- [ ] Reduce container padding on mobile: `px-4 sm:px-6`
- [ ] Reduce badge padding: `px-3 py-1.5 sm:px-4 sm:py-2`
- [ ] Reduce body text margin: `mb-6 sm:mb-8 lg:mb-10`
- [ ] Make hero image responsive: Add max-width constraints and responsive sizing
- [ ] Hide or resize floating audio score on mobile: `hidden sm:block` or smaller version

#### 1.2 Features Section
- [ ] Reduce section padding: `py-12 sm:py-16 lg:py-24` (from `py-24`)
- [ ] Reduce card padding: `p-4 sm:p-6 lg:p-8` (from `p-8`)
- [ ] Make feature grid single column on mobile: `grid-cols-1 md:grid-cols-2 lg:grid-cols-4`
- [ ] Reduce icon sizes on mobile: `w-10 h-10 sm:w-12 sm:h-12 lg:w-14 lg:h-14`
- [ ] Reduce section heading margin: `mb-8 sm:mb-12 lg:mb-16`
- [ ] Reduce gap between cards: `gap-4 sm:gap-6 lg:gap-8`

#### 1.3 CTA Section
- [ ] Reduce section padding: `py-12 sm:py-16 lg:py-24` (from `py-24`)
- [ ] Reduce heading margin: `mb-4 sm:mb-6`
- [ ] Reduce paragraph margin: `mb-6 sm:mb-8 lg:mb-10`
- [ ] Make button responsive: Ensure proper sizing on mobile

### Phase 2: Design System Consistency

#### 2.1 Replace Hardcoded Colors with HSL Tokens
- [ ] **CTA Section Background**: Replace `bg-charcoal` with `bg-[hsl(var(--surface-dark))] dark:bg-[hsl(var(--surface-dark-alt))]`
- [ ] **CTA Section Text**: Replace `text-white` with `text-text-inverse` or `text-[hsl(var(--text-inverse))]`
- [ ] **CTA Section Subtext**: Replace `text-gray-300` with `text-text-secondary` or appropriate HSL token
- [ ] **Badge Background**: Replace `bg-[#FF6B9D]` with `bg-[hsl(var(--brand-primary))]` or use design token
- [ ] **Badge Text**: Ensure uses HSL tokens for theme support

#### 2.2 Card Component Consistency
- [ ] Review if `variant="glass"` is appropriate or should use `variant="elevated"` to match Settings page
- [ ] Ensure all cards use consistent variant across the app
- [ ] Add proper hover states using design system tokens

#### 2.3 Button Consistency
- [ ] Ensure all buttons use `btn-primary` and `btn-secondary` classes
- [ ] Verify button styles match the rest of the app
- [ ] Ensure proper focus states using design system

### Phase 3: Typography Improvements

#### 3.1 Responsive Typography
- [ ] **Hero Heading**: Add responsive classes `text-3xl sm:text-4xl lg:text-6xl xl:text-7xl` with appropriate line-height
- [ ] **Section Headings**: Ensure `heading-section` is responsive or add responsive overrides
- [ ] **Body Text**: Use `body-default` with responsive sizing if needed
- [ ] **Card Headings**: Ensure `heading-card` is appropriately sized on mobile

### Phase 4: Dark Mode Support

#### 4.1 Theme-Aware Colors
- [ ] Verify all background colors use HSL tokens with dark mode variants
- [ ] Verify all text colors use HSL tokens
- [ ] Test CTA section in dark mode
- [ ] Test badge in dark mode
- [ ] Test feature cards in dark mode
- [ ] Test hero section background elements in dark mode

#### 4.2 Background Elements
- [ ] Ensure abstract background blurs work in dark mode
- [ ] Verify gradient overlays adapt to dark mode
- [ ] Test hero image container in dark mode

### Phase 5: Spacing & Layout Refinements

#### 5.1 Consistent Spacing Scale
- [ ] Use consistent spacing scale: `space-y-4 sm:space-y-6 lg:space-y-8`
- [ ] Apply responsive margins throughout
- [ ] Ensure proper gap sizing in grids

#### 5.2 Layout Improvements
- [ ] Optimize feature grid for mobile-first approach
- [ ] Ensure proper content max-widths
- [ ] Improve button group layouts on mobile

## Testing Checklist

### Mobile Testing (375px width)
- [ ] Hero section displays correctly without excessive padding
- [ ] Hero heading is readable and appropriately sized
- [ ] Feature cards stack vertically and are readable
- [ ] CTA section is properly sized
- [ ] All buttons are easily tappable
- [ ] Text is readable without zooming
- [ ] No horizontal scrolling

### Desktop Testing (1920px width)
- [ ] Hero section has appropriate spacing
- [ ] Feature cards display in grid layout
- [ ] All sections are properly spaced
- [ ] Typography is appropriately sized

### Light Mode Testing
- [ ] All colors display correctly
- [ ] Text has proper contrast
- [ ] Backgrounds are appropriate
- [ ] Cards are visible and readable

### Dark Mode Testing
- [ ] All colors adapt correctly
- [ ] Text has proper contrast in dark mode
- [ ] Backgrounds are appropriate for dark mode
- [ ] Cards are visible and readable in dark mode
- [ ] CTA section background adapts properly

## Files to Modify

1. `frontend/src/pages/HomePage.tsx` - Main homepage component

## Design System References

- **Card Component**: `frontend/src/components/ui/Card.tsx`
- **Design Tokens**: `frontend/src/styles/globals.css`
- **Settings Page**: Reference for responsive patterns (`frontend/src/pages/SettingsPage.tsx`)
- **Affiliate Page**: Reference for similar landing page patterns (`frontend/src/pages/AffiliatePage.tsx`)

## Success Criteria

1. ✅ Homepage is fully responsive on mobile (375px) and desktop (1920px)
2. ✅ All colors use HSL design tokens for proper theme support
3. ✅ Typography scales appropriately across breakpoints
4. ✅ Spacing is optimized for mobile while maintaining desktop aesthetics
5. ✅ Dark mode displays correctly with proper contrast
6. ✅ Design matches the rest of the app's design system
7. ✅ No horizontal scrolling on any device
8. ✅ All interactive elements are easily accessible

## Estimated Impact

- **Mobile Space Efficiency**: ~50% improvement in vertical space usage
- **Theme Consistency**: 100% HSL token usage
- **Mobile UX**: Significantly improved readability and usability
- **Design System Alignment**: Full consistency with rest of app

