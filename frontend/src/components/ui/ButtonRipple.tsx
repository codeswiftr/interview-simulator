import { useState, useCallback, type ReactNode, type MouseEvent } from 'react';

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

interface RipplesProps {
  ripples: RippleProps[];
  color?: string;
}

/**
 * Renders ripple effect elements.
 * Should be placed inside a relatively positioned container with overflow-hidden.
 */
export function Ripples({ ripples, color = 'rgba(255, 255, 255, 0.3)' }: RipplesProps) {
  return (
    <>
      {ripples.map((ripple) => (
        <span
          key={ripple.id}
          className="absolute rounded-full pointer-events-none animate-ripple"
          style={{
            left: ripple.x,
            top: ripple.y,
            width: ripple.size,
            height: ripple.size,
            backgroundColor: color,
          }}
        />
      ))}
    </>
  );
}

interface RippleButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
  rippleColor?: string;
}

/**
 * A button component with built-in ripple effect.
 * Use this for primary actions that need tactile feedback.
 */
export function RippleButton({
  children,
  rippleColor = 'rgba(255, 255, 255, 0.3)',
  className = '',
  onClick,
  ...props
}: RippleButtonProps) {
  const { ripples, createRipple } = useRipple();
  const [isPressed, setIsPressed] = useState(false);

  const handleClick = (e: MouseEvent<HTMLButtonElement>) => {
    createRipple(e);
    setIsPressed(true);
    setTimeout(() => setIsPressed(false), 150);
    onClick?.(e);
  };

  return (
    <button
      onClick={handleClick}
      className={`relative overflow-hidden transition-transform ${isPressed ? 'scale-[0.97]' : ''} ${className}`}
      {...props}
    >
      <Ripples ripples={ripples} color={rippleColor} />
      {children}
    </button>
  );
}
