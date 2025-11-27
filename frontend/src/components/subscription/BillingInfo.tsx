import { CreditCard, Calendar } from 'lucide-react';
import type { SubscriptionStatus } from '../../types';

interface BillingInfoProps {
  subscription: SubscriptionStatus;
}

export default function BillingInfo({ subscription }: BillingInfoProps) {
  const { tier, status, expires_at } = subscription;

  if (tier === 'free') {
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
              <p className="body-small text-text-tertiary">Renews on</p>
              <p className="body-default font-medium">{formatDate(expires_at)}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

