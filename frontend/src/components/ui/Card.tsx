import * as React from 'react';
import { cn } from '../../lib/utils';

/**
 * Card variants matching legacy CSS classes
 */
export type CardVariant = 'default' | 'glass' | 'interactive' | 'elevated' | 'outline';

const variantClasses: Record<CardVariant, string> = {
  default: 'bg-[hsl(var(--card))] border border-[hsl(var(--border))] shadow-sm hover:shadow-md',
  glass: 'card-glass',
  interactive: 'card-interactive',
  elevated: 'bg-[hsl(var(--card))] border border-[hsl(var(--border))] shadow-md hover:shadow-lg',
  outline: 'bg-transparent border border-[hsl(var(--border))]',
};

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: CardVariant;
  /** Enable entrance animation with optional stagger index (1-8) */
  animate?: boolean | number;
}

const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, variant = 'default', animate, ...props }, ref) => {
    // Determine animation classes
    const animationClasses = animate
      ? typeof animate === 'number'
        ? `animate-stagger-in stagger-${Math.min(Math.max(animate, 1), 8)}`
        : 'animate-stagger-in'
      : '';

    return (
      <div
        ref={ref}
        className={cn(
          'rounded-xl transition-all duration-300',
          variantClasses[variant],
          animationClasses,
          className
        )}
        style={animate ? { animationFillMode: 'forwards' } : undefined}
        {...props}
      />
    );
  }
);
Card.displayName = 'Card';

const CardHeader = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn('flex flex-col space-y-1.5 p-6', className)}
    {...props}
  />
));
CardHeader.displayName = 'CardHeader';

const CardTitle = React.forwardRef<
  HTMLHeadingElement,
  React.HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => (
  <h3
    ref={ref}
    className={cn(
      'font-semibold leading-none tracking-tight text-lg text-text-primary',
      className
    )}
    {...props}
  />
));
CardTitle.displayName = 'CardTitle';

const CardDescription = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
  <p
    ref={ref}
    className={cn('text-sm text-text-secondary', className)}
    {...props}
  />
));
CardDescription.displayName = 'CardDescription';

const CardContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div ref={ref} className={cn('p-6 pt-0', className)} {...props} />
));
CardContent.displayName = 'CardContent';

const CardFooter = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn('flex items-center p-6 pt-0', className)}
    {...props}
  />
));
CardFooter.displayName = 'CardFooter';

export {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
};
