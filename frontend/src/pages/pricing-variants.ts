/**
 * Pricing page copy variants for A/B conversion testing.
 *
 * Usage: import the variant you want to test in PricingPage.tsx and
 * replace the inline strings with values from the variant object.
 *
 * Test one variant at a time. Track conversion with the existing
 * analytics.track(Events.UPGRADE_CTA_CLICKED) event already wired in
 * PricingPage.tsx — add a `variant` property to the event payload so
 * results are segmentable in PostHog.
 */

export interface PricingVariant {
  /** Short label used in analytics payloads, e.g. "A", "B", "C" */
  id: string;

  /** Primary h1 on the pricing page */
  headline: string;

  /** Supporting paragraph below the headline */
  subheadline: string;

  /** Label on the primary upgrade / start-trial CTA button */
  ctaText: string;

  /**
   * Social proof line rendered below the CTA or in the hero section.
   * Keep it to one sentence — it sits in a constrained layout.
   */
  socialProof: string;

  /**
   * Bottom-of-page section headline (the dark "Final CTA" band).
   * Kept separate because it often needs a different tone than the hero.
   */
  finalCtaHeadline: string;

  /** Supporting copy inside the Final CTA band */
  finalCtaSubheadline: string;
}

// ---------------------------------------------------------------------------
// Variant A — Baseline (current production copy)
// Extracted verbatim from PricingPage.tsx as of 2026-03-17.
// ---------------------------------------------------------------------------
export const variantA: PricingVariant = {
  id: 'A',
  headline: 'Simple, Transparent Pricing',
  subheadline: "Start free, upgrade when you're ready. No hidden fees, cancel anytime.",
  ctaText: 'Start Free Trial',
  socialProof: "Join thousands of engineers who've improved their interview skills.",
  finalCtaHeadline: 'Start Your Interview Prep Today',
  finalCtaSubheadline:
    "Join thousands of engineers who've improved their interview skills. Start with a 7-day free trial.",
};

// ---------------------------------------------------------------------------
// Variant B — Urgency + Social Proof
// Hypothesis: highlighting momentum ("500+ engineers") and the founding-member
// price window creates loss-aversion urgency that improves conversion.
// ---------------------------------------------------------------------------
export const variantB: PricingVariant = {
  id: 'B',
  headline: 'Founding Member Pricing — Closing Soon',
  subheadline:
    'Lock in $29/month before we raise prices. Cancel anytime, no questions asked.',
  ctaText: 'Claim Founding Member Price',
  socialProof: 'Join 500+ engineers who already upgraded this month.',
  finalCtaHeadline: 'This Price Disappears When Spots Fill',
  finalCtaSubheadline:
    'Founding Member pricing is limited. 500+ engineers have already locked it in — start your 7-day free trial before it closes.',
};

// ---------------------------------------------------------------------------
// Variant C — ROI / Outcome Focus
// Hypothesis: framing the subscription as an investment with a concrete
// salary-uplift number shifts the mental model from "cost" to "return",
// increasing willingness to pay.
// ---------------------------------------------------------------------------
export const variantC: PricingVariant = {
  id: 'C',
  headline: 'The $29 Investment That Pays Back $15,000',
  subheadline:
    'Engineers who practice with Interview Simulator see an average salary increase of $15K within 3 months. Start your free trial today.',
  ctaText: 'Start Earning More — Free Trial',
  socialProof: 'Average salary increase after 3 months of consistent practice: $15K.',
  finalCtaHeadline: 'Your Next Offer Could Be $15K Higher',
  finalCtaSubheadline:
    'One month of focused interview practice changes negotiation outcomes. Try it free for 7 days — no card required until you upgrade.',
};

// ---------------------------------------------------------------------------
// Convenience export — all variants in an array, useful for dynamic selection
// ---------------------------------------------------------------------------
export const pricingVariants: PricingVariant[] = [variantA, variantB, variantC];

/**
 * Look up a variant by its id. Falls back to variantA (baseline) if the
 * requested id is not found, so the page always renders safely.
 *
 * Example usage in PricingPage.tsx:
 *
 *   import { getVariant } from './pricing-variants';
 *   const copy = getVariant(import.meta.env.VITE_PRICING_VARIANT ?? 'A');
 *
 *   // Then in JSX:
 *   <h1>{copy.headline}</h1>
 *   <p>{copy.subheadline}</p>
 *   <button>{copy.ctaText}</button>
 *
 *   // And in the analytics call:
 *   analytics.track(Events.UPGRADE_CTA_CLICKED, {
 *     surface: 'pricing_page',
 *     plan: 'pro',
 *     billing_period: billingPeriod,
 *     variant: copy.id,   // <-- add this
 *   });
 */
export function getVariant(id: string): PricingVariant {
  return pricingVariants.find((v) => v.id === id) ?? variantA;
}
