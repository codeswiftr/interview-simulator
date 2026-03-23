import { useEffect, useRef, useCallback } from 'react';

interface UseFocusTrapOptions {
  /** Whether the focus trap is active */
  isActive: boolean;
  /** Callback when escape is pressed */
  onEscape?: () => void;
  /** Initial element to focus (selector or element) */
  initialFocus?: string | HTMLElement | null;
  /** Whether to return focus on deactivation */
  returnFocus?: boolean;
}

/**
 * Custom hook for trapping focus within a container.
 * Used for modals, dialogs, and other overlay components.
 *
 * @example
 * ```tsx
 * function Modal({ isOpen, onClose }) {
 *   const containerRef = useFocusTrap({
 *     isActive: isOpen,
 *     onEscape: onClose,
 *   });
 *
 *   return <div ref={containerRef}>...</div>;
 * }
 * ```
 */
export function useFocusTrap({
  isActive,
  onEscape,
  initialFocus,
  returnFocus = true,
}: UseFocusTrapOptions) {
  const containerRef = useRef<HTMLDivElement>(null);
  const previousActiveElement = useRef<HTMLElement | null>(null);

  // Get all focusable elements within container
  const getFocusableElements = useCallback(() => {
    if (!containerRef.current) return [];

    const selector = [
      'button:not([disabled])',
      '[href]',
      'input:not([disabled])',
      'select:not([disabled])',
      'textarea:not([disabled])',
      '[tabindex]:not([tabindex="-1"])',
    ].join(', ');

    return Array.from(
      containerRef.current.querySelectorAll<HTMLElement>(selector)
    ).filter((el) => {
      // Additional check for visibility
      return el.offsetParent !== null;
    });
  }, []);

  // Handle focus trap
  useEffect(() => {
    if (!isActive || !containerRef.current) return;

    // Save current focus
    previousActiveElement.current = document.activeElement as HTMLElement;

    // Determine initial focus target
    const focusableElements = getFocusableElements();
    let elementToFocus: HTMLElement | null = null;

    if (initialFocus) {
      if (typeof initialFocus === 'string') {
        elementToFocus = containerRef.current.querySelector(initialFocus);
      } else {
        elementToFocus = initialFocus;
      }
    }

    // Fall back to first focusable or container itself
    if (!elementToFocus) {
      elementToFocus = focusableElements[0] || containerRef.current;
    }

    // Small delay to ensure DOM is ready
    requestAnimationFrame(() => {
      elementToFocus?.focus();
    });

    // Handle tab key for focus trap
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && onEscape) {
        event.preventDefault();
        onEscape();
        return;
      }

      if (event.key !== 'Tab') return;

      const focusable = getFocusableElements();
      if (focusable.length === 0) return;

      const firstElement = focusable[0];
      const lastElement = focusable[focusable.length - 1];

      if (event.shiftKey) {
        // Shift + Tab: go to last if on first
        if (document.activeElement === firstElement) {
          event.preventDefault();
          lastElement.focus();
        }
      } else {
        // Tab: go to first if on last
        if (document.activeElement === lastElement) {
          event.preventDefault();
          firstElement.focus();
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);

    // Prevent body scroll
    const originalOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = originalOverflow;

      // Restore focus
      if (returnFocus && previousActiveElement.current) {
        previousActiveElement.current.focus();
      }
    };
  }, [isActive, onEscape, getFocusableElements, initialFocus, returnFocus]);

  return containerRef;
}
