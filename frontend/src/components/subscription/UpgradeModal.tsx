import { useState } from 'react';
import { X, Check, Crown, Loader2 } from 'lucide-react';
import { subscriptionsAPI } from '../../lib/api';

interface UpgradeModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentTier: 'free' | 'pro' | 'team';
  onSuccess?: () => void;
}

export default function UpgradeModal({
  isOpen,
  onClose,
  currentTier: _currentTier,
  onSuccess: _onSuccess,
}: UpgradeModalProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleUpgrade = async () => {
    try {
      setLoading(true);
      setError(null);

      // TODO: Get actual price ID from config or API
      // For now, using placeholder - should come from backend config
      const priceId = 'price_pro_monthly'; // This should be fetched from API or config

      const response = await subscriptionsAPI.createCheckout(priceId);
      const checkoutUrl = response.data.url;

      // Redirect to Stripe checkout
      window.location.href = checkoutUrl;
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to create checkout session');
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
            <Crown className="w-6 h-6 text-electric-blue" />
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
                <span className="body-small">3 interviews/month</span>
              </li>
              <li className="flex items-center gap-2 text-text-secondary">
                <Check className="w-4 h-4" />
                <span className="body-small">Basic feedback</span>
              </li>
            </ul>
          </div>

          {/* Pro Plan */}
          <div className="card p-6 border-2 border-electric-blue bg-electric-blue/5">
            <div className="flex items-center gap-2 mb-2">
              <h3 className="heading-card">Pro</h3>
              <span className="badge badge-in-progress">Recommended</span>
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

