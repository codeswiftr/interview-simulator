import type { HTMLAttributes } from 'react';
import { cn } from '../../lib/utils';

export type SpinnerSize = 'sm' | 'md' | 'lg';

export interface SpinnerProps extends HTMLAttributes<HTMLDivElement> {
  size?: SpinnerSize;
  label?: string;
}

const sizeStyles: Record<SpinnerSize, string> = {
  sm: 'w-4 h-4 border-2',
  md: 'w-8 h-8 border-2',
  lg: 'w-12 h-12 border-3',
};

export function Spinner({ size = 'md', label, className, ...props }: SpinnerProps) {
  return (
    <div
      role="status"
      aria-label={label || 'Loading'}
      className={cn('inline-flex items-center justify-center', className)}
      {...props}
    >
      <div
        className={cn(
          'animate-spin rounded-full',
          'border-current border-t-transparent',
          sizeStyles[size]
        )}
      />
      {label && (
        <span className="ml-2 text-sm text-text-secondary">{label}</span>
      )}
    </div>
  );
}
