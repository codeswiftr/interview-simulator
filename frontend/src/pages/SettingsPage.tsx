import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ArrowLeft, Settings as SettingsIcon, Loader2, User, Lock, Trash2, AlertTriangle, Check } from 'lucide-react';
import { subscriptionsAPI, userAPI, authAPI } from '../lib/api';
import { useToast } from '../hooks/useToast';
import { useAuth } from '../hooks/useAuth';
import SubscriptionCard from '../components/subscription/SubscriptionCard';
import BillingInfo from '../components/subscription/BillingInfo';
import UpgradeModal from '../components/subscription/UpgradeModal';
import type { SubscriptionStatus } from '../types';

export default function SettingsPage() {
  const navigate = useNavigate();
  const toast = useToast();
  const { user, refreshUser } = useAuth();

  const [subscription, setSubscription] = useState<SubscriptionStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showUpgradeModal, setShowUpgradeModal] = useState(false);

  // Profile edit state
  const [profileData, setProfileData] = useState({
    full_name: '',
    email: '',
  });
  const [isSavingProfile, setIsSavingProfile] = useState(false);

  // Password change state
  const [passwordData, setPasswordData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  });
  const [isChangingPassword, setIsChangingPassword] = useState(false);

  // Delete account state
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleteConfirmText, setDeleteConfirmText] = useState('');
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    loadSubscription();
  }, []);

  useEffect(() => {
    if (user) {
      setProfileData({
        full_name: user.full_name || '',
        email: user.email || '',
      });
    }
  }, [user]);

  const loadSubscription = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await subscriptionsAPI.getStatus();
      setSubscription(response.data);
    } catch (err: unknown) {
      const apiError = err as { response?: { data?: { message?: string } } };
      setError(apiError.response?.data?.message || 'Failed to load subscription status');
    } finally {
      setLoading(false);
    }
  };

  const handleUpgrade = () => {
    setShowUpgradeModal(true);
  };

  const handleUpgradeSuccess = () => {
    setShowUpgradeModal(false);
    setTimeout(() => {
      loadSubscription();
    }, 2000);
  };

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setIsSavingProfile(true);
      await userAPI.updateProfile(profileData);
      await refreshUser();
      toast.success('Profile updated', 'Your profile has been saved');
    } catch (err: unknown) {
      const apiError = err as { response?: { data?: { detail?: string } } };
      toast.error('Error', apiError.response?.data?.detail || 'Failed to update profile');
    } finally {
      setIsSavingProfile(false);
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();

    if (passwordData.newPassword !== passwordData.confirmPassword) {
      toast.error('Error', 'New passwords do not match');
      return;
    }

    if (passwordData.newPassword.length < 8) {
      toast.error('Error', 'Password must be at least 8 characters');
      return;
    }

    try {
      setIsChangingPassword(true);
      await userAPI.changePassword(passwordData.currentPassword, passwordData.newPassword);
      toast.success('Password changed', 'Your password has been updated');
      setPasswordData({ currentPassword: '', newPassword: '', confirmPassword: '' });
    } catch (err: unknown) {
      const apiError = err as { response?: { data?: { detail?: string } } };
      toast.error('Error', apiError.response?.data?.detail || 'Failed to change password');
    } finally {
      setIsChangingPassword(false);
    }
  };

  const handleDeleteAccount = async () => {
    if (deleteConfirmText !== 'DELETE') {
      toast.error('Error', 'Please type DELETE to confirm');
      return;
    }

    try {
      setIsDeleting(true);
      await userAPI.deleteAccount();
      toast.success('Account deleted', 'Your account has been deleted');
      authAPI.logout();
      navigate('/');
    } catch (err: unknown) {
      const apiError = err as { response?: { data?: { detail?: string } } };
      toast.error('Error', apiError.response?.data?.detail || 'Failed to delete account');
    } finally {
      setIsDeleting(false);
    }
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

        <div className="space-y-8">
          {/* Profile Section */}
          <div className="card p-6">
            <div className="flex items-center gap-3 mb-6">
              <User className="w-5 h-5 text-electric-blue" />
              <h2 className="heading-section">Profile</h2>
            </div>

            <form onSubmit={handleSaveProfile} className="space-y-4">
              <div>
                <label className="label mb-2 block">Full Name</label>
                <input
                  type="text"
                  value={profileData.full_name}
                  onChange={(e) => setProfileData({ ...profileData, full_name: e.target.value })}
                  className="input w-full"
                  placeholder="Enter your full name"
                />
              </div>

              <div>
                <label className="label mb-2 block">Email</label>
                <input
                  type="email"
                  value={profileData.email}
                  onChange={(e) => setProfileData({ ...profileData, email: e.target.value })}
                  className="input w-full"
                  placeholder="Enter your email"
                />
              </div>

              <button
                type="submit"
                disabled={isSavingProfile}
                className="btn-primary flex items-center gap-2"
              >
                {isSavingProfile ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Check className="w-4 h-4" />
                    Save Changes
                  </>
                )}
              </button>
            </form>
          </div>

          {/* Password Section */}
          <div className="card p-6">
            <div className="flex items-center gap-3 mb-6">
              <Lock className="w-5 h-5 text-electric-blue" />
              <h2 className="heading-section">Change Password</h2>
            </div>

            <form onSubmit={handleChangePassword} className="space-y-4">
              <div>
                <label className="label mb-2 block">Current Password</label>
                <input
                  type="password"
                  value={passwordData.currentPassword}
                  onChange={(e) => setPasswordData({ ...passwordData, currentPassword: e.target.value })}
                  className="input w-full"
                  placeholder="Enter current password"
                />
              </div>

              <div>
                <label className="label mb-2 block">New Password</label>
                <input
                  type="password"
                  value={passwordData.newPassword}
                  onChange={(e) => setPasswordData({ ...passwordData, newPassword: e.target.value })}
                  className="input w-full"
                  placeholder="Enter new password (min 8 characters)"
                />
              </div>

              <div>
                <label className="label mb-2 block">Confirm New Password</label>
                <input
                  type="password"
                  value={passwordData.confirmPassword}
                  onChange={(e) => setPasswordData({ ...passwordData, confirmPassword: e.target.value })}
                  className="input w-full"
                  placeholder="Confirm new password"
                />
              </div>

              <button
                type="submit"
                disabled={isChangingPassword || !passwordData.currentPassword || !passwordData.newPassword}
                className="btn-primary flex items-center gap-2"
              >
                {isChangingPassword ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Changing...
                  </>
                ) : (
                  <>
                    <Lock className="w-4 h-4" />
                    Change Password
                  </>
                )}
              </button>
            </form>
          </div>

          {/* Subscription Section */}
          {subscription && (
            <div className="space-y-6">
              <SubscriptionCard subscription={subscription} onUpgrade={handleUpgrade} />
              <BillingInfo subscription={subscription} />
            </div>
          )}

          {/* Danger Zone */}
          <div className="card p-6 border-status-error/20">
            <div className="flex items-center gap-3 mb-6">
              <AlertTriangle className="w-5 h-5 text-status-error" />
              <h2 className="heading-section text-status-error">Danger Zone</h2>
            </div>

            {!showDeleteConfirm ? (
              <div>
                <p className="text-text-secondary mb-4">
                  Once you delete your account, there is no going back. Please be certain.
                </p>
                <button
                  onClick={() => setShowDeleteConfirm(true)}
                  className="btn-ghost text-status-error border-status-error/50 hover:bg-status-error/10 flex items-center gap-2"
                >
                  <Trash2 className="w-4 h-4" />
                  Delete Account
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="p-4 bg-status-error/10 rounded-lg border border-status-error/20">
                  <p className="text-text-primary font-medium mb-2">
                    Are you absolutely sure?
                  </p>
                  <p className="text-sm text-text-secondary">
                    This action cannot be undone. This will permanently delete your account
                    and remove all your data from our servers.
                  </p>
                </div>

                <div>
                  <label className="label mb-2 block">
                    Type <span className="font-mono font-bold">DELETE</span> to confirm
                  </label>
                  <input
                    type="text"
                    value={deleteConfirmText}
                    onChange={(e) => setDeleteConfirmText(e.target.value)}
                    className="input w-full"
                    placeholder="Type DELETE to confirm"
                  />
                </div>

                <div className="flex gap-3">
                  <button
                    onClick={() => {
                      setShowDeleteConfirm(false);
                      setDeleteConfirmText('');
                    }}
                    className="btn-secondary"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleDeleteAccount}
                    disabled={isDeleting || deleteConfirmText !== 'DELETE'}
                    className="btn-primary bg-status-error hover:bg-status-error/90 flex items-center gap-2"
                  >
                    {isDeleting ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Deleting...
                      </>
                    ) : (
                      <>
                        <Trash2 className="w-4 h-4" />
                        Delete Account
                      </>
                    )}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

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
