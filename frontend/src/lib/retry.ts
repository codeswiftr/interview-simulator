/**
 * Retry utilities for resilient API calls.
 *
 * Provides exponential backoff and configurable retry behavior
 * for handling transient failures gracefully.
 */

export interface RetryConfig {
  /** Maximum number of retry attempts (default: 3) */
  maxRetries?: number;
  /** Base delay in milliseconds (default: 1000) */
  baseDelay?: number;
  /** Maximum delay in milliseconds (default: 10000) */
  maxDelay?: number;
  /** Jitter factor (0-1) to add randomness (default: 0.1) */
  jitter?: number;
  /** Function to determine if error is retryable */
  shouldRetry?: (error: unknown) => boolean;
  /** Callback on each retry attempt */
  onRetry?: (attempt: number, error: unknown, delay: number) => void;
}

const DEFAULT_CONFIG: Required<RetryConfig> = {
  maxRetries: 3,
  baseDelay: 1000,
  maxDelay: 10000,
  jitter: 0.1,
  shouldRetry: isRetryableError,
  onRetry: () => {},
};

/**
 * Determine if an error is retryable (transient).
 * Retries network errors and 5xx server errors.
 * Does NOT retry 4xx client errors (except 429 rate limit).
 */
export function isRetryableError(error: unknown): boolean {
  // Network errors (no response)
  if (error instanceof Error) {
    const message = error.message.toLowerCase();
    if (message.includes('network') ||
        message.includes('timeout') ||
        message.includes('econnrefused') ||
        message.includes('econnreset')) {
      return true;
    }
  }

  // Axios-style error with response
  const axiosError = error as { response?: { status?: number } };
  if (axiosError.response?.status) {
    const status = axiosError.response.status;
    // Retry 5xx server errors and 429 rate limit
    return status >= 500 || status === 429;
  }

  // No response = network error, retry
  if (axiosError.response === undefined) {
    return true;
  }

  return false;
}

/**
 * Calculate exponential backoff delay with jitter.
 */
export function exponentialBackoff(
  attempt: number,
  baseDelay: number,
  maxDelay: number,
  jitter: number
): number {
  // Exponential: baseDelay * 2^attempt
  const exponentialDelay = baseDelay * Math.pow(2, attempt);

  // Cap at maxDelay
  const cappedDelay = Math.min(exponentialDelay, maxDelay);

  // Add jitter (randomness) to prevent thundering herd
  const jitterAmount = cappedDelay * jitter * Math.random();

  return Math.floor(cappedDelay + jitterAmount);
}

/**
 * Execute an async function with retry logic.
 *
 * @example
 * ```ts
 * const result = await withRetry(
 *   () => api.get('/data'),
 *   { maxRetries: 3 }
 * );
 * ```
 */
export async function withRetry<T>(
  fn: () => Promise<T>,
  config: RetryConfig = {}
): Promise<T> {
  const opts = { ...DEFAULT_CONFIG, ...config };

  let lastError: unknown;

  for (let attempt = 0; attempt <= opts.maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;

      // Check if we should retry
      if (attempt >= opts.maxRetries || !opts.shouldRetry(error)) {
        throw error;
      }

      // Calculate delay
      const delay = exponentialBackoff(
        attempt,
        opts.baseDelay,
        opts.maxDelay,
        opts.jitter
      );

      // Notify callback
      opts.onRetry(attempt + 1, error, delay);

      // Wait before retrying
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }

  // Should never reach here, but TypeScript needs this
  throw lastError;
}

/**
 * Add timeout to a promise.
 *
 * @example
 * ```ts
 * const result = await withTimeout(
 *   api.get('/data'),
 *   5000,
 *   'Request timed out'
 * );
 * ```
 */
export async function withTimeout<T>(
  promise: Promise<T>,
  timeoutMs: number,
  message = 'Operation timed out'
): Promise<T> {
  let timeoutId: ReturnType<typeof setTimeout>;

  const timeoutPromise = new Promise<never>((_, reject) => {
    timeoutId = setTimeout(() => {
      reject(new Error(message));
    }, timeoutMs);
  });

  try {
    return await Promise.race([promise, timeoutPromise]);
  } finally {
    clearTimeout(timeoutId!);
  }
}

/**
 * Retry configuration presets for common use cases.
 */
export const RetryPresets = {
  /** Quick retry for fast operations */
  quick: {
    maxRetries: 2,
    baseDelay: 500,
    maxDelay: 2000,
  } as RetryConfig,

  /** Standard retry for API calls */
  standard: {
    maxRetries: 3,
    baseDelay: 1000,
    maxDelay: 10000,
  } as RetryConfig,

  /** Aggressive retry for critical operations */
  aggressive: {
    maxRetries: 5,
    baseDelay: 500,
    maxDelay: 30000,
  } as RetryConfig,

  /** No retry - just timeout */
  none: {
    maxRetries: 0,
  } as RetryConfig,
};
