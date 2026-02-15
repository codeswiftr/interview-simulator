import { describe, it, expect, vi, beforeEach } from 'vitest';
import posthog from 'posthog-js';
import { analytics, Events } from '../analytics';

// PostHog is mocked in test/setup.ts - the mock is already set up globally

describe('Analytics Module', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Events Constants', () => {
    it('should define all auth events', () => {
      expect(Events.USER_REGISTERED).toBe('is_user_registered');
      expect(Events.USER_LOGGED_IN).toBe('is_user_logged_in');
      expect(Events.USER_LOGGED_OUT).toBe('is_user_logged_out');
    });

    it('should define all page events', () => {
      expect(Events.PAGE_VIEWED).toBe('is_page_viewed');
    });

    it('should define all upgrade/billing events', () => {
      expect(Events.UPGRADE_MODAL_OPENED).toBe('is_upgrade_modal_opened');
      expect(Events.UPGRADE_MODAL_CLOSED).toBe('is_upgrade_modal_closed');
      expect(Events.UPGRADE_CTA_CLICKED).toBe('is_upgrade_cta_clicked');
      expect(Events.CHECKOUT_STARTED).toBe('is_checkout_started');
      expect(Events.UPGRADE_REASON_SUBMITTED).toBe('is_upgrade_reason_submitted');
      expect(Events.LIMIT_REACHED).toBe('is_limit_reached');
    });

    it('should define all interview lifecycle events', () => {
      expect(Events.INTERVIEW_CREATED).toBe('is_interview_created');
      expect(Events.INTERVIEW_STARTED).toBe('is_interview_started');
      expect(Events.INTERVIEW_COMPLETED).toBe('is_interview_completed');
      expect(Events.INTERVIEW_ABANDONED).toBe('is_interview_abandoned');
    });

    it('should define all question/recording events', () => {
      expect(Events.QUESTION_VIEWED).toBe('is_question_viewed');
      expect(Events.QUESTION_SKIPPED).toBe('is_question_skipped');
      expect(Events.RECORDING_STARTED).toBe('is_recording_started');
      expect(Events.RECORDING_COMPLETED).toBe('is_recording_completed');
    });

    it('should define all feedback events', () => {
      expect(Events.FEEDBACK_GENERATED).toBe('is_feedback_generated');
      expect(Events.FEEDBACK_VIEWED).toBe('is_feedback_viewed');
    });

    it('should define all feature usage events', () => {
      expect(Events.SAMPLE_ANSWER_VIEWED).toBe('is_sample_answer_viewed');
      expect(Events.COACHING_HINT_USED).toBe('is_coaching_hint_used');
    });

    it('should define payment events', () => {
      expect(Events.SUBSCRIPTION_CREATED).toBe('is_subscription_created');
    });

    it('should define settings events', () => {
      expect(Events.THEME_CHANGED).toBe('is_theme_changed');
      expect(Events.VOICE_SETTINGS_CHANGED).toBe('is_voice_settings_changed');
    });

    it('should define question bank events', () => {
      expect(Events.QUESTION_FILTER_APPLIED).toBe('is_question_filter_applied');
      expect(Events.QUESTION_PRACTICE_STARTED).toBe('is_question_practice_started');
    });

    it('should define error events', () => {
      expect(Events.UPLOAD_FAILED).toBe('is_upload_failed');
      expect(Events.API_ERROR).toBe('is_api_error');
    });
  });

  describe('analytics.init()', () => {
    it('should not throw during initialization', () => {
      // Since PostHog is mocked, init should not throw
      expect(() => analytics.init()).not.toThrow();
    });
  });

  describe('analytics.identify()', () => {
    it('should not throw when calling identify', () => {
      expect(() =>
        analytics.identify('123', { email: 'test@example.com', tier: 'pro' })
      ).not.toThrow();
    });

    it('should handle empty properties', () => {
      expect(() => analytics.identify('456', {})).not.toThrow();
    });

    it('should handle additional properties', () => {
      expect(() =>
        analytics.identify('789', {
          email: 'user@test.com',
          tier: 'enterprise',
          company: 'Acme Corp',
        })
      ).not.toThrow();
    });
  });

  describe('analytics.track()', () => {
    it('should not throw when tracking events with properties', () => {
      expect(() =>
        analytics.track(Events.USER_LOGGED_IN, { login_method: 'email' })
      ).not.toThrow();
    });

    it('should not throw when tracking interview events', () => {
      expect(() =>
        analytics.track(Events.INTERVIEW_STARTED, {
          interview_id: 'int_123',
          question_count: 5,
          category: 'behavioral',
        })
      ).not.toThrow();
    });

    it('should not throw when tracking recording events', () => {
      expect(() =>
        analytics.track(Events.RECORDING_COMPLETED, {
          duration_seconds: 120,
          question_id: 'q_456',
        })
      ).not.toThrow();
    });

    it('should not throw when tracking upgrade funnel events', () => {
      expect(() =>
        analytics.track(Events.UPGRADE_MODAL_OPENED, {
          trigger: 'limit_reached',
          current_tier: 'free',
        })
      ).not.toThrow();
    });

    it('should not throw when tracking error events', () => {
      expect(() =>
        analytics.track(Events.API_ERROR, {
          endpoint: '/api/v1/interviews',
          status_code: 500,
          error_message: 'Internal Server Error',
        })
      ).not.toThrow();
    });

    it('should allow custom event names as strings', () => {
      expect(() => analytics.track('custom_event', { data: 'value' })).not.toThrow();
    });
  });

  describe('analytics.pageView()', () => {
    it('should not throw when tracking page view with path', () => {
      expect(() => analytics.pageView('/dashboard')).not.toThrow();
    });

    it('should not throw when tracking page view with custom title', () => {
      expect(() => analytics.pageView('/interview', 'Interview Session')).not.toThrow();
    });
  });

  describe('analytics.reset()', () => {
    it('should not throw when calling reset', () => {
      expect(() => analytics.reset()).not.toThrow();
    });
  });

  describe('analytics.hasOptedOut()', () => {
    it('should return a boolean', () => {
      const result = analytics.hasOptedOut();
      expect(typeof result).toBe('boolean');
    });
  });

  describe('analytics.optOut()', () => {
    it('should not throw when opting out', () => {
      expect(() => analytics.optOut()).not.toThrow();
    });
  });

  describe('analytics.optIn()', () => {
    it('should not throw when opting in', () => {
      expect(() => analytics.optIn()).not.toThrow();
    });
  });

  describe('Error Handling', () => {
    it('should not throw when tracking events', () => {
      // Analytics should gracefully handle any errors
      expect(() => analytics.track(Events.USER_LOGGED_IN, {})).not.toThrow();
    });

    it('should handle identify calls gracefully', () => {
      expect(() => analytics.identify('123', {})).not.toThrow();
    });
  });

  describe('Event Naming Convention', () => {
    it('should follow is_ prefix convention for all events', () => {
      // Verify all events follow the {prefix}_{entity}_{action} naming convention
      const eventValues = Object.values(Events);

      eventValues.forEach(event => {
        // Each event should start with is_ prefix and have snake_case
        expect(event).toMatch(/^is_[a-z]+(_[a-z]+)+$/);
      });
    });
  });
});
