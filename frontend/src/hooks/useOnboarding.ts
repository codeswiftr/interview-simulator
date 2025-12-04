import { useState, useCallback, useEffect } from 'react';

const ONBOARDING_KEY = 'interview_simulator_onboarding';

interface OnboardingState {
  hasSeenWelcome: boolean;
  completedSteps: string[];
  dismissedAt?: string;
}

const defaultState: OnboardingState = {
  hasSeenWelcome: false,
  completedSteps: [],
};

export function useOnboarding() {
  const [state, setState] = useState<OnboardingState>(() => {
    try {
      const stored = localStorage.getItem(ONBOARDING_KEY);
      if (stored) {
        return JSON.parse(stored);
      }
    } catch {
      // Ignore parse errors
    }
    return defaultState;
  });

  // Persist state changes
  useEffect(() => {
    localStorage.setItem(ONBOARDING_KEY, JSON.stringify(state));
  }, [state]);

  // Check if user should see welcome modal
  const shouldShowWelcome = !state.hasSeenWelcome;

  // Mark welcome as seen
  const markWelcomeSeen = useCallback(() => {
    setState((prev) => ({
      ...prev,
      hasSeenWelcome: true,
      dismissedAt: new Date().toISOString(),
    }));
  }, []);

  // Mark a step as completed
  const completeStep = useCallback((step: string) => {
    setState((prev) => ({
      ...prev,
      completedSteps: prev.completedSteps.includes(step)
        ? prev.completedSteps
        : [...prev.completedSteps, step],
    }));
  }, []);

  // Check if a step is completed
  const isStepCompleted = useCallback(
    (step: string) => state.completedSteps.includes(step),
    [state.completedSteps]
  );

  // Reset onboarding (for testing/debugging)
  const resetOnboarding = useCallback(() => {
    setState(defaultState);
    localStorage.removeItem(ONBOARDING_KEY);
  }, []);

  // Trigger new user onboarding (called after registration)
  const triggerNewUserOnboarding = useCallback(() => {
    setState(defaultState);
  }, []);

  return {
    state,
    shouldShowWelcome,
    markWelcomeSeen,
    completeStep,
    isStepCompleted,
    resetOnboarding,
    triggerNewUserOnboarding,
  };
}
