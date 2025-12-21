import { useState, useEffect, useMemo } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { ArrowLeft, Settings as SettingsIcon, Loader2, User, Lock, Trash2, AlertTriangle, Check, Palette, Volume2, Calendar, Target } from 'lucide-react';
import { subscriptionsAPI, userAPI, authAPI } from '../lib/api';
import { useToast } from '../hooks/useToast';
import { useAuth } from '../hooks/useAuth';
import { useTheme } from '../contexts/ThemeContext';
import { Card } from '../components/ui/Card';
import SubscriptionCard from '../components/subscription/SubscriptionCard';
import BillingInfo from '../components/subscription/BillingInfo';
import UpgradeModal from '../components/subscription/UpgradeModal';
import { useVoicePreferences } from '../hooks/useVoicePreferences';
import { useSpeechSynthesis } from '../hooks/useSpeechSynthesis';
import VoiceSettingsPanel from '../components/settings/VoiceSettingsPanel';
import type { SubscriptionStatus, ExperienceLevel } from '../types';

export default function SettingsPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const toast = useToast();
  const { user, refreshUser } = useAuth();
  const { theme, setTheme } = useTheme();
  const { settings: voiceSettings, updateSettings: updateVoiceSettings, resetSettings: resetVoiceSettings } = useVoicePreferences();
  const {
    speak,
    stop,
    voices,
    setVoice,
    setRate,
    setPitch,
    setVolume,
    isSupported: isSpeechSupported,
  } = useSpeechSynthesis({
    defaultRate: voiceSettings.rate,
    defaultPitch: voiceSettings.pitch,
    defaultVolume: voiceSettings.volume,
    defaultVoiceName: voiceSettings.voiceName || undefined,
  });

  const [subscription, setSubscription] = useState<SubscriptionStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showUpgradeModal, setShowUpgradeModal] = useState(false);

  // Profile edit state
  const [profileData, setProfileData] = useState<{
    full_name: string;
    email: string;
    experience_level: ExperienceLevel;
  }>({
    full_name: '',
    email: '',
    experience_level: 'mid',
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

  // Sync speech hook with persisted voice preferences when they change
  useEffect(() => {
    setRate(voiceSettings.rate);
    setPitch(voiceSettings.pitch);
    setVolume(voiceSettings.volume);

    if (voiceSettings.voiceName && voices.length > 0) {
      const match = voices.find((v) => v.name === voiceSettings.voiceName);
      if (match) {
        setVoice(match);
      }
    }
  }, [voiceSettings.pitch, voiceSettings.rate, voiceSettings.voiceName, voiceSettings.volume, setPitch, setRate, setVoice, setVolume, voices]);

  const handleTestVoice = () => {
    if (!isSpeechSupported || !voiceSettings.enabled) return;
    stop();
    const sample = 'Hi! I am your interview mentor. Let us prepare together.';
    speak(sample);
  };

  const voiceSummary = useMemo(() => {
    const name = voiceSettings.voiceName || 'System default';
    return `${name} • ${voiceSettings.rate.toFixed(2)}x • pitch ${voiceSettings.pitch.toFixed(2)} • volume ${voiceSettings.volume.toFixed(2)}`;
  }, [voiceSettings.pitch, voiceSettings.rate, voiceSettings.voiceName, voiceSettings.volume]);

  useEffect(() => {
    loadSubscription();
  }, []);

  useEffect(() => {
    if (user) {
      setProfileData({
        full_name: user.full_name || '',
        email: user.email || '',
        experience_level: user.experience_level || 'mid',
      });
    }
  }, [user]);

  // Handle Stripe redirect query params (run only once on mount)
  useEffect(() => {
    const success = searchParams.get('success');
    const canceled = searchParams.get('canceled');

    if (success === 'true') {
      toast.success('Subscription successful!', 'Welcome to Pro! Your account has been upgraded.');
      // Clear the query params immediately to prevent re-runs
      searchParams.delete('success');
      navigate('/settings', { replace: true });
    } else if (canceled === 'true') {
      toast.info('Checkout canceled', 'Your subscription upgrade was canceled. No charges were made.');
      // Clear the query params immediately to prevent re-runs
      searchParams.delete('canceled');
      navigate('/settings', { replace: true });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

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
          <Card className="p-4 mb-8 border-status-error bg-status-error/10">
            <p className="text-status-error">{error}</p>
          </Card>
        )}

        <div className="space-y-8">
          {/* Account Summary */}
          {user && (
            <Card className="p-8">
              <div className="flex items-center gap-3 mb-8">
                <User className="w-5 h-5 text-electric-blue" />
                <h2 className="heading-section">Account Overview</h2>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 rounded-xl bg-electric-blue/10 flex items-center justify-center shrink-0">
                    <User className="w-6 h-6 text-electric-blue" />
                  </div>
                  <div>
                    <p className="text-sm text-text-tertiary mb-0.5">Name</p>
                    <p className="text-base font-medium text-text-primary">{user.full_name || 'Not set'}</p>
                  </div>
                </div>

                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 rounded-xl bg-electric-blue/10 flex items-center justify-center shrink-0">
                    <Calendar className="w-6 h-6 text-electric-blue" />
                  </div>
                  <div>
                    <p className="text-sm text-text-tertiary mb-0.5">Member since</p>
                    <p className="text-base font-medium text-text-primary">
                      {user.created_at ? new Date(user.created_at).toLocaleDateString('en-US', { month: 'short', year: 'numeric' }) : 'N/A'}
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 rounded-xl bg-electric-blue/10 flex items-center justify-center shrink-0">
                    <Target className="w-6 h-6 text-electric-blue" />
                  </div>
                  <div>
                    <p className="text-sm text-text-tertiary mb-0.5">Total interviews</p>
                    <p className="text-base font-medium text-text-primary">{user.total_interviews || 0}</p>
                  </div>
                </div>

                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 rounded-xl bg-electric-blue/10 flex items-center justify-center shrink-0">
                    <span className="text-base font-bold text-electric-blue">
                      {user.subscription_tier === 'pro' ? '★' : user.subscription_tier === 'team' ? '★★' : '○'}
                    </span>
                  </div>
                  <div>
                    <p className="text-sm text-text-tertiary mb-0.5">Plan</p>
                    <p className="text-base font-medium text-text-primary capitalize">{user.subscription_tier || 'Free'}</p>
                  </div>
                </div>
              </div>
            </Card>
          )}

          {/* Profile Section */}
          <Card className="p-8">
            <div className="flex items-center gap-3 mb-8">
              <User className="w-5 h-5 text-electric-blue" />
              <h2 className="heading-section">Profile</h2>
            </div>

            <form onSubmit={handleSaveProfile} className="space-y-6">
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

              <div>
                <label className="label mb-2 block">Experience Level</label>
                <select
                  value={profileData.experience_level}
                  onChange={(e) => setProfileData({ ...profileData, experience_level: e.target.value as ExperienceLevel })}
                  className="input w-full"
                >
                  <option value="junior">Junior (0-2 years)</option>
                  <option value="mid">Mid-Level (2-5 years)</option>
                  <option value="senior">Senior (5+ years)</option>
                </select>
                <p className="mt-1 text-xs text-text-tertiary">
                  This helps tailor feedback to your experience level
                </p>
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
          </Card>

          {/* Theme Section */}
          <Card className="p-8">
            <div className="flex items-center gap-3 mb-8">
              <Palette className="w-5 h-5 text-electric-blue" />
              <h2 className="heading-section">Appearance</h2>
            </div>

            <div>
              <label className="label mb-4 block">Theme</label>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4" role="group" aria-label="Theme selection">
                <button
                  type="button"
                  onClick={() => setTheme('light')}
                  aria-pressed={theme === 'light'}
                  className={`p-5 rounded-xl border-2 transition-all focus:outline-none focus:ring-2 focus:ring-electric-blue focus:ring-offset-2 bg-[hsl(var(--card))] ${theme === 'light'
                    ? 'border-electric-blue'
                    : 'border-[hsl(var(--border))] hover:border-electric-blue/50'
                    }`}
                >
                  <div className="flex flex-col items-center gap-3">
                    <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-white to-gray-100 border border-gray-200 flex items-center justify-center shadow-sm">
                      <div className="w-7 h-7 rounded-full bg-gradient-to-br from-yellow-300 to-orange-400 shadow-md"></div>
                    </div>
                    <div className="text-center">
                      <span className="font-semibold text-text-primary block">Light</span>
                      <span className="text-xs text-text-tertiary">Bright and clear</span>
                    </div>
                  </div>
                </button>

                <button
                  type="button"
                  onClick={() => setTheme('dark')}
                  aria-pressed={theme === 'dark'}
                  className={`p-5 rounded-xl border-2 transition-all focus:outline-none focus:ring-2 focus:ring-electric-blue focus:ring-offset-2 bg-[hsl(var(--card))] ${theme === 'dark'
                    ? 'border-electric-blue'
                    : 'border-[hsl(var(--border))] hover:border-electric-blue/50'
                    }`}
                >
                  <div className="flex flex-col items-center gap-3">
                    <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-slate-700 to-slate-900 border border-slate-600 flex items-center justify-center shadow-sm">
                      <div className="w-7 h-7 rounded-full bg-gradient-to-br from-blue-400 to-purple-500 shadow-md"></div>
                    </div>
                    <div className="text-center">
                      <span className="font-semibold text-text-primary block">Dark</span>
                      <span className="text-xs text-text-tertiary">Easy on the eyes</span>
                    </div>
                  </div>
                </button>

                <button
                  type="button"
                  onClick={() => setTheme('system')}
                  aria-pressed={theme === 'system'}
                  className={`p-5 rounded-xl border-2 transition-all focus:outline-none focus:ring-2 focus:ring-electric-blue focus:ring-offset-2 bg-[hsl(var(--card))] ${theme === 'system'
                    ? 'border-electric-blue'
                    : 'border-[hsl(var(--border))] hover:border-electric-blue/50'
                    }`}
                >
                  <div className="flex flex-col items-center gap-3">
                    <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-white via-gray-400 to-slate-800 border border-gray-300 flex items-center justify-center shadow-sm">
                      <div className="w-7 h-7 rounded-full bg-gradient-to-br from-electric-blue to-indigo-500 shadow-md"></div>
                    </div>
                    <div className="text-center">
                      <span className="font-semibold text-text-primary block">System</span>
                      <span className="text-xs text-text-tertiary">Auto-adjust</span>
                    </div>
                  </div>
                </button>
              </div>
            </div>
          </Card>

          {/* Voice & Conversation */}
          <Card className="p-8">
            <div className="flex items-center gap-3 mb-8">
              <Volume2 className="w-5 h-5 text-electric-blue" />
              <h2 className="heading-section">Voice & Conversation</h2>
            </div>

            <div className="mb-3 text-sm text-text-secondary">
              Configure the mentor voice used in conversational mode. Settings are stored on this device.
            </div>

            <VoiceSettingsPanel
              settings={voiceSettings}
              voices={voices}
              isSupported={isSpeechSupported}
              onChange={updateVoiceSettings}
              onReset={resetVoiceSettings}
              onTestVoice={handleTestVoice}
            />

            <div className="mt-4 text-xs text-text-tertiary">
              Current: {voiceSummary}
            </div>
          </Card>

          {/* Password Section */}
          <Card className="p-8">
            <div className="flex items-center gap-3 mb-8">
              <Lock className="w-5 h-5 text-electric-blue" />
              <h2 className="heading-section">Change Password</h2>
            </div>

            <form onSubmit={handleChangePassword} className="space-y-6">
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
          </Card>

          {/* Subscription Section */}
          {subscription && (
            <div className="space-y-6">
              <SubscriptionCard subscription={subscription} onUpgrade={handleUpgrade} />
              <BillingInfo subscription={subscription} onSubscriptionChange={loadSubscription} />
            </div>
          )}

          {/* Danger Zone */}
          <Card className="p-8 border-status-error/20">
            <div className="flex items-center gap-3 mb-8">
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
          </Card>
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
