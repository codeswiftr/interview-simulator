import { useMemo } from 'react';
import { CheckCircle2, XCircle } from 'lucide-react';

interface PasswordStrengthIndicatorProps {
  password: string;
  className?: string;
}

interface StrengthCriteria {
  label: string;
  met: boolean;
}

/**
 * Password strength indicator component.
 * Shows visual feedback for password strength criteria.
 */
export function PasswordStrengthIndicator({ password, className = '' }: PasswordStrengthIndicatorProps) {
  const criteria = useMemo<StrengthCriteria[]>(() => {
    return [
      {
        label: 'At least 8 characters',
        met: password.length >= 8,
      },
      {
        label: 'Contains uppercase letter',
        met: /[A-Z]/.test(password),
      },
      {
        label: 'Contains lowercase letter',
        met: /[a-z]/.test(password),
      },
      {
        label: 'Contains number',
        met: /\d/.test(password),
      },
      {
        label: 'Contains special character',
        met: /[!@#$%^&*(),.?":{}|<>]/.test(password),
      },
    ];
  }, [password]);

  const strengthScore = criteria.filter((c) => c.met).length;
  const strengthLevel =
    strengthScore === 0
      ? 'none'
      : strengthScore <= 2
        ? 'weak'
        : strengthScore <= 3
          ? 'fair'
          : strengthScore === 4
            ? 'good'
            : 'strong';

  const strengthColor = {
    none: 'text-text-tertiary',
    weak: 'text-status-error',
    fair: 'text-status-warning',
    good: 'text-status-success',
    strong: 'text-status-success',
  }[strengthLevel];

  if (!password) {
    return null;
  }

  return (
    <div className={`mt-2 space-y-2 ${className}`}>
      <div className="flex items-center gap-2">
        <span className="text-xs text-text-secondary">Password strength:</span>
        <span className={`text-xs font-medium ${strengthColor}`}>
          {strengthLevel.charAt(0).toUpperCase() + strengthLevel.slice(1)}
        </span>
      </div>
      <div className="space-y-1">
        {criteria.map((criterion, index) => (
          <div key={index} className="flex items-center gap-2 text-xs">
            {criterion.met ? (
              <CheckCircle2 size={14} className="text-status-success" />
            ) : (
              <XCircle size={14} className="text-text-tertiary" />
            )}
            <span className={criterion.met ? 'text-status-success' : 'text-text-tertiary'}>
              {criterion.label}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
