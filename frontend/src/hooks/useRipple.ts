import { useState, useCallback, type MouseEvent } from 'react';

interface RippleProps {
  x: number;
  y: number;
  size: number;
  id: number;
}

/**
 * Hook for creating ripple effects on button clicks.
 * Returns ripple state and a function to create new ripples.
 */
export function useRipple() {
  const [ripples, setRipples] = useState<RippleProps[]>([]);

  const createRipple = useCallback((event: MouseEvent<HTMLElement>) => {
    const button = event.currentTarget;
    const rect = button.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    const x = event.clientX - rect.left - size / 2;
    const y = event.clientY - rect.top - size / 2;

    const newRipple = { x, y, size, id: Date.now() };
    setRipples((prev) => [...prev, newRipple]);

    // Remove ripple after animation completes
    setTimeout(() => {
      setRipples((prev) => prev.filter((r) => r.id !== newRipple.id));
    }, 600);
  }, []);

  return { ripples, createRipple };
}

export type { RippleProps };
