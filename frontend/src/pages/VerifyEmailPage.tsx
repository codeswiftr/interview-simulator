import { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { CheckCircle, XCircle, Loader2 } from 'lucide-react';
import api from '../lib/api';

type VerificationStatus = 'loading' | 'success' | 'error';

export default function VerifyEmailPage() {
  const [searchParams] = useSearchParams();
  const [status, setStatus] = useState<VerificationStatus>('loading');
  const [message, setMessage] = useState('');

  useEffect(() => {
    const verifyEmail = async () => {
      const token = searchParams.get('token');

      if (!token) {
        setStatus('error');
        setMessage('Invalid verification link. Please request a new email change.');
        return;
      }

      try {
        const response = await api.post('/users/verify-email', null, {
          params: { token },
        });
        setStatus('success');
        setMessage(response.data.message || 'Email address successfully verified and updated.');
      } catch (error) {
        setStatus('error');
        const axiosError = error as { response?: { data?: { detail?: string } } };
        setMessage(
          axiosError.response?.data?.detail ||
            'Verification failed. The link may have expired or already been used.'
        );
      }
    };

    verifyEmail();
  }, [searchParams]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-surface-primary py-12 px-4">
      <div className="max-w-md w-full">
        <div className="card p-8 text-center">
          {status === 'loading' && (
            <>
              <Loader2
                size={48}
                className="animate-spin text-electric-blue mx-auto mb-4"
              />
              <h1 className="heading-section mb-2">Verifying Email</h1>
              <p className="text-text-secondary">
                Please wait while we verify your new email address...
              </p>
            </>
          )}

          {status === 'success' && (
            <>
              <CheckCircle
                size={48}
                className="text-status-success mx-auto mb-4"
              />
              <h1 className="heading-section mb-2">Email Verified</h1>
              <p className="text-text-secondary mb-6">{message}</p>
              <Link to="/settings" className="btn-primary inline-flex">
                Go to Settings
              </Link>
            </>
          )}

          {status === 'error' && (
            <>
              <XCircle
                size={48}
                className="text-status-error mx-auto mb-4"
              />
              <h1 className="heading-section mb-2">Verification Failed</h1>
              <p className="text-text-secondary mb-6">{message}</p>
              <div className="flex flex-col gap-3">
                <Link to="/settings" className="btn-primary">
                  Go to Settings
                </Link>
                <Link
                  to="/dashboard"
                  className="text-text-secondary hover:text-text-primary text-sm"
                >
                  Return to Dashboard
                </Link>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
