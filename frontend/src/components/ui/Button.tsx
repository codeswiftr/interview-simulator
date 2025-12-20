import { forwardRef, useState } from 'react';
import type { ButtonHTMLAttributes, ReactNode, MouseEvent } from 'react';
import { cn } from '../../lib/utils';
import { Spinner } from './Spinner';
import { useRipple, Ripples } from './ButtonRipple';

export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger';
export type ButtonSize = 'sm' | 'md' | 'lg';

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
  fullWidth?: boolean;
  children: ReactNode;
}

const variantStyles: Record<ButtonVariant, string> = {
  primary: 'btn-primary',
  secondary: 'btn-secondary',
  ghost: 'btn-ghost',
  danger: 'bg-status-error hover:bg-red-600 text-white shadow-md hover:shadow-lg active:shadow-sm transition-all',
};

const sizeStyles: Record<ButtonSize, string> = {
  sm: 'px-3 py-1.5 text-sm',
  md: 'px-6 py-3',
  lg: 'px-8 py-4 text-lg',
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = 'primary',
      size = 'md',
      loading = false,
      leftIcon,
      rightIcon,
      fullWidth = false,
      disabled,
      className,
      children,
      onClick,
      ...props
    },
    ref
  ) => {
    const isDisabled = disabled || loading;
    const { ripples, createRipple } = useRipple();
    const [isPressed, setIsPressed] = useState(false);

    const handleClick = (e: MouseEvent<HTMLButtonElement>) => {
      if (!isDisabled) {
        createRipple(e);
        setIsPressed(true);
        setTimeout(() => setIsPressed(false), 150);
      }
      onClick?.(e);
    };

    // Determine ripple color based on variant
    const rippleColor = variant === 'primary' || variant === 'danger'
      ? 'rgba(255, 255, 255, 0.3)'
      : 'rgba(56, 189, 248, 0.2)';

    return (
      <button
        ref={ref}
        disabled={isDisabled}
        onClick={handleClick}
        className={cn(
          // Base styles
          'relative overflow-hidden',
          'inline-flex items-center justify-center gap-2',
          'font-semibold rounded-xl',
          'transition-all duration-200',
          'focus:outline-none focus-visible:ring-2 focus-visible:ring-electric-blue focus-visible:ring-offset-2',
          'disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none',

          // Press feedback
          isPressed && !isDisabled && 'scale-[0.97]',

          // Variant styles
          variantStyles[variant],

          // Size styles
          sizeStyles[size],

          // Full width
          fullWidth && 'w-full',

          className
        )}
        {...props}
      >
        <Ripples ripples={ripples} color={rippleColor} />
        {loading && <Spinner size="sm" className="text-current" />}
        {!loading && leftIcon && <span className="inline-flex">{leftIcon}</span>}
        <span>{children}</span>
        {!loading && rightIcon && <span className="inline-flex">{rightIcon}</span>}
      </button>
    );
  }
);

Button.displayName = 'Button';
