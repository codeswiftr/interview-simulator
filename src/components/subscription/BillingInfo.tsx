import { useState } from 'react';
import { CreditCard, Calendar, ExternalLink, Loader2 } from 'lucide-react';
import { subscriptionsAPI } from '../../lib/api';
import { useToast } from '../../hooks/useToast';
import type { SubscriptionStatus } from '../../types';

interface BillingInfoProps {
  subscription: SubscriptionStatus;
  onSubscriptionChange?: () => void;
}

export default function BillingInfo({ subscription, onSubscriptionChange }: BillingInfoProps) {
  const { tier, status, expires_at } = subscription;
  const toast = useToast();
  const [isLoadingPortal, setIsLoadingPortal] = useState(false);
  const [isCanceling, setIsCanceling] = useState(false);
  const [showCancelConfirm, setShowCancelConfirm] = useState(false);

  // Don't show billing info for free tier or if there's no subscription status
  if (tier === 'free' || !status) {
    return null;
  }

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'long',
      day: 'numeric',
      year: 'numeric',
    });
  };

  const statusLabels: Record<string, string> = {
    active: 'Active',
    canceled: 'Canceled',
    past_due: 'Past Due',
    trialing: 'Trial',
    incomplete: 'Incomplete',
    cancel_at_period_end: 'Cancels at period end',
  };

  const handleManageSubscription = async () => {
    try {
      setIsLoadingPortal(true);
      const response = await subscriptionsAPI.createPortalSession();
      window.location.href = response.data.url;
    } catch (err: unknown) {
      const apiError = err as { response?: { data?: { detail?: string } } };
      toast.error('Error', apiError.response?.data?.detail || 'Failed to open billing portal');
      setIsLoadingPortal(false);
    }
  };

  const handleCancelSubscription = async () => {
    try {
      setIsCanceling(true);
      await subscriptionsAPI.cancel();
      toast.success('Subscription canceled', 'Your subscription will remain active until the end of the billing period.');
      setShowCancelConfirm(false);
      onSubscriptionChange?.();
    } catch (err: unknown) {
      const apiError = err as { response?: { data?: { detail?: string } } };
      toast.error('Error', apiError.response?.data?.detail || 'Failed to cancel subscription');
    } finally {
      setIsCanceling(false);
    }
  };

  const isCanceled = status === 'canceled' || status === 'cancel_at_period_end';
  const canCancel = status === 'active'; // Only allow cancel for active subscriptions

  return (
    <div className="card p-6">
      <h3 className="heading-card mb-4">Billing Information</h3>
      <div className="space-y-4">
        <div className="flex items-center gap-3">
          <CreditCard className="w-5 h-5 text-text-secondary" />
          <div>
            <p className="body-small text-text-tertiary">Status</p>
            <p className="body-default font-medium">
              {status ? statusLabels[status] || status : 'Active'}
            </p>
          </div>
        </div>
        {expires_at && (
          <div className="flex items-center gap-3">
            <Calendar className="w-5 h-5 text-text-secondary" />
            <div>
              <p className="body-small text-text-tertiary">
                {isCanceled ? 'Access until' : 'Renews on'}
              </p>
              <p className="body-default font-medium">{formatDate(expires_at)}</p>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="pt-4 border-t border-border-light space-y-3">
          <button
            onClick={handleManageSubscription}
            disabled={isLoadingPortal}
            className="btn-secondary w-full flex items-center justify-center gap-2"
          >
            {isLoadingPortal ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Opening portal...
              </>
            ) : (
              <>
                <ExternalLink className="w-4 h-4" />
                Manage Subscription & Invoices
              </>
            )}
          </button>

          {canCancel && !showCancelConfirm && (
            <button
              onClick={() => setShowCancelConfirm(true)}
              className="btn-ghost text-status-error w-full"
            >
              Cancel Subscription
            </button>
          )}

          {showCancelConfirm && (
            <div className="p-4 bg-status-error/10 rounded-lg border border-status-error/20">
              <p className="body-small text-text-primary mb-3">
                Are you sure you want to cancel? You'll still have access until the end of your billing period.
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => setShowCancelConfirm(false)}
                  className="btn-secondary flex-1"
                  disabled={isCanceling}
                >
                  Keep Subscription
                </button>
                <button
                  onClick={handleCancelSubscription}
                  disabled={isCanceling}
                  className="btn-primary bg-status-error hover:bg-status-error/90 flex-1 flex items-center justify-center gap-2"
                >
                  {isCanceling ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Canceling...
                    </>
                  ) : (
                    'Yes, Cancel'
                  )}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

