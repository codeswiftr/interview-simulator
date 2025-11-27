import { Crown, Check, X } from 'lucide-react';
import type { SubscriptionStatus } from '../../types';

interface SubscriptionCardProps {
  subscription: SubscriptionStatus;
  onUpgrade?: () => void;
}

export default function SubscriptionCard({ subscription, onUpgrade }: SubscriptionCardProps) {
  const { tier, interviews_this_month, interviews_limit, can_create_interview } = subscription;

  const tierLabels: Record<string, string> = {
    free: 'Free',
    pro: 'Pro',
    team: 'Team',
  };

  const tierColors: Record<string, string> = {
    free: 'bg-gray-100 text-gray-800',
    pro: 'bg-electric-blue/10 text-electric-blue',
    team: 'bg-purple-100 text-purple-800',
  };

  const usagePercentage =
    interviews_limit !== null ? (interviews_this_month / interviews_limit) * 100 : 0;

  return (
    <div className="card p-6">
      <div className="flex items-start justify-between mb-4">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <span className={`badge ${tierColors[tier]}`}>{tierLabels[tier]}</span>
            {tier !== 'free' && <Crown className="w-5 h-5 text-electric-blue" />}
          </div>
          <h3 className="heading-card">Current Plan</h3>
        </div>
        {tier === 'free' && onUpgrade && (
          <button onClick={onUpgrade} className="btn-primary">
            Upgrade
          </button>
        )}
      </div>

      {/* Usage Stats */}
      {interviews_limit !== null ? (
        <div className="mb-4">
          <div className="flex items-center justify-between mb-2">
            <span className="body-small text-text-secondary">Interviews this month</span>
            <span className="body-small font-medium">
              {interviews_this_month} / {interviews_limit}
            </span>
          </div>
          <div className="progress-bar">
            <div
              className={`progress-bar-fill ${
                usagePercentage >= 100 ? 'bg-status-error' : 'bg-electric-blue'
              }`}
              style={{ width: `${Math.min(usagePercentage, 100)}%` }}
            />
          </div>
          {!can_create_interview && (
            <p className="body-small text-status-error mt-2">
              Limit reached. Upgrade to Pro for unlimited interviews.
            </p>
          )}
        </div>
      ) : (
        <div className="mb-4">
          <div className="flex items-center gap-2 text-status-success">
            <Check className="w-4 h-4" />
            <span className="body-small">Unlimited interviews</span>
          </div>
        </div>
      )}

      {/* Features */}
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          {tier === 'free' ? (
            <X className="w-4 h-4 text-text-tertiary" />
          ) : (
            <Check className="w-4 h-4 text-status-success" />
          )}
          <span className="body-small text-text-secondary">Unlimited interviews</span>
        </div>
        <div className="flex items-center gap-2">
          {tier === 'free' ? (
            <X className="w-4 h-4 text-text-tertiary" />
          ) : (
            <Check className="w-4 h-4 text-status-success" />
          )}
          <span className="body-small text-text-secondary">Full multimodal feedback</span>
        </div>
        <div className="flex items-center gap-2">
          {tier === 'free' ? (
            <X className="w-4 h-4 text-text-tertiary" />
          ) : (
            <Check className="w-4 h-4 text-status-success" />
          )}
          <span className="body-small text-text-secondary">Priority support</span>
        </div>
      </div>
    </div>
  );
}

