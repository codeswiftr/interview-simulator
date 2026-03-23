import posthog from 'posthog-js';

const POSTHOG_KEY = import.meta.env.VITE_POSTHOG_KEY;
// Use reverse proxy to bypass ad blockers - proxy at api.codeswiftr.com/ph forwards to PostHog EU
const POSTHOG_HOST = import.meta.env.VITE_POSTHOG_HOST || 'https://api.codeswiftr.com/ph';

// Event names following {prefix}_{entity}_{action} convention (PostHog standard)
export const Events = {
  // Auth events
  USER_REGISTERED: 'is_user_registered',
  USER_LOGGED_IN: 'is_user_logged_in',
  USER_LOGGED_OUT: 'is_user_logged_out',

  // Page events
  PAGE_VIEWED: 'is_page_viewed',

  // Upgrade / billing funnel events
  UPGRADE_MODAL_OPENED: 'is_upgrade_modal_opened',
  UPGRADE_MODAL_CLOSED: 'is_upgrade_modal_closed',
  UPGRADE_CTA_CLICKED: 'is_upgrade_cta_clicked',
  CHECKOUT_STARTED: 'is_checkout_started',
  UPGRADE_REASON_SUBMITTED: 'is_upgrade_reason_submitted',
  LIMIT_REACHED: 'is_limit_reached',

  // Interview lifecycle events
  INTERVIEW_CREATED: 'is_interview_created',
  INTERVIEW_STARTED: 'is_interview_started',
  INTERVIEW_COMPLETED: 'is_interview_completed',
  INTERVIEW_ABANDONED: 'is_interview_abandoned',

  // Question/recording events
  QUESTION_VIEWED: 'is_question_viewed',
  QUESTION_SKIPPED: 'is_question_skipped',
  RECORDING_STARTED: 'is_recording_started',
  RECORDING_COMPLETED: 'is_recording_completed',

  // Feedback events
  FEEDBACK_GENERATED: 'is_feedback_generated',
  FEEDBACK_VIEWED: 'is_feedback_viewed',

  // Feature usage events
  SAMPLE_ANSWER_VIEWED: 'is_sample_answer_viewed',
  COACHING_HINT_USED: 'is_coaching_hint_used',

  // Payment events
  SUBSCRIPTION_CREATED: 'is_subscription_created',

  // Settings events
  THEME_CHANGED: 'is_theme_changed',
  VOICE_SETTINGS_CHANGED: 'is_voice_settings_changed',

  // Question bank events
  QUESTION_FILTER_APPLIED: 'is_question_filter_applied',
  QUESTION_PRACTICE_STARTED: 'is_question_practice_started',

  // Error events
  UPLOAD_FAILED: 'is_upload_failed',
  API_ERROR: 'is_api_error',
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
        // UI host for EU region (used for opt-out, surveys, etc.)
        ui_host: 'https://eu.posthog.com',
        capture_pageview: false, // We manually track page views
        capture_pageleave: true,
        persistence: 'localStorage',
        autocapture: false, // We explicitly capture events
        // Disable session recording by default (can enable in PostHog dashboard)
        disable_session_recording: true,
      });
      console.debug('[Analytics] PostHog initialized with reverse proxy');
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
