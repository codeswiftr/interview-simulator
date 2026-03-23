import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Users,
  AlertCircle,
  Loader2,
  UserMinus,
  MailX,
  Crown,
  Send,
  CreditCard,
  X,
  Settings,
} from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { teamAPI, subscriptionsAPI } from '../lib/api';
import { Card } from '../components/ui/Card';
import { Modal } from '../components/ui/Modal';
import type { TeamRead } from '../types/team';
import type { AxiosError } from 'axios';

// ─── Invite Members Modal ────────────────────────────────────────────────────

interface InviteMembersModalProps {
  isOpen: boolean;
  onClose: () => void;
  orgId: string;
  onSuccess: () => void;
}

function InviteMembersModal({ isOpen, onClose, orgId, onSuccess }: InviteMembersModalProps) {
  const [emailsRaw, setEmailsRaw] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sentCount, setSentCount] = useState<number | null>(null);

  const handleClose = () => {
    setEmailsRaw('');
    setError(null);
    setSentCount(null);
    onClose();
  };

  const parseEmails = (raw: string): string[] => {
    return raw
      .split(/[\n,]+/)
      .map((e) => e.trim())
      .filter((e) => e.length > 0 && e.includes('@'));
  };

  const handleSubmit = async () => {
    const emails = parseEmails(emailsRaw);
    if (emails.length === 0) {
      setError('Please enter at least one valid email address.');
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);
      const result = await teamAPI.inviteMembers(orgId, emails);
      setSentCount(result.sent);
      onSuccess();
    } catch (err) {
      const axiosError = err as AxiosError<{ detail?: string }>;
      setError(axiosError.response?.data?.detail || 'Failed to send invitations. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Invite Team Members" size="md">
      {sentCount !== null ? (
        <div className="text-center py-4">
          <div className="w-16 h-16 rounded-full bg-status-success/10 flex items-center justify-center mx-auto mb-4">
            <Send className="w-8 h-8 text-status-success" />
          </div>
          <h3 className="text-lg font-semibold text-text-primary mb-2">Invitations Sent</h3>
          <p className="text-text-secondary mb-6">
            {sentCount} invitation{sentCount !== 1 ? 's' : ''} sent successfully. Team members will
            receive an email with a link to join.
          </p>
          <button className="btn-primary" onClick={handleClose}>
            Done
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          <p className="text-text-secondary text-sm">
            Enter email addresses separated by commas or one per line.
          </p>

          <div>
            <label
              htmlFor="invite-emails"
              className="block text-sm font-medium text-text-primary mb-1.5"
            >
              Email Addresses
            </label>
            <textarea
              id="invite-emails"
              value={emailsRaw}
              onChange={(e) => setEmailsRaw(e.target.value)}
              placeholder={'alice@company.com\nbob@company.com'}
              rows={5}
              className="w-full rounded-xl border border-border-light bg-surface-secondary px-4 py-3 text-sm text-text-primary placeholder:text-text-tertiary focus:outline-none focus:ring-2 focus:ring-electric-blue resize-none"
            />
          </div>

          {error && (
            <div className="flex items-start gap-2 p-3 bg-status-error/10 border border-status-error/20 rounded-lg">
              <AlertCircle className="w-4 h-4 text-status-error shrink-0 mt-0.5" />
              <p className="text-sm text-status-error">{error}</p>
            </div>
          )}

          <div className="flex gap-3 pt-2">
            <button className="btn-secondary flex-1" onClick={handleClose} disabled={isSubmitting}>
              Cancel
            </button>
            <button
              className="btn-primary flex-1 flex items-center justify-center gap-2"
              onClick={handleSubmit}
              disabled={isSubmitting}
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Sending...
                </>
              ) : (
                <>
                  <Send className="w-4 h-4" />
                  Send Invitations
                </>
              )}
            </button>
          </div>
        </div>
      )}
    </Modal>
  );
}

// ─── Role Badge ──────────────────────────────────────────────────────────────

function RoleBadge({ role }: { role: 'admin' | 'member' }) {
  if (role === 'admin') {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-amber-500/15 text-amber-700 border border-amber-500/30">
        <Crown className="w-3 h-3" />
        Admin
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-indigo-500/10 text-indigo-600 border border-indigo-500/20">
      <Users className="w-3 h-3" />
      Member
    </span>
  );
}

// ─── Status Badge ────────────────────────────────────────────────────────────

function StatusBadge({ status }: { status: string }) {
  const styleMap: Record<string, string> = {
    pending:
      'bg-amber-500/10 text-amber-700 border-amber-500/20',
    accepted:
      'bg-status-success/10 text-status-success border-status-success/20',
    declined:
      'bg-status-error/10 text-status-error border-status-error/20',
    expired:
      'bg-surface-secondary text-text-tertiary border-border-light',
  };
  const label = status.charAt(0).toUpperCase() + status.slice(1);
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${
        styleMap[status] ?? styleMap.pending
      }`}
    >
      {label}
    </span>
  );
}

// ─── Seat Usage Bar ──────────────────────────────────────────────────────────

function SeatUsageBar({ used, total }: { used: number; total: number }) {
  const pct = total > 0 ? Math.min(100, Math.round((used / total) * 100)) : 0;
  const isNearFull = pct >= 80;
  const barColor = isNearFull ? 'bg-amber-500' : 'bg-electric-blue';

  return (
    <div className="w-full">
      <div className="flex items-center justify-between text-xs text-text-secondary mb-1.5">
        <span>Seat Usage</span>
        <span>
          {used} / {total} seats used
        </span>
      </div>
      <div className="w-full h-2 rounded-full bg-surface-secondary overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${barColor}`}
          style={{ width: `${pct}%` }}
          role="progressbar"
          aria-valuenow={used}
          aria-valuemin={0}
          aria-valuemax={total}
          aria-label={`${used} of ${total} seats used`}
        />
      </div>
    </div>
  );
}

// ─── Skeleton ────────────────────────────────────────────────────────────────

function TeamDashboardSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="h-8 w-56 rounded-lg bg-surface-secondary" />
      <Card className="p-6">
        <div className="h-5 w-32 rounded bg-surface-secondary mb-4" />
        <div className="h-2 w-full rounded-full bg-surface-secondary" />
      </Card>
      <Card className="p-6">
        <div className="h-5 w-24 rounded bg-surface-secondary mb-4" />
        {[1, 2, 3].map((i) => (
          <div key={i} className="flex items-center gap-4 py-3 border-b border-border-light last:border-0">
            <div className="w-8 h-8 rounded-full bg-surface-secondary" />
            <div className="flex-1 space-y-1.5">
              <div className="h-4 w-40 rounded bg-surface-secondary" />
              <div className="h-3 w-28 rounded bg-surface-secondary" />
            </div>
          </div>
        ))}
      </Card>
    </div>
  );
}

// ─── Main Page ───────────────────────────────────────────────────────────────

export default function TeamDashboardPage() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [team, setTeam] = useState<TeamRead | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isInviteOpen, setIsInviteOpen] = useState(false);
  const [removingUserId, setRemovingUserId] = useState<string | null>(null);
  const [revokingInviteId, setRevokingInviteId] = useState<string | null>(null);
  const [billingLoading, setBillingLoading] = useState(false);

  const loadTeam = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await teamAPI.getMyTeam();
      setTeam(data);
    } catch (err) {
      const axiosError = err as AxiosError<{ detail?: string }>;
      if (axiosError.response?.status === 404) {
        // Not in a team — redirect to pricing
        navigate('/pricing');
      } else {
        setError(axiosError.response?.data?.detail || 'Failed to load team data.');
      }
    } finally {
      setIsLoading(false);
    }
  }, [navigate]);

  useEffect(() => {
    loadTeam();
  }, [loadTeam]);

  const handleRemoveMember = async (userId: string) => {
    if (!team) return;
    try {
      setRemovingUserId(userId);
      await teamAPI.removeMember(team.id, userId);
      await loadTeam();
    } catch (err) {
      const axiosError = err as AxiosError<{ detail?: string }>;
      setError(axiosError.response?.data?.detail || 'Failed to remove member.');
    } finally {
      setRemovingUserId(null);
    }
  };

  const handleRevokeInvitation = async (invitationId: string) => {
    if (!team) return;
    try {
      setRevokingInviteId(invitationId);
      await teamAPI.revokeInvitation(team.id, invitationId);
      await loadTeam();
    } catch (err) {
      const axiosError = err as AxiosError<{ detail?: string }>;
      setError(axiosError.response?.data?.detail || 'Failed to revoke invitation.');
    } finally {
      setRevokingInviteId(null);
    }
  };

  const handleToggleRole = async (userId: string, currentRole: 'admin' | 'member') => {
    if (!team) return;
    const newRole = currentRole === 'admin' ? 'member' : 'admin';
    try {
      await teamAPI.updateMemberRole(team.id, userId, newRole);
      await loadTeam();
    } catch {
      setError('Failed to update member role.');
    }
  };

  const handleManageBilling = async () => {
    try {
      setBillingLoading(true);
      const response = await subscriptionsAPI.createPortalSession();
      window.location.href = response.data.url;
    } catch {
      window.location.href = 'https://billing.stripe.com';
    } finally {
      setBillingLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-surface-primary pb-12">
        <div className="container mx-auto px-4 sm:px-6 py-8 max-w-4xl">
          <TeamDashboardSkeleton />
        </div>
      </div>
    );
  }

  if (error || !team) {
    return (
      <div className="min-h-screen bg-surface-primary flex items-center justify-center p-6">
        <Card className="p-8 max-w-md w-full text-center">
          <AlertCircle className="w-12 h-12 text-status-error mx-auto mb-4" />
          <h2 className="heading-section mb-2">Failed to Load Team</h2>
          <p className="body-default text-text-secondary mb-6">
            {error || 'Something went wrong loading your team.'}
          </p>
          <button className="btn-primary" onClick={loadTeam}>
            Try Again
          </button>
        </Card>
      </div>
    );
  }

  const pendingInvitations = team.pending_invitations.filter(
    (inv) => inv.status === 'pending'
  );

  return (
    <div className="min-h-screen bg-surface-primary pb-12">
      <div className="container mx-auto px-4 sm:px-6 py-8 max-w-4xl">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
          <div>
            <h1 className="heading-page mb-1">{team.name}</h1>
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-medium bg-indigo-500/10 text-indigo-600 border border-indigo-500/20">
                <Crown className="w-3.5 h-3.5" />
                Team Plan
              </span>
              {team.subscription_status && (
                <StatusBadge status={team.subscription_status} />
              )}
            </div>
          </div>

          <div className="flex items-center gap-3">
            {team.is_admin && (
              <button
                className="btn-secondary flex items-center gap-2"
                onClick={() => setIsInviteOpen(true)}
              >
                <Users className="w-4 h-4" />
                Invite Members
              </button>
            )}
            <button
              className="btn-secondary flex items-center gap-2"
              onClick={handleManageBilling}
              disabled={billingLoading}
            >
              {billingLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <CreditCard className="w-4 h-4" />
              )}
              Manage Billing
            </button>
            {team?.is_admin && (
              <button
                onClick={() => navigate('/team/settings')}
                className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                <Settings className="w-4 h-4" />
                Settings
              </button>
            )}
          </div>
        </div>

        {/* Seat Usage Card */}
        <Card className="p-6 mb-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 rounded-lg bg-indigo-500/10">
              <Users className="w-5 h-5 text-indigo-500" />
            </div>
            <div>
              <h2 className="heading-card">
                Team Plan — {team.seats_used} of {team.seat_count} seats used
              </h2>
            </div>
          </div>
          <SeatUsageBar used={team.seats_used} total={team.seat_count} />
        </Card>

        {/* Members Table */}
        <Card className="p-6 mb-6">
          <h2 className="heading-section mb-4">Members ({team.members.length})</h2>

          {team.members.length === 0 ? (
            <p className="text-text-secondary text-sm py-4 text-center">
              No members yet. Invite your team to get started.
            </p>
          ) : (
            <div className="overflow-x-auto -mx-2">
              <table className="w-full text-sm min-w-[500px]">
                <thead>
                  <tr className="border-b border-border-light">
                    <th className="text-left py-3 px-2 text-text-secondary font-medium">Name</th>
                    <th className="text-left py-3 px-2 text-text-secondary font-medium">Email</th>
                    <th className="text-left py-3 px-2 text-text-secondary font-medium">Role</th>
                    <th className="text-left py-3 px-2 text-text-secondary font-medium">Joined</th>
                    {team.is_admin && (
                      <th className="text-right py-3 px-2 text-text-secondary font-medium">
                        Action
                      </th>
                    )}
                  </tr>
                </thead>
                <tbody>
                  {team.members.map((member) => {
                    const isSelf = member.email === user?.email;
                    return (
                      <tr
                        key={member.user_id}
                        className="border-b border-border-light last:border-0 hover:bg-surface-secondary/50 transition-colors"
                      >
                        <td className="py-3 px-2 text-text-primary font-medium">
                          {member.full_name || '—'}
                          {isSelf && (
                            <span className="ml-2 text-xs text-text-tertiary">(you)</span>
                          )}
                        </td>
                        <td className="py-3 px-2 text-text-secondary">{member.email}</td>
                        <td className="py-3 px-2">
                          <RoleBadge role={member.role} />
                        </td>
                        <td className="py-3 px-2 text-text-secondary">
                          {new Date(member.joined_at).toLocaleDateString()}
                        </td>
                        {team.is_admin && (
                          <td className="py-3 px-2 text-right">
                            {!isSelf && (
                              <>
                                {team.is_admin && member.user_id !== user?.id && (
                                  <button
                                    onClick={() => handleToggleRole(member.user_id, member.role)}
                                    className="text-xs text-indigo-600 hover:text-indigo-800 mr-2"
                                    title={member.role === 'admin' ? 'Demote to member' : 'Promote to admin'}
                                  >
                                    {member.role === 'admin' ? 'Demote' : 'Promote'}
                                  </button>
                                )}
                                <button
                                  onClick={() => handleRemoveMember(member.user_id)}
                                  disabled={removingUserId === member.user_id}
                                  className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs text-status-error hover:bg-status-error/10 transition-colors disabled:opacity-50"
                                  aria-label={`Remove ${member.email}`}
                                >
                                  {removingUserId === member.user_id ? (
                                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                                  ) : (
                                    <UserMinus className="w-3.5 h-3.5" />
                                  )}
                                  Remove
                                </button>
                              </>
                            )}
                          </td>
                        )}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </Card>

        {/* Pending Invitations */}
        {pendingInvitations.length > 0 && (
          <Card className="p-6 mb-6">
            <h2 className="heading-section mb-4">
              Pending Invitations ({pendingInvitations.length})
            </h2>
            <div className="overflow-x-auto -mx-2">
              <table className="w-full text-sm min-w-[480px]">
                <thead>
                  <tr className="border-b border-border-light">
                    <th className="text-left py-3 px-2 text-text-secondary font-medium">Email</th>
                    <th className="text-left py-3 px-2 text-text-secondary font-medium">Status</th>
                    <th className="text-left py-3 px-2 text-text-secondary font-medium">Expires</th>
                    {team.is_admin && (
                      <th className="text-right py-3 px-2 text-text-secondary font-medium">
                        Action
                      </th>
                    )}
                  </tr>
                </thead>
                <tbody>
                  {pendingInvitations.map((inv) => (
                    <tr
                      key={inv.id}
                      className="border-b border-border-light last:border-0 hover:bg-surface-secondary/50 transition-colors"
                    >
                      <td className="py-3 px-2 text-text-primary">{inv.email}</td>
                      <td className="py-3 px-2">
                        <StatusBadge status={inv.status} />
                      </td>
                      <td className="py-3 px-2 text-text-secondary">
                        {new Date(inv.expires_at).toLocaleDateString()}
                      </td>
                      {team.is_admin && (
                        <td className="py-3 px-2 text-right">
                          <button
                            onClick={() => handleRevokeInvitation(inv.id)}
                            disabled={revokingInviteId === inv.id}
                            className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs text-status-error hover:bg-status-error/10 transition-colors disabled:opacity-50"
                            aria-label={`Revoke invitation for ${inv.email}`}
                          >
                            {revokingInviteId === inv.id ? (
                              <Loader2 className="w-3.5 h-3.5 animate-spin" />
                            ) : (
                              <MailX className="w-3.5 h-3.5" />
                            )}
                            Revoke
                          </button>
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        )}

        {/* Error toast-like banner */}
        {error && (
          <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 flex items-center gap-3 px-5 py-3 bg-status-error text-white rounded-xl shadow-lg">
            <AlertCircle className="w-5 h-5 shrink-0" />
            <span className="text-sm">{error}</span>
            <button
              onClick={() => setError(null)}
              className="ml-2 p-0.5 hover:bg-white/20 rounded transition-colors"
              aria-label="Dismiss error"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>

      {/* Invite Members Modal */}
      {team && (
        <InviteMembersModal
          isOpen={isInviteOpen}
          onClose={() => setIsInviteOpen(false)}
          orgId={team.id}
          onSuccess={loadTeam}
        />
      )}
    </div>
  );
}
