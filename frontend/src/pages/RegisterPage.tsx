import { useEffect, useState } from 'react';
import type { FormEvent } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { AlertCircle } from 'lucide-react';
import { PasswordStrengthIndicator } from '../components/ui/PasswordStrengthIndicator';
import { trackConversion } from '../hooks/useAffiliateTracking';
import type { ExperienceLevel } from '../types';
import type { AxiosError } from 'axios';

export default function RegisterPage() {
  const { register } = useAuth();
  const [searchParams] = useSearchParams();
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [experienceLevel, setExperienceLevel] = useState<ExperienceLevel>('mid');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  // Preserve pricing intent from marketing pages (e.g. /register?plan=pro)
  // so we can open the upgrade flow immediately after signup.
  useEffect(() => {
    const plan = searchParams.get('plan');
    if (plan) {
      sessionStorage.setItem('pending_plan', plan);
    }
  }, [searchParams]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');

    // Validation
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters long');
      return;
    }

    setIsLoading(true);

    try {
      await register(email, password, fullName, experienceLevel);
      // Track affiliate conversion on successful signup
      trackConversion(email);
    } catch (err) {
      const axiosError = err as AxiosError<{ detail?: string }>;
      setError(axiosError.response?.data?.detail || 'Registration failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-surface-primary py-12 px-4">
      <div className="max-w-md w-full">
        <div className="text-center mb-8">
          <h1 className="heading-page mb-2">Create Your Account</h1>
          <p className="text-text-secondary">Start practicing for your dream job</p>
        </div>

        <div className="card p-8">
          {error && (
            <div
              id="register-error"
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
              <label htmlFor="fullName" className="block text-sm font-medium text-text-primary mb-2">
                Full Name
              </label>
              <input
                id="fullName"
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="input"
                placeholder="John Doe"
                required
                autoFocus
                aria-invalid={!!error}
                aria-describedby={error ? 'register-error' : undefined}
              />
            </div>

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-text-primary mb-2">
                Email Address
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="input"
                placeholder="you@example.com"
                required
                aria-invalid={!!error}
                aria-describedby={error ? 'register-error' : undefined}
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-text-primary mb-2">
                Password
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="input"
                placeholder="••••••••"
                required
                aria-invalid={!!error && error.toLowerCase().includes('password')}
                aria-describedby="password-strength register-error"
              />
              <div id="password-strength">
                <PasswordStrengthIndicator password={password} />
              </div>
            </div>

            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-text-primary mb-2">
                Confirm Password
              </label>
              <input
                id="confirmPassword"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="input"
                placeholder="••••••••"
                required
                aria-invalid={!!error && error.toLowerCase().includes('match')}
                aria-describedby={error ? 'register-error' : undefined}
              />
            </div>

            <div>
              <label htmlFor="experienceLevel" className="block text-sm font-medium text-text-primary mb-2">
                Experience Level
              </label>
              <select
                id="experienceLevel"
                value={experienceLevel}
                onChange={(e) => setExperienceLevel(e.target.value as ExperienceLevel)}
                className="input"
                aria-describedby="experience-hint"
              >
                <option value="junior">Junior (0-2 years)</option>
                <option value="mid">Mid-Level (2-5 years)</option>
                <option value="senior">Senior (5+ years)</option>
              </select>
              <p id="experience-hint" className="mt-1 text-xs text-text-tertiary">
                This helps us tailor feedback to your experience level
              </p>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="btn-primary w-full disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Creating account...' : 'Create Account'}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-text-secondary">
              Already have an account?{' '}
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
