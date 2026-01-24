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
      expect(Events.USER_REGISTERED).toBe('user_registered');
      expect(Events.USER_LOGGED_IN).toBe('user_logged_in');
      expect(Events.USER_LOGGED_OUT).toBe('user_logged_out');
    });

    it('should define all page events', () => {
      expect(Events.PAGE_VIEWED).toBe('page_viewed');
    });

    it('should define all upgrade/billing events', () => {
      expect(Events.UPGRADE_MODAL_OPENED).toBe('upgrade_modal_opened');
      expect(Events.UPGRADE_MODAL_CLOSED).toBe('upgrade_modal_closed');
      expect(Events.UPGRADE_CTA_CLICKED).toBe('upgrade_cta_clicked');
      expect(Events.CHECKOUT_STARTED).toBe('checkout_started');
      expect(Events.UPGRADE_REASON_SUBMITTED).toBe('upgrade_reason_submitted');
      expect(Events.LIMIT_REACHED).toBe('limit_reached');
    });

    it('should define all interview lifecycle events', () => {
      expect(Events.INTERVIEW_CREATED).toBe('interview_created');
      expect(Events.INTERVIEW_STARTED).toBe('interview_started');
      expect(Events.INTERVIEW_COMPLETED).toBe('interview_completed');
      expect(Events.INTERVIEW_ABANDONED).toBe('interview_abandoned');
    });

    it('should define all question/recording events', () => {
      expect(Events.QUESTION_VIEWED).toBe('question_viewed');
      expect(Events.QUESTION_SKIPPED).toBe('question_skipped');
      expect(Events.RECORDING_STARTED).toBe('recording_started');
      expect(Events.RECORDING_COMPLETED).toBe('recording_completed');
    });

    it('should define all feedback events', () => {
      expect(Events.FEEDBACK_GENERATED).toBe('feedback_generated');
      expect(Events.FEEDBACK_VIEWED).toBe('feedback_viewed');
    });

    it('should define all feature usage events', () => {
      expect(Events.SAMPLE_ANSWER_VIEWED).toBe('sample_answer_viewed');
      expect(Events.COACHING_HINT_USED).toBe('coaching_hint_used');
    });

    it('should define payment events', () => {
      expect(Events.SUBSCRIPTION_CREATED).toBe('subscription_created');
    });

    it('should define settings events', () => {
      expect(Events.THEME_CHANGED).toBe('theme_changed');
      expect(Events.VOICE_SETTINGS_CHANGED).toBe('voice_settings_changed');
    });

    it('should define question bank events', () => {
      expect(Events.QUESTION_FILTER_APPLIED).toBe('question_filter_applied');
      expect(Events.QUESTION_PRACTICE_STARTED).toBe('question_practice_started');
    });

    it('should define error events', () => {
      expect(Events.UPLOAD_FAILED).toBe('upload_failed');
      expect(Events.API_ERROR).toBe('api_error');
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
    it('should follow noun_action convention for all events', () => {
      // Verify all events follow the {noun}_{action} naming convention
      const eventValues = Object.values(Events);

      eventValues.forEach(event => {
        // Each event should have at least one underscore
        expect(event).toMatch(/^[a-z]+(_[a-z]+)+$/);
      });
    });
  });
});
