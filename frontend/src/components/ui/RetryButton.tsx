import { useState, useCallback } from 'react';
import { RefreshCw, Loader2 } from 'lucide-react';
import { cn } from '../../lib/utils';

interface RetryButtonProps {
  /** Function to call when retrying */
  onRetry: () => Promise<void>;
  /** Button label (default: "Retry") */
  label?: string;
  /** Additional CSS classes */
  className?: string;
  /** Button size variant */
  size?: 'sm' | 'md' | 'lg';
  /** Button variant */
  variant?: 'primary' | 'secondary' | 'ghost';
  /** Disable the button */
  disabled?: boolean;
}

/**
 * Button component for retry actions with loading state.
 * Automatically shows loading spinner during retry operation.
 */
export function RetryButton({
  onRetry,
  label = 'Retry',
  className,
  size = 'md',
  variant = 'secondary',
  disabled = false,
}: RetryButtonProps) {
  const [isRetrying, setIsRetrying] = useState(false);

  const handleRetry = useCallback(async () => {
    if (isRetrying) return;

    setIsRetrying(true);
    try {
      await onRetry();
    } finally {
      setIsRetrying(false);
    }
  }, [onRetry, isRetrying]);

  const sizeClasses = {
    sm: 'px-3 py-1.5 text-xs gap-1.5',
    md: 'px-4 py-2 text-sm gap-2',
    lg: 'px-6 py-3 text-base gap-2',
  };

  const variantClasses = {
    primary: 'btn-primary',
    secondary: 'bg-surface-secondary hover:bg-surface-tertiary text-text-primary border border-border-primary',
    ghost: 'text-text-secondary hover:text-text-primary hover:bg-surface-secondary',
  };

  const iconSize = size === 'sm' ? 14 : size === 'lg' ? 18 : 16;

  return (
    <button
      onClick={handleRetry}
      disabled={disabled || isRetrying}
      className={cn(
        'inline-flex items-center justify-center rounded-lg font-medium transition-all',
        'disabled:opacity-50 disabled:cursor-not-allowed',
        sizeClasses[size],
        variantClasses[variant],
        className
      )}
      aria-busy={isRetrying}
    >
      {isRetrying ? (
        <Loader2 size={iconSize} className="animate-spin" aria-hidden="true" />
      ) : (
        <RefreshCw size={iconSize} aria-hidden="true" />
      )}
      <span>{isRetrying ? 'Retrying...' : label}</span>
    </button>
  );
}

interface ErrorRecoveryOptionsProps {
  /** Function to retry the operation */
  onRetry: () => Promise<void>;
  /** Function to refresh the page */
  onRefresh?: () => void;
  /** Function to go home */
  onGoHome?: () => void;
  /** Error message to display */
  errorMessage?: string;
  /** Additional CSS classes */
  className?: string;
}

/**
 * Error recovery component with multiple options.
 * Shows retry, refresh, and home navigation options.
 */
export function ErrorRecoveryOptions({
  onRetry,
  onRefresh,
  onGoHome,
  errorMessage,
  className,
}: ErrorRecoveryOptionsProps) {
  const handleRefresh = () => {
    if (onRefresh) {
      onRefresh();
    } else {
      window.location.reload();
    }
  };

  const handleGoHome = () => {
    if (onGoHome) {
      onGoHome();
    } else {
      window.location.href = '/dashboard';
    }
  };

  return (
    <div className={cn('space-y-4', className)}>
      {errorMessage && (
        <p className="text-sm text-text-secondary">{errorMessage}</p>
      )}

      <div className="flex flex-wrap gap-3">
        <RetryButton onRetry={onRetry} variant="primary" />

        <button
          onClick={handleRefresh}
          className="px-4 py-2 text-sm font-medium text-text-secondary hover:text-text-primary transition-colors"
        >
          Refresh Page
        </button>

        <button
          onClick={handleGoHome}
          className="px-4 py-2 text-sm font-medium text-text-secondary hover:text-text-primary transition-colors"
        >
          Go to Dashboard
        </button>
      </div>
    </div>
  );
}

/**
 * Hook for managing retry state.
 */
// eslint-disable-next-line react-refresh/only-export-components
export function useRetry(retryFn: () => Promise<void>) {
  const [isRetrying, setIsRetrying] = useState(false);
  const [retryCount, setRetryCount] = useState(0);
  const [lastError, setLastError] = useState<Error | null>(null);

  const retry = useCallback(async () => {
    if (isRetrying) return;

    setIsRetrying(true);
    setLastError(null);

    try {
      await retryFn();
      setRetryCount(0); // Reset on success
    } catch (error) {
      setLastError(error instanceof Error ? error : new Error(String(error)));
      setRetryCount((prev) => prev + 1);
      throw error;
    } finally {
      setIsRetrying(false);
    }
  }, [retryFn, isRetrying]);

  const reset = useCallback(() => {
    setRetryCount(0);
    setLastError(null);
  }, []);

  return {
    retry,
    isRetrying,
    retryCount,
    lastError,
    reset,
  };
}
