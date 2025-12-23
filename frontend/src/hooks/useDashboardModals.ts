import { useState, useEffect, useCallback } from 'react';
import { useOnboarding } from './useOnboarding';

interface UseDashboardModalsOptions {
  sessionsCount: number;
  isDataLoaded: boolean;
  userSubscriptionTier?: string;
}

interface DashboardModalsState {
  // Modal open states
  isNewInterviewOpen: boolean;
  isUpgradeOpen: boolean;
  isWelcomeOpen: boolean;
  isFirstSessionPromptOpen: boolean;

  // Actions
  openNewInterview: () => void;
  closeNewInterview: () => void;
  openUpgrade: () => void;
  closeUpgrade: () => void;
  closeWelcome: () => void;
  completeWelcome: () => void;
  createFirstSession: () => void;
  skipFirstSession: () => void;
}

/**
 * Centralized modal state management for DashboardPage.
 * Handles modal priorities and onboarding flow logic.
 */
export function useDashboardModals({
  sessionsCount,
  isDataLoaded,
  userSubscriptionTier,
}: UseDashboardModalsOptions): DashboardModalsState {
  const {
    shouldShowWelcome,
    markWelcomeSeen,
    shouldShowFirstSessionPrompt,
    markFirstSessionCreated,
  } = useOnboarding();

  // Modal states
  const [isNewInterviewOpen, setIsNewInterviewOpen] = useState(false);
  const [isUpgradeOpen, setIsUpgradeOpen] = useState(false);
  const [isWelcomeOpen, setIsWelcomeOpen] = useState(false);
  const [isFirstSessionPromptOpen, setIsFirstSessionPromptOpen] = useState(false);

  // Check for pending plan upgrade from registration
  useEffect(() => {
    const pendingPlan = sessionStorage.getItem('pending_plan');
    if (!pendingPlan) return;

    sessionStorage.removeItem('pending_plan');

    if (pendingPlan === 'pro' && userSubscriptionTier === 'free') {
      setIsUpgradeOpen(true);
    }
  }, [userSubscriptionTier]);

  // Show welcome modal for new users (priority: after upgrade modal)
  useEffect(() => {
    if (isDataLoaded && !isUpgradeOpen && shouldShowWelcome && sessionsCount === 0) {
      setIsWelcomeOpen(true);
    }
  }, [isDataLoaded, shouldShowWelcome, sessionsCount, isUpgradeOpen]);

  // Show first session prompt after welcome is seen
  useEffect(() => {
    if (isDataLoaded && !isUpgradeOpen && shouldShowFirstSessionPrompt && sessionsCount === 0) {
      setIsFirstSessionPromptOpen(true);
    }
  }, [isDataLoaded, shouldShowFirstSessionPrompt, sessionsCount, isUpgradeOpen]);

  // Actions
  const openNewInterview = useCallback(() => {
    setIsNewInterviewOpen(true);
  }, []);

  const closeNewInterview = useCallback(() => {
    setIsNewInterviewOpen(false);
  }, []);

  const openUpgrade = useCallback(() => {
    setIsUpgradeOpen(true);
  }, []);

  const closeUpgrade = useCallback(() => {
    setIsUpgradeOpen(false);
  }, []);

  const closeWelcome = useCallback(() => {
    markWelcomeSeen();
    setIsWelcomeOpen(false);
  }, [markWelcomeSeen]);

  const completeWelcome = useCallback(() => {
    markWelcomeSeen();
    setIsWelcomeOpen(false);
    // Show first session prompt after welcome
    setIsFirstSessionPromptOpen(true);
  }, [markWelcomeSeen]);

  const createFirstSession = useCallback(() => {
    markFirstSessionCreated();
    setIsFirstSessionPromptOpen(false);
    setIsNewInterviewOpen(true);
  }, [markFirstSessionCreated]);

  const skipFirstSession = useCallback(() => {
    markFirstSessionCreated();
    setIsFirstSessionPromptOpen(false);
  }, [markFirstSessionCreated]);

  return {
    isNewInterviewOpen,
    isUpgradeOpen,
    isWelcomeOpen,
    isFirstSessionPromptOpen,
    openNewInterview,
    closeNewInterview,
    openUpgrade,
    closeUpgrade,
    closeWelcome,
    completeWelcome,
    createFirstSession,
    skipFirstSession,
  };
}
