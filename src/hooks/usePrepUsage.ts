import { useCallback, useEffect, useState } from 'react';

const STORAGE_KEY = 'prepUsage';
const FREE_TIER_PREP_LIMIT = 3; // 3 preparations per month

interface PrepUsageData {
  count: number;
  resetDate: string; // ISO date string of next reset
}

function getStartOfNextMonth(): string {
  const now = new Date();
  const nextMonth = new Date(now.getFullYear(), now.getMonth() + 1, 1);
  return nextMonth.toISOString();
}

function loadUsage(): PrepUsageData {
  if (typeof window === 'undefined') {
    return { count: 0, resetDate: getStartOfNextMonth() };
  }

  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return { count: 0, resetDate: getStartOfNextMonth() };
    }

    const data = JSON.parse(raw) as PrepUsageData;

    // Check if reset is needed
    if (new Date(data.resetDate) <= new Date()) {
      return { count: 0, resetDate: getStartOfNextMonth() };
    }

    return data;
  } catch {
    return { count: 0, resetDate: getStartOfNextMonth() };
  }
}

function saveUsage(data: PrepUsageData): void {
  if (typeof window === 'undefined') return;

  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  } catch {
    // Ignore storage failures
  }
}

export interface UsePrepUsageReturn {
  prepCount: number;
  prepLimit: number;
  remaining: number;
  isLimitReached: boolean;
  resetDate: Date;
  incrementUsage: () => void;
}

/**
 * Hook to track preparation usage for free tier users
 *
 * Free tier gets 3 preparations per month, resets on the 1st
 */
export function usePrepUsage(): UsePrepUsageReturn {
  const [usage, setUsage] = useState<PrepUsageData>(() => loadUsage());

  // Check for reset on mount and periodically
  useEffect(() => {
    const checkReset = () => {
      const current = loadUsage();
      if (current.resetDate !== usage.resetDate || current.count !== usage.count) {
        setUsage(current);
      }
    };

    checkReset();

    // Check every minute in case month rolls over
    const interval = setInterval(checkReset, 60000);
    return () => clearInterval(interval);
  }, [usage.count, usage.resetDate]);

  const incrementUsage = useCallback(() => {
    setUsage((prev) => {
      const newData = { ...prev, count: prev.count + 1 };
      saveUsage(newData);
      return newData;
    });
  }, []);

  return {
    prepCount: usage.count,
    prepLimit: FREE_TIER_PREP_LIMIT,
    remaining: Math.max(0, FREE_TIER_PREP_LIMIT - usage.count),
    isLimitReached: usage.count >= FREE_TIER_PREP_LIMIT,
    resetDate: new Date(usage.resetDate),
    incrementUsage,
  };
}
