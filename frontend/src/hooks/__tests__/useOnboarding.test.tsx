import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useOnboarding } from '../useOnboarding';

const ONBOARDING_KEY = 'interview_simulator_onboarding';

describe('useOnboarding', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    localStorage.clear();
  });

  describe('initialization', () => {
    it('should initialize with default state when no saved state exists', () => {
      const { result } = renderHook(() => useOnboarding());

      expect(result.current.state).toEqual({
        hasSeenWelcome: false,
        completedSteps: [],
        firstSessionCreated: false,
        preparationTourCompleted: false,
      });
      expect(result.current.shouldShowWelcome).toBe(true);
    });

    it('should load saved state from localStorage', () => {
      const savedState = {
        hasSeenWelcome: true,
        completedSteps: ['step1', 'step2'],
        dismissedAt: '2024-01-01T00:00:00.000Z',
      };
      localStorage.setItem(ONBOARDING_KEY, JSON.stringify(savedState));

      const { result } = renderHook(() => useOnboarding());

      expect(result.current.state).toEqual(savedState);
      expect(result.current.shouldShowWelcome).toBe(false);
    });

    it('should handle invalid localStorage data gracefully', () => {
      localStorage.setItem(ONBOARDING_KEY, 'invalid-json');

      const { result } = renderHook(() => useOnboarding());

      expect(result.current.state).toEqual({
        hasSeenWelcome: false,
        completedSteps: [],
        firstSessionCreated: false,
        preparationTourCompleted: false,
      });
    });
  });

  describe('markWelcomeSeen', () => {
    it('should mark welcome as seen', () => {
      const { result } = renderHook(() => useOnboarding());

      expect(result.current.shouldShowWelcome).toBe(true);

      act(() => {
        result.current.markWelcomeSeen();
      });

      expect(result.current.shouldShowWelcome).toBe(false);
      expect(result.current.state.hasSeenWelcome).toBe(true);
      expect(result.current.state.dismissedAt).toBeDefined();
    });

    it('should persist welcome seen state to localStorage', () => {
      const { result } = renderHook(() => useOnboarding());

      act(() => {
        result.current.markWelcomeSeen();
      });

      const saved = localStorage.getItem(ONBOARDING_KEY);
      expect(saved).toBeTruthy();

      const parsed = JSON.parse(saved!);
      expect(parsed.hasSeenWelcome).toBe(true);
      expect(parsed.dismissedAt).toBeDefined();
    });
  });

  describe('completeStep', () => {
    it('should add completed step to the list', () => {
      const { result } = renderHook(() => useOnboarding());

      act(() => {
        result.current.completeStep('first-interview');
      });

      expect(result.current.state.completedSteps).toContain('first-interview');
      expect(result.current.isStepCompleted('first-interview')).toBe(true);
    });

    it('should handle multiple completed steps', () => {
      const { result } = renderHook(() => useOnboarding());

      act(() => {
        result.current.completeStep('step1');
        result.current.completeStep('step2');
        result.current.completeStep('step3');
      });

      expect(result.current.state.completedSteps).toEqual(['step1', 'step2', 'step3']);
    });

    it('should not duplicate steps', () => {
      const { result } = renderHook(() => useOnboarding());

      act(() => {
        result.current.completeStep('duplicate-step');
        result.current.completeStep('duplicate-step');
        result.current.completeStep('duplicate-step');
      });

      expect(result.current.state.completedSteps).toEqual(['duplicate-step']);
    });

    it('should persist completed steps to localStorage', () => {
      const { result } = renderHook(() => useOnboarding());

      act(() => {
        result.current.completeStep('persisted-step');
      });

      const saved = localStorage.getItem(ONBOARDING_KEY);
      const parsed = JSON.parse(saved!);
      expect(parsed.completedSteps).toContain('persisted-step');
    });
  });

  describe('isStepCompleted', () => {
    it('should return false for uncompleted step', () => {
      const { result } = renderHook(() => useOnboarding());

      expect(result.current.isStepCompleted('uncompleted-step')).toBe(false);
    });

    it('should return true for completed step', () => {
      const { result } = renderHook(() => useOnboarding());

      act(() => {
        result.current.completeStep('completed-step');
      });

      expect(result.current.isStepCompleted('completed-step')).toBe(true);
    });

    it('should check multiple steps independently', () => {
      const { result } = renderHook(() => useOnboarding());

      act(() => {
        result.current.completeStep('step1');
        result.current.completeStep('step3');
      });

      expect(result.current.isStepCompleted('step1')).toBe(true);
      expect(result.current.isStepCompleted('step2')).toBe(false);
      expect(result.current.isStepCompleted('step3')).toBe(true);
    });
  });

  describe('resetOnboarding', () => {
    it('should reset state to defaults', () => {
      const { result } = renderHook(() => useOnboarding());

      act(() => {
        result.current.markWelcomeSeen();
        result.current.completeStep('step1');
        result.current.completeStep('step2');
      });

      expect(result.current.state.hasSeenWelcome).toBe(true);
      expect(result.current.state.completedSteps).toHaveLength(2);

      act(() => {
        result.current.resetOnboarding();
      });

      expect(result.current.state).toEqual({
        hasSeenWelcome: false,
        completedSteps: [],
        firstSessionCreated: false,
        preparationTourCompleted: false,
      });
      expect(result.current.shouldShowWelcome).toBe(true);
    });

    it('should clear or reset localStorage to defaults', () => {
      const { result } = renderHook(() => useOnboarding());

      act(() => {
        result.current.markWelcomeSeen();
      });

      expect(localStorage.getItem(ONBOARDING_KEY)).toBeTruthy();

      act(() => {
        result.current.resetOnboarding();
      });

      // After reset, either no item exists or it contains default state
      const saved = localStorage.getItem(ONBOARDING_KEY);
      if (saved) {
        // If item exists, verify it's the default state
        const parsed = JSON.parse(saved);
        expect(parsed.hasSeenWelcome).toBe(false);
        expect(parsed.completedSteps).toEqual([]);
      }
    });
  });

  describe('triggerNewUserOnboarding', () => {
    it('should reset to default state for new users', () => {
      const { result } = renderHook(() => useOnboarding());

      act(() => {
        result.current.markWelcomeSeen();
        result.current.completeStep('old-step');
      });

      act(() => {
        result.current.triggerNewUserOnboarding();
      });

      expect(result.current.state).toEqual({
        hasSeenWelcome: false,
        completedSteps: [],
        firstSessionCreated: false,
        preparationTourCompleted: false,
      });
      expect(result.current.shouldShowWelcome).toBe(true);
    });
  });

  describe('state persistence', () => {
    it('should persist state changes automatically', () => {
      const { result } = renderHook(() => useOnboarding());

      act(() => {
        result.current.markWelcomeSeen();
      });

      const saved1 = localStorage.getItem(ONBOARDING_KEY);
      expect(saved1).toBeTruthy();

      act(() => {
        result.current.completeStep('test-step');
      });

      const saved2 = localStorage.getItem(ONBOARDING_KEY);
      const parsed = JSON.parse(saved2!);
      expect(parsed.hasSeenWelcome).toBe(true);
      expect(parsed.completedSteps).toContain('test-step');
    });

    it('should maintain state across hook instances', () => {
      const { result: result1 } = renderHook(() => useOnboarding());

      act(() => {
        result1.current.markWelcomeSeen();
        result1.current.completeStep('shared-step');
      });

      // Create new hook instance
      const { result: result2 } = renderHook(() => useOnboarding());

      expect(result2.current.state.hasSeenWelcome).toBe(true);
      expect(result2.current.isStepCompleted('shared-step')).toBe(true);
    });
  });

  describe('edge cases', () => {
    it('should handle empty step names', () => {
      const { result } = renderHook(() => useOnboarding());

      act(() => {
        result.current.completeStep('');
      });

      expect(result.current.state.completedSteps).toContain('');
      expect(result.current.isStepCompleted('')).toBe(true);
    });

    it('should handle special characters in step names', () => {
      const { result } = renderHook(() => useOnboarding());

      const specialStep = 'step-with-special_chars.123!@#';

      act(() => {
        result.current.completeStep(specialStep);
      });

      expect(result.current.isStepCompleted(specialStep)).toBe(true);
    });

    it('should preserve step order', () => {
      const { result } = renderHook(() => useOnboarding());

      const steps = ['first', 'second', 'third', 'fourth'];

      act(() => {
        steps.forEach(step => result.current.completeStep(step));
      });

      expect(result.current.state.completedSteps).toEqual(steps);
    });
  });
});
