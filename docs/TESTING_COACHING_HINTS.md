# Testing Guide: Real-Time AI Coaching Hints

## Overview
This document outlines testing procedures for the Real-Time AI Coaching Hints feature (Epic 4, Phase 3).

## Feature Description
Dynamic, contextual AI-generated hints that appear in the CoachOverlay during interview recording. Hints are generated based on:
- Current question text
- Question type (behavioral, technical, system_design)
- Live transcript from speech recognition

## Test Scenarios

### 1. Behavioral Questions

**Setup:**
- Start interview with behavioral question
- Enable coach overlay
- Begin recording

**Test Cases:**
- [ ] Hint appears after 2 seconds of silence
- [ ] Hint appears after 50+ new words
- [ ] Hint focuses on STAR framework
- [ ] Hint mentions quantifying results
- [ ] Hint emphasizes personal contribution
- [ ] Streaming indicator shows while hint is being generated
- [ ] Hint updates as transcript changes

**Expected Behavior:**
- Hints should be contextual to the answer being given
- Should reference STAR method when appropriate
- Should suggest adding metrics/numbers

### 2. Technical Questions

**Setup:**
- Start interview with technical question
- Enable coach overlay
- Begin recording

**Test Cases:**
- [ ] Hint appears after 2 seconds of silence
- [ ] Hint appears after 50+ new words
- [ ] Hint focuses on problem clarification
- [ ] Hint suggests explaining approach
- [ ] Hint mentions edge cases
- [ ] Streaming works smoothly
- [ ] Hint updates based on transcript

**Expected Behavior:**
- Hints should guide problem-solving approach
- Should encourage thinking aloud
- Should suggest considering edge cases

### 3. System Design Questions

**Setup:**
- Start interview with system design question
- Enable coach overlay
- Begin recording

**Test Cases:**
- [ ] Hint appears after 2 seconds of silence
- [ ] Hint appears after 50+ new words
- [ ] Hint focuses on requirements
- [ ] Hint mentions scalability
- [ ] Hint suggests trade-offs discussion
- [ ] Streaming works smoothly
- [ ] Hint updates based on transcript

**Expected Behavior:**
- Hints should guide architectural thinking
- Should encourage starting with requirements
- Should suggest discussing trade-offs

### 4. Streaming Behavior

**Test Cases:**
- [ ] Hint text appears incrementally (streaming)
- [ ] "Live" indicator shows while streaming
- [ ] Typing cursor appears during streaming
- [ ] Streaming stops when hint is complete
- [ ] No flickering or jumping during updates
- [ ] Smooth transition from loading to streaming to complete

**Expected Behavior:**
- Text should stream in smoothly
- Visual indicators should be clear but not distracting
- No performance issues during streaming

### 5. Error Handling

**Test Cases:**
- [ ] Falls back to static hints if API unavailable
- [ ] Shows error message if rate limit exceeded
- [ ] Handles network errors gracefully
- [ ] Continues working after temporary errors
- [ ] No crashes on API failures

**Expected Behavior:**
- Should always show some hint (static fallback)
- Error messages should be user-friendly
- Should recover automatically when possible

### 6. Rate Limiting

**Test Cases:**
- [ ] Maximum 5 hints per minute enforced
- [ ] Rate limit message appears when exceeded
- [ ] Hints resume after cooldown period
- [ ] Rate limit is per-user (not global)

**Expected Behavior:**
- Should prevent excessive API calls
- Should inform user when rate limited
- Should resume automatically after window

### 7. Debouncing

**Test Cases:**
- [ ] Hint doesn't generate on every word
- [ ] Waits 2 seconds of silence before generating
- [ ] Generates immediately after 50+ new words
- [ ] Cancels pending requests when transcript changes
- [ ] Doesn't generate duplicate hints for same transcript

**Expected Behavior:**
- Should balance responsiveness with efficiency
- Should avoid excessive API calls
- Should cancel outdated requests

### 8. UI/UX

**Test Cases:**
- [ ] Coach overlay shows dynamic hints when available
- [ ] Loading state shows while generating
- [ ] Streaming state shows while streaming
- [ ] Error state shows fallback hints
- [ ] Static hints show when no dynamic hint available
- [ ] All states are visually distinct
- [ ] No layout shifts during state changes

**Expected Behavior:**
- Clear visual feedback for all states
- Smooth transitions between states
- Professional appearance

### 9. Performance

**Test Cases:**
- [ ] Hint generation doesn't block UI
- [ ] No lag in transcript updates
- [ ] Streaming doesn't cause performance issues
- [ ] Memory usage remains stable
- [ ] No memory leaks from streaming connections

**Expected Behavior:**
- Should feel responsive and smooth
- Should not impact recording performance
- Should clean up resources properly

### 10. Cross-Browser Testing

**Test Cases:**
- [ ] Works in Chrome
- [ ] Works in Firefox
- [ ] Works in Safari
- [ ] Works in Edge
- [ ] Speech recognition works in all browsers
- [ ] Streaming works in all browsers

**Expected Behavior:**
- Should work in all modern browsers
- Should handle browser-specific differences gracefully

## Manual Testing Checklist

### Quick Smoke Test (5 minutes)
1. Start interview with behavioral question
2. Begin recording
3. Speak for 10 seconds
4. Verify hint appears
5. Verify streaming works
6. Verify hint is relevant

### Full Test (30 minutes)
- [ ] Test all 3 question types
- [ ] Test all error scenarios
- [ ] Test rate limiting
- [ ] Test debouncing behavior
- [ ] Test UI states
- [ ] Test performance
- [ ] Test in multiple browsers

## Automated Testing (Future)

### Unit Tests Needed
- [ ] `useCoachingHint` hook tests
- [ ] Debouncing logic tests
- [ ] Streaming parser tests
- [ ] Error handling tests

### Integration Tests Needed
- [ ] End-to-end hint generation flow
- [ ] Rate limiting enforcement
- [ ] Error fallback behavior

### E2E Tests Needed
- [ ] Complete interview flow with hints
- [ ] Multiple question types
- [ ] Error scenarios

## Known Issues

None currently.

## Test Results

**Date**: [To be filled]
**Tester**: [To be filled]
**Environment**: [To be filled]

### Results Summary
- [ ] All behavioral tests pass
- [ ] All technical tests pass
- [ ] All system design tests pass
- [ ] Streaming works correctly
- [ ] Error handling works correctly
- [ ] Rate limiting works correctly
- [ ] UI/UX is acceptable
- [ ] Performance is acceptable
- [ ] Cross-browser compatibility verified

### Issues Found
[List any issues found during testing]

### Recommendations
[List any recommendations for improvements]
