/**
 * Affiliate tracking hook for Rewardful integration
 *
 * Rewardful automatically:
 * - Tracks referral clicks via ?via=CODE or ?ref=CODE
 * - Sets cookies for attribution
 * - Provides window.Rewardful.referral for checkout
 *
 * This hook provides utilities for accessing referral data
 * and integrating with the checkout flow.
 */

declare global {
  interface Window {
    Rewardful?: {
      referral?: string;
      affiliate?: {
        id: string;
        name: string;
        token: string;
      };
      coupon?: {
        id: string;
        code: string;
      };
      convert?: (options: { email: string }) => void;
    };
    rewardful?: (...args: unknown[]) => void;
  }
}

/**
 * Get the current referral code from Rewardful
 * Returns undefined if no referral is active
 */
export function getReferralCode(): string | undefined {
  if (typeof window !== 'undefined' && window.Rewardful?.referral) {
    return window.Rewardful.referral;
  }
  return undefined;
}

/**
 * Get affiliate information if available
 */
export function getAffiliateInfo() {
  if (typeof window !== 'undefined' && window.Rewardful?.affiliate) {
    return window.Rewardful.affiliate;
  }
  return undefined;
}

/**
 * Get coupon code if affiliate has one configured
 */
export function getCouponCode(): string | undefined {
  if (typeof window !== 'undefined' && window.Rewardful?.coupon?.code) {
    return window.Rewardful.coupon.code;
  }
  return undefined;
}

/**
 * Trigger conversion tracking after successful signup/purchase
 * Call this after a user completes registration or checkout
 */
export function trackConversion(email: string): void {
  if (typeof window !== 'undefined' && window.Rewardful?.convert) {
    window.Rewardful.convert({ email });
  }
}

/**
 * Check if Rewardful is loaded and ready
 */
export function isRewardfulReady(): boolean {
  return typeof window !== 'undefined' && typeof window.Rewardful !== 'undefined';
}

/**
 * Hook to access affiliate tracking data
 */
export function useAffiliateTracking() {
  return {
    referralCode: getReferralCode(),
    affiliateInfo: getAffiliateInfo(),
    couponCode: getCouponCode(),
    isReady: isRewardfulReady(),
    trackConversion,
  };
}

export default useAffiliateTracking;
