import posthog from 'posthog-js';

const POSTHOG_KEY = import.meta.env.VITE_POSTHOG_KEY;
const POSTHOG_HOST = import.meta.env.VITE_POSTHOG_HOST || 'https://app.posthog.com';

// Event names following {noun}_{action} convention
export const Events = {
  // Auth events
  USER_REGISTERED: 'user_registered',
  USER_LOGGED_IN: 'user_logged_in',
  USER_LOGGED_OUT: 'user_logged_out',

  // Page events
  PAGE_VIEWED: 'page_viewed',

  // Upgrade / billing funnel events
  UPGRADE_MODAL_OPENED: 'upgrade_modal_opened',
  UPGRADE_CTA_CLICKED: 'upgrade_cta_clicked',
  CHECKOUT_STARTED: 'checkout_started',
  UPGRADE_REASON_SUBMITTED: 'upgrade_reason_submitted',

  // Interview lifecycle events
  INTERVIEW_CREATED: 'interview_created',
  INTERVIEW_STARTED: 'interview_started',
  INTERVIEW_COMPLETED: 'interview_completed',
  INTERVIEW_ABANDONED: 'interview_abandoned',

  // Question/recording events
  QUESTION_VIEWED: 'question_viewed',
  RECORDING_STARTED: 'recording_started',
  RECORDING_COMPLETED: 'recording_completed',

  // Feedback events
  FEEDBACK_GENERATED: 'feedback_generated',
  FEEDBACK_VIEWED: 'feedback_viewed',

  // Feature usage events
  SAMPLE_ANSWER_VIEWED: 'sample_answer_viewed',
  COACHING_HINT_USED: 'coaching_hint_used',

  // Payment events
  SUBSCRIPTION_CREATED: 'subscription_created',
} as const;

export type EventName = (typeof Events)[keyof typeof Events];

interface UserProperties {
  email?: string;
  tier?: string;
  [key: string]: unknown;
}

interface EventProperties {
  [key: string]: unknown;
}

// Check if analytics is enabled and PostHog is available
const isEnabled = (): boolean => {
  return !!POSTHOG_KEY && typeof window !== 'undefined';
};

export const analytics = {
  /**
   * Initialize PostHog analytics.
   * Call this once at app startup.
   */
  init(): void {
    if (!isEnabled()) {
      console.debug('[Analytics] PostHog disabled: VITE_POSTHOG_KEY not set');
      return;
    }

    try {
      posthog.init(POSTHOG_KEY!, {
        api_host: POSTHOG_HOST,
        capture_pageview: false, // We manually track page views
        capture_pageleave: true,
        persistence: 'localStorage',
        autocapture: false, // We explicitly capture events
        // Disable session recording by default (can enable in PostHog dashboard)
        disable_session_recording: true,
      });
      console.debug('[Analytics] PostHog initialized');
    } catch (error) {
      console.error('[Analytics] Failed to initialize PostHog:', error);
    }
  },

  /**
   * Identify a user after login/signup.
   * Uses forge_{userId} format for cross-product tracking.
   */
  identify(userId: string, properties: UserProperties = {}): void {
    if (!isEnabled()) return;

    try {
      posthog.identify(`forge_${userId}`, {
        ...properties,
        product: 'interview-simulator',
        domain: 'codeswiftr.com',
      });
    } catch (error) {
      console.error('[Analytics] Failed to identify user:', error);
    }
  },

  /**
   * Track a custom event.
   */
  track(event: EventName | string, properties: EventProperties = {}): void {
    if (!isEnabled()) return;

    try {
      posthog.capture(event, {
        ...properties,
        product: 'interview-simulator',
        domain: 'codeswiftr.com',
      });
    } catch (error) {
      console.error('[Analytics] Failed to track event:', error);
    }
  },

  /**
   * Track a page view.
   */
  pageView(path: string, title?: string): void {
    if (!isEnabled()) return;

    try {
      posthog.capture(Events.PAGE_VIEWED, {
        path,
        title: title || document.title,
        referrer: document.referrer,
        product: 'interview-simulator',
        domain: 'codeswiftr.com',
      });
    } catch (error) {
      console.error('[Analytics] Failed to track page view:', error);
    }
  },

  /**
   * Reset analytics state on logout.
   */
  reset(): void {
    if (!isEnabled()) return;

    try {
      posthog.reset();
    } catch (error) {
      console.error('[Analytics] Failed to reset:', error);
    }
  },

  /**
   * Check if user has opted out of tracking.
   */
  hasOptedOut(): boolean {
    if (!isEnabled()) return true;
    return posthog.has_opted_out_capturing?.() ?? false;
  },

  /**
   * Opt user out of tracking (GDPR compliance).
   */
  optOut(): void {
    if (!isEnabled()) return;
    posthog.opt_out_capturing?.();
  },

  /**
   * Opt user back into tracking.
   */
  optIn(): void {
    if (!isEnabled()) return;
    posthog.opt_in_capturing?.();
  },
};

export default analytics;
