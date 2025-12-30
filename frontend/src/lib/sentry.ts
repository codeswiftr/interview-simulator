import * as Sentry from '@sentry/react';

/**
 * Initialize Sentry for error tracking and performance monitoring
 * Only initializes if VITE_SENTRY_DSN is set in environment
 */
export function initSentry(): void {
  const dsn = import.meta.env.VITE_SENTRY_DSN;

  // Skip initialization if no DSN is configured
  if (!dsn) {
    console.info('[Sentry] DSN not configured, skipping initialization');
    return;
  }

  Sentry.init({
    dsn,
    environment: import.meta.env.MODE,
    integrations: [
      Sentry.browserTracingIntegration(),
      Sentry.replayIntegration({
        maskAllText: true,
        blockAllMedia: true,
      }),
    ],
    // Performance monitoring: 10% of transactions in production
    tracesSampleRate: import.meta.env.MODE === 'production' ? 0.1 : 1.0,
    // Session replay: 10% of sessions in production
    replaysSessionSampleRate: import.meta.env.MODE === 'production' ? 0.1 : 0,
    // Capture 100% of sessions with errors
    replaysOnErrorSampleRate: 1.0,

    // Don't send errors in development (console is enough)
    beforeSend(event) {
      if (import.meta.env.DEV) {
        console.warn('[Sentry] Would send error:', event);
        return null;
      }
      return event;
    },

    // Ignore common/expected errors
    ignoreErrors: [
      // Browser extensions
      'top.GLOBALS',
      // Network errors (handled by UI)
      'NetworkError',
      'Network request failed',
      // ResizeObserver loop errors (harmless)
      'ResizeObserver loop limit exceeded',
      'ResizeObserver loop completed with undelivered notifications',
    ],
  });

  console.info('[Sentry] Initialized in', import.meta.env.MODE, 'mode');
}

/**
 * Capture an error to Sentry
 * Wrapper around Sentry.captureException for consistent error handling
 */
export function captureError(error: Error | unknown, context?: Record<string, unknown>): void {
  // Always log to console first
  console.error('[Error]', error, context);

  // If Sentry is initialized, send the error
  if (Sentry.isInitialized()) {
    if (context) {
      Sentry.setContext('custom', context);
    }
    Sentry.captureException(error);
  }
}

/**
 * Set user context for Sentry
 * Call this when a user logs in to associate errors with specific users
 */
export function setUserContext(user: { id: number; email: string; tier?: string }): void {
  if (!Sentry.isInitialized()) {
    return;
  }

  Sentry.setUser({
    id: String(user.id),
    email: user.email,
    tier: user.tier || 'free',
  });
}

/**
 * Clear user context from Sentry
 * Call this when a user logs out
 */
export function clearUserContext(): void {
  if (!Sentry.isInitialized()) {
    return;
  }

  Sentry.setUser(null);
}

/**
 * Add breadcrumb for debugging context
 * Useful for tracking user actions leading up to an error
 */
export function addBreadcrumb(message: string, data?: Record<string, unknown>): void {
  if (!Sentry.isInitialized()) {
    return;
  }

  Sentry.addBreadcrumb({
    message,
    data,
    timestamp: Date.now() / 1000,
  });
}
