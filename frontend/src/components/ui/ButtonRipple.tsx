import { useState, type ReactNode, type MouseEvent } from 'react';
import { useRipple, type RippleProps } from '../../hooks/useRipple';

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
