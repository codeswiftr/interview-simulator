import { useState, useEffect } from 'react';
import { X, Check, Crown, Loader2 } from 'lucide-react';
import { subscriptionsAPI } from '../../lib/api';
import { analytics, Events } from '../../lib/analytics';
import type { AxiosError } from 'axios';

interface UpgradeModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentTier?: 'free' | 'pro' | 'team';
  onSuccess?: () => void;
}

export default function UpgradeModal({
  isOpen,
  onClose,
}: UpgradeModalProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [priceId, setPriceId] = useState<string | null>(null);
  const [upgradeReason, setUpgradeReason] = useState<string>('');
  const [upgradeReasonDetails, setUpgradeReasonDetails] = useState<string>('');

  // Fetch pricing configuration when modal opens
  useEffect(() => {
    if (isOpen && !priceId) {
      subscriptionsAPI.getPricing()
        .then((response) => {
          setPriceId(response.data.pro_monthly_price_id);
        })
        .catch((err) => {
          console.error('Failed to fetch pricing:', err);
        });
    }
  }, [isOpen, priceId]);

  // Track upgrade intent
  useEffect(() => {
    if (!isOpen) return;
    analytics.track(Events.UPGRADE_MODAL_OPENED, { surface: 'upgrade_modal' });
  }, [isOpen]);

  if (!isOpen) return null;

  const submitUpgradeReason = () => {
    const reason = upgradeReason.trim();
    const details = upgradeReasonDetails.trim();
    if (!reason && !details) return;

    analytics.track(Events.UPGRADE_REASON_SUBMITTED, {
      surface: 'upgrade_modal',
      reason: reason || 'unspecified',
      details_len: details.length,
    });
  };

  const handleUpgrade = async () => {
    try {
      setLoading(true);
      setError(null);

      if (!priceId) {
        setError('Pricing not configured. Please contact support.');
        setLoading(false);
        return;
      }

      // Optional (non-blocking) intent signal before redirect
      submitUpgradeReason();

      analytics.track(Events.UPGRADE_CTA_CLICKED, { surface: 'upgrade_modal', plan: 'pro' });
      const response = await subscriptionsAPI.createCheckout(priceId);
      const checkoutUrl = response.data.url;

      analytics.track(Events.CHECKOUT_STARTED, { plan: 'pro' });
      // Redirect to Stripe checkout
      window.location.href = checkoutUrl;
    } catch (err) {
      const axiosError = err as AxiosError<{ detail?: string; message?: string }>;
      setError(axiosError.response?.data?.detail || axiosError.response?.data?.message || 'Failed to create checkout session');
      setLoading(false);
    }
  };

  const features = [
    'Unlimited interview sessions',
    'Full multimodal feedback analysis',
    'Advanced progress tracking',
    'Priority customer support',
    'Company-specific question sets',
  ];

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-6 z-50">
      <div className="card p-8 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <Crown className="w-6 h-6 text-[#FF6B9D]" />
            <h2 className="heading-section">Upgrade to Pro</h2>
          </div>
          <button
            onClick={onClose}
            className="text-text-tertiary hover:text-text-primary transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Error Message */}
        {error && (
          <div className="card p-4 mb-6 border-status-error bg-status-error/10">
            <p className="text-status-error">{error}</p>
          </div>
        )}

        {/* Pricing Comparison */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          {/* Free Plan */}
          <div className="card p-6 border-2 border-border-light">
            <h3 className="heading-card mb-2">Free</h3>
            <div className="text-3xl font-bold mb-4">$0<span className="text-lg">/month</span></div>
            <ul className="space-y-2">
              <li className="flex items-center gap-2 text-text-secondary">
                <Check className="w-4 h-4" />
                <span className="body-small">5 interviews/month</span>
              </li>
              <li className="flex items-center gap-2 text-text-secondary">
                <Check className="w-4 h-4" />
                <span className="body-small">Basic feedback</span>
              </li>
            </ul>
          </div>

          {/* Pro Plan */}
          <div className="card p-6 border-2 border-[#FF6B9D] bg-[#FF6B9D]/5">
            <div className="flex items-center gap-2 mb-2">
              <h3 className="heading-card">Pro</h3>
              <span className="badge bg-[#FF6B9D]/10 text-[#FF6B9D] border border-[#FF6B9D]/20">Recommended</span>
            </div>
            <div className="text-3xl font-bold mb-4">
              $29<span className="text-lg">/month</span>
            </div>
            <ul className="space-y-2">
              {features.map((feature, idx) => (
                <li key={idx} className="flex items-center gap-2 text-text-secondary">
                  <Check className="w-4 h-4 text-status-success" />
                  <span className="body-small">{feature}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="card p-4 mb-6 border-border-light">
          <p className="body-small text-text-secondary mb-3">
            Optional: what made you click upgrade? (helps improve the product)
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <select
              className="btn-secondary"
              value={upgradeReason}
              onChange={(e) => setUpgradeReason(e.target.value)}
            >
              <option value="">Select a reason…</option>
              <option value="unlimited_sessions">Unlimited sessions</option>
              <option value="better_feedback">Better feedback quality</option>
              <option value="interview_soon">Interview soon</option>
              <option value="company_specific">Company-specific questions</option>
              <option value="other">Other</option>
            </select>
            <input
              className="btn-secondary md:col-span-2"
              placeholder="Optional detail (one sentence)"
              value={upgradeReasonDetails}
              onChange={(e) => setUpgradeReasonDetails(e.target.value)}
            />
          </div>
          <div className="mt-3 flex justify-end">
            <button
              type="button"
              className="btn-secondary"
              onClick={submitUpgradeReason}
              disabled={!upgradeReason.trim() && !upgradeReasonDetails.trim()}
            >
              Send
            </button>
          </div>
        </div>

        <div className="flex gap-4">
          <button onClick={onClose} className="btn-secondary flex-1" disabled={loading}>
            Cancel
          </button>
          <button
            onClick={handleUpgrade}
            className="btn-primary flex-1 inline-flex items-center justify-center gap-2"
            disabled={loading}
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Processing...
              </>
            ) : (
              <>
                <Crown className="w-5 h-5" />
                Upgrade Now
              </>
            )}
          </button>
        </div>

        <p className="body-small text-text-tertiary text-center mt-4">
          You'll be redirected to Stripe to complete your payment
        </p>
      </div>
    </div>
  );
}
