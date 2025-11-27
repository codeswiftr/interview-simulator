import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, Settings as SettingsIcon, Loader2 } from 'lucide-react';
import { subscriptionsAPI } from '../lib/api';
import SubscriptionCard from '../components/subscription/SubscriptionCard';
import BillingInfo from '../components/subscription/BillingInfo';
import UpgradeModal from '../components/subscription/UpgradeModal';
import type { SubscriptionStatus } from '../types';

export default function SettingsPage() {
  const [subscription, setSubscription] = useState<SubscriptionStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showUpgradeModal, setShowUpgradeModal] = useState(false);

  useEffect(() => {
    loadSubscription();
  }, []);

  const loadSubscription = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await subscriptionsAPI.getStatus();
      setSubscription(response.data);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to load subscription status');
    } finally {
      setLoading(false);
    }
  };

  const handleUpgrade = () => {
    setShowUpgradeModal(true);
  };

  const handleUpgradeSuccess = () => {
    setShowUpgradeModal(false);
    // Reload subscription status after successful upgrade
    setTimeout(() => {
      loadSubscription();
    }, 2000);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-electric-blue mx-auto mb-4" />
          <p className="body-large text-text-secondary">Loading settings...</p>
        </div>
      </div>
    );
  }

  if (error && !subscription) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="body-large text-status-error mb-4">{error}</p>
          <Link to="/dashboard" className="btn-primary">
            Return to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-surface-primary py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <Link
            to="/dashboard"
            className="inline-flex items-center gap-2 text-electric-blue hover:text-electric-blue/80 transition-colors mb-4"
          >
            <ArrowLeft className="w-4 h-4" />
            <span className="body-default font-medium">Back to Dashboard</span>
          </Link>

          <div className="flex items-center gap-3">
            <SettingsIcon className="w-6 h-6 text-electric-blue" />
            <h1 className="heading-page">Settings</h1>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="card p-4 mb-8 border-status-error bg-status-error/10">
            <p className="text-status-error">{error}</p>
          </div>
        )}

        {/* Subscription Section */}
        {subscription && (
          <div className="space-y-6">
            <SubscriptionCard subscription={subscription} onUpgrade={handleUpgrade} />
            <BillingInfo subscription={subscription} />
          </div>
        )}

        {/* Upgrade Modal */}
        {showUpgradeModal && subscription && (
          <UpgradeModal
            isOpen={showUpgradeModal}
            onClose={() => setShowUpgradeModal(false)}
            currentTier={subscription.tier}
            onSuccess={handleUpgradeSuccess}
          />
        )}
      </div>
    </div>
  );
}

