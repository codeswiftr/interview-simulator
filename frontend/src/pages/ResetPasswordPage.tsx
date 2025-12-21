import { useState, useEffect } from 'react';
import type { FormEvent } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import { authAPI } from '../lib/api';
import { useToast } from '../hooks/useToast';
import { AlertCircle, CheckCircle, Eye, EyeOff } from 'lucide-react';

export default function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const toast = useToast();
  const token = searchParams.get('token');

  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  useEffect(() => {
    if (!token) {
      setError('Invalid or missing reset token. Please request a new password reset link.');
    }
  }, [token]);

  const getPasswordStrength = (pass: string): { strength: string; color: string } => {
    if (pass.length === 0) return { strength: '', color: '' };
    if (pass.length < 8) return { strength: 'Too short', color: 'text-red-600' };
    if (pass.length < 12) return { strength: 'Good', color: 'text-yellow-600' };
    return { strength: 'Strong', color: 'text-green-600' };
  };

  const passwordStrength = getPasswordStrength(password);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validation
    if (password.length < 8) {
      setError('Password must be at least 8 characters long');
      return;
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (!token) {
      setError('Invalid or missing reset token');
      return;
    }

    setIsLoading(true);

    try {
      await authAPI.resetPassword(token, password);
      toast.success('Password Reset Successful', 'You can now sign in with your new password');
      setTimeout(() => {
        navigate('/login');
      }, 1500);
    } catch (err) {
      const errorMessage = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail || 'Failed to reset password';
      if (errorMessage.includes('expired') || errorMessage.includes('invalid')) {
        setError('This reset link has expired or is invalid. Please request a new one.');
      } else {
        setError(errorMessage);
      }
    } finally {
      setIsLoading(false);
    }
  };

  // Show error state if no token
  if (!token) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-surface-primary py-12 px-4">
        <div className="max-w-md w-full">
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-red-100 mb-4">
              <AlertCircle className="w-8 h-8 text-red-600" aria-hidden="true" />
            </div>
            <h1 className="heading-page mb-2">Invalid Reset Link</h1>
            <p className="text-text-secondary">
              This password reset link is invalid or has expired.
            </p>
          </div>

          <div className="card p-8">
            <div className="text-center space-y-4">
              <p className="text-sm text-text-secondary">
                Password reset links are only valid for 1 hour after being requested.
              </p>
              <Link
                to="/forgot-password"
                className="inline-block btn-primary"
              >
                Request New Reset Link
              </Link>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-surface-primary py-12 px-4">
      <div className="max-w-md w-full">
        <div className="text-center mb-8">
          <h1 className="heading-page mb-2">Create New Password</h1>
          <p className="text-text-secondary">
            Choose a strong password for your account
          </p>
        </div>

        <div className="card p-8">
          {error && (
            <div
              id="reset-error"
              role="alert"
              aria-live="assertive"
              className="mb-6 p-4 rounded-lg bg-red-50 border border-red-200 flex items-start gap-3"
            >
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" aria-hidden="true" />
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-text-primary mb-2">
                New Password
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="input pr-10"
                  placeholder="••••••••"
                  required
                  autoFocus
                  disabled={isLoading}
                  aria-invalid={!!error && error.toLowerCase().includes('password')}
                  aria-describedby="password-requirements password-strength reset-error"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-text-tertiary hover:text-text-secondary"
                  tabIndex={-1}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? (
                    <EyeOff className="w-5 h-5" aria-hidden="true" />
                  ) : (
                    <Eye className="w-5 h-5" aria-hidden="true" />
                  )}
                </button>
              </div>
              <div className="mt-2 flex items-center justify-between">
                <p id="password-requirements" className="text-xs text-text-tertiary">
                  Must be at least 8 characters long
                </p>
                {passwordStrength.strength && (
                  <p id="password-strength" className={`text-xs font-medium ${passwordStrength.color}`} aria-live="polite">
                    {passwordStrength.strength}
                  </p>
                )}
              </div>
            </div>

            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-text-primary mb-2">
                Confirm New Password
              </label>
              <div className="relative">
                <input
                  id="confirmPassword"
                  type={showConfirmPassword ? 'text' : 'password'}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="input pr-10"
                  placeholder="••••••••"
                  required
                  disabled={isLoading}
                  aria-invalid={confirmPassword.length > 0 && password !== confirmPassword}
                  aria-describedby="confirm-password-status"
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-text-tertiary hover:text-text-secondary"
                  tabIndex={-1}
                  aria-label={showConfirmPassword ? 'Hide password' : 'Show password'}
                >
                  {showConfirmPassword ? (
                    <EyeOff className="w-5 h-5" aria-hidden="true" />
                  ) : (
                    <Eye className="w-5 h-5" aria-hidden="true" />
                  )}
                </button>
              </div>
              <div id="confirm-password-status" aria-live="polite">
                {confirmPassword && password !== confirmPassword && (
                  <p className="mt-1 text-xs text-red-600">
                    Passwords do not match
                  </p>
                )}
                {confirmPassword && password === confirmPassword && (
                  <div className="mt-1 flex items-center gap-1 text-xs text-green-600">
                    <CheckCircle className="w-3 h-3" aria-hidden="true" />
                    <span>Passwords match</span>
                  </div>
                )}
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading || password !== confirmPassword || password.length < 8}
              className="btn-primary w-full disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Resetting Password...' : 'Reset Password'}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-text-secondary">
              Remember your password?{' '}
              <Link to="/login" className="text-electric-blue hover:underline font-medium">
                Sign in
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
