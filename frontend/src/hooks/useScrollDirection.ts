import { useState, useEffect, useRef } from 'react';

export type ScrollDirection = 'up' | 'down' | null;

interface UseScrollDirectionOptions {
  /** Minimum scroll amount before triggering direction change (default: 10) */
  threshold?: number;
  /** Initial direction (default: null) */
  initialDirection?: ScrollDirection;
}

/**
 * Hook to detect scroll direction for show/hide UI patterns.
 * Returns 'up' when scrolling up (show header), 'down' when scrolling down (hide header).
 */
export function useScrollDirection(options: UseScrollDirectionOptions = {}): ScrollDirection {
  const { threshold = 10, initialDirection = null } = options;
  const [scrollDirection, setScrollDirection] = useState<ScrollDirection>(initialDirection);
  const lastScrollY = useRef(0);
  const ticking = useRef(false);

  useEffect(() => {
    // Store initial scroll position
    lastScrollY.current = window.scrollY;

    const updateScrollDirection = () => {
      const scrollY = window.scrollY;
      const diff = scrollY - lastScrollY.current;

      // Only update if we've scrolled more than threshold
      if (Math.abs(diff) < threshold) {
        ticking.current = false;
        return;
      }

      // At top of page, always show header
      if (scrollY < threshold) {
        setScrollDirection('up');
      } else {
        setScrollDirection(diff > 0 ? 'down' : 'up');
      }

      lastScrollY.current = scrollY > 0 ? scrollY : 0;
      ticking.current = false;
    };

    const onScroll = () => {
      if (!ticking.current) {
        window.requestAnimationFrame(updateScrollDirection);
        ticking.current = true;
      }
    };

    window.addEventListener('scroll', onScroll, { passive: true });

    return () => {
      window.removeEventListener('scroll', onScroll);
    };
  }, [threshold]);

  return scrollDirection;
}

export default useScrollDirection;
