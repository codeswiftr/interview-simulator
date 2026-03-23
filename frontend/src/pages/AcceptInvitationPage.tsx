import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { Loader2, AlertCircle, Users, Crown, Check } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { teamAPI } from '../lib/api';
import { Card } from '../components/ui/Card';
import type { PublicInvitationRead } from '../types/team';
import type { AxiosError } from 'axios';

export default function AcceptInvitationPage() {
  const { token } = useParams<{ token: string }>();
  const navigate = useNavigate();
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  const [invitation, setInvitation] = useState<PublicInvitationRead | null>(null);
  const [isLoadingInvitation, setIsLoadingInvitation] = useState(true);
  const [invitationError, setInvitationError] = useState<string | null>(null);
  const [isAccepting, setIsAccepting] = useState(false);
  const [acceptError, setAcceptError] = useState<string | null>(null);

  // Load invitation details (public, no auth required)
  useEffect(() => {
    if (!token) {
      setInvitationError('Invalid invitation link.');
      setIsLoadingInvitation(false);
      return;
    }

    teamAPI
      .getInvitation(token)
      .then((data) => {
        setInvitation(data);
      })
      .catch((err: AxiosError<{ detail?: string }>) => {
        if (err.response?.status === 404 || err.response?.status === 410) {
          setInvitationError(
            'This invitation is no longer valid. Contact your team admin.'
          );
        } else {
          setInvitationError(
            err.response?.data?.detail ||
              'This invitation is no longer valid. Contact your team admin.'
          );
        }
      })
      .finally(() => {
        setIsLoadingInvitation(false);
      });
  }, [token]);

  const handleAccept = async () => {
    if (!token) return;
    try {
      setIsAccepting(true);
      setAcceptError(null);
      await teamAPI.acceptInvitation(token);
      navigate('/team');
    } catch (err) {
      const axiosError = err as AxiosError<{ detail?: string }>;
      setAcceptError(
        axiosError.response?.data?.detail ||
          'Failed to accept invitation. Please try again.'
      );
    } finally {
      setIsAccepting(false);
    }
  };

  // Loading: auth context still initializing
  if (authLoading || isLoadingInvitation) {
    return (
      <div className="min-h-screen bg-surface-primary flex items-center justify-center p-6">
        <div className="text-center">
          <Loader2 size={40} className="animate-spin text-electric-blue mx-auto mb-4" />
          <p className="text-text-secondary">Loading invitation...</p>
        </div>
      </div>
    );
  }

  // Invalid / expired invitation
  if (invitationError || !invitation) {
    return (
      <div className="min-h-screen bg-surface-primary flex items-center justify-center p-6">
        <Card className="p-8 max-w-md w-full text-center">
          <AlertCircle className="w-12 h-12 text-status-error mx-auto mb-4" />
          <h2 className="text-xl font-bold text-text-primary mb-2">
            Invitation Unavailable
          </h2>
          <p className="text-text-secondary mb-6">
            {invitationError ||
              'This invitation is no longer valid. Contact your team admin.'}
          </p>
          <Link to="/" className="btn-secondary inline-flex">
            Back to Home
          </Link>
        </Card>
      </div>
    );
  }

  const roleLabel = invitation.role === 'admin' ? 'Admin' : 'Member';
  const expiryDate = new Date(invitation.expires_at).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });

  return (
    <div className="min-h-screen bg-surface-primary flex items-center justify-center p-6">
      <Card className="p-8 max-w-md w-full">
        {/* Icon */}
        <div className="w-16 h-16 rounded-2xl bg-indigo-500/10 flex items-center justify-center mx-auto mb-5">
          <Users className="w-8 h-8 text-indigo-500" />
        </div>

        {/* Heading */}
        <h1 className="text-xl font-bold text-text-primary text-center mb-1">
          You're invited to join
        </h1>
        <h2 className="text-2xl font-extrabold text-text-primary text-center mb-4">
          {invitation.org_name}
        </h2>

        {/* Metadata */}
        <div className="space-y-3 mb-6 bg-surface-secondary rounded-xl p-4 text-sm">
          <div className="flex items-center justify-between">
            <span className="text-text-secondary">Invited by</span>
            <span className="font-medium text-text-primary">{invitation.inviter_name}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-text-secondary">Role</span>
            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-500/15 text-amber-700 border border-amber-500/30">
              {invitation.role === 'admin' ? (
                <Crown className="w-3 h-3" />
              ) : (
                <Users className="w-3 h-3" />
              )}
              {roleLabel}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-text-secondary">Expires</span>
            <span className="text-text-primary">{expiryDate}</span>
          </div>
        </div>

        {/* Auth-gated CTA */}
        {!isAuthenticated ? (
          <div className="space-y-3">
            <p className="text-sm text-text-secondary text-center mb-4">
              Sign in or create an account to accept this invitation.
            </p>
            <Link
              to={`/login?redirect=/join/${token}`}
              className="btn-primary w-full flex items-center justify-center gap-2"
            >
              Sign In
            </Link>
            <Link
              to={`/register?redirect=/join/${token}`}
              className="btn-secondary w-full flex items-center justify-center gap-2"
            >
              Create Account
            </Link>
          </div>
        ) : (
          <div className="space-y-3">
            {acceptError && (
              <div className="flex items-start gap-2 p-3 bg-status-error/10 border border-status-error/20 rounded-lg">
                <AlertCircle className="w-4 h-4 text-status-error shrink-0 mt-0.5" />
                <p className="text-sm text-status-error">{acceptError}</p>
              </div>
            )}
            <button
              className="btn-primary w-full flex items-center justify-center gap-2"
              onClick={handleAccept}
              disabled={isAccepting}
            >
              {isAccepting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Accepting...
                </>
              ) : (
                <>
                  <Check className="w-4 h-4" />
                  Accept Invitation
                </>
              )}
            </button>
          </div>
        )}
      </Card>
    </div>
  );
}
