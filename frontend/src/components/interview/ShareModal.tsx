import { useState, useEffect } from 'react';
import { Share2, Copy, Check, Trash2, Eye, Calendar, ExternalLink, Loader2 } from 'lucide-react';
import { Modal } from '../ui/Modal';
import { Button } from '../ui/Button';
import { Card } from '../ui/Card';
import { interviewsAPI } from '../../lib/api';
import { useToast } from '../../hooks/useToast';

interface ShareLink {
  id: string;
  interview_id: string;
  token: string;
  expires_at: string;
  view_count: number;
  created_at: string;
  share_url: string | null;
}

interface ShareModalProps {
  isOpen: boolean;
  onClose: () => void;
  interviewId: string;
}

export function ShareModal({ isOpen, onClose, interviewId }: ShareModalProps) {
  const [shares, setShares] = useState<ShareLink[]>([]);
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [copiedToken, setCopiedToken] = useState<string | null>(null);
  const { success, error: showError } = useToast();

  // Load existing shares when modal opens
  useEffect(() => {
    if (isOpen) {
      loadShares();
    }
  }, [isOpen, interviewId]);

  const loadShares = async () => {
    try {
      setLoading(true);
      const response = await interviewsAPI.getShares(interviewId);
      setShares(response.data);
    } catch (error) {
      console.error('Error loading shares:', error);
      showError('Failed to load share links');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateShare = async () => {
    try {
      setCreating(true);
      const response = await interviewsAPI.createShare(interviewId);
      setShares([response.data, ...shares]);
      success('Share link created successfully');
    } catch (error) {
      console.error('Error creating share:', error);
      showError('Failed to create share link');
    } finally {
      setCreating(false);
    }
  };

  const handleCopyLink = async (token: string) => {
    const shareUrl = `${window.location.origin}/shared/${token}`;
    try {
      await navigator.clipboard.writeText(shareUrl);
      setCopiedToken(token);
      success('Link copied to clipboard');
      setTimeout(() => setCopiedToken(null), 2000);
    } catch (error) {
      console.error('Error copying to clipboard:', error);
      showError('Failed to copy link');
    }
  };

  const handleRevokeShare = async (shareId: string) => {
    if (!confirm('Are you sure you want to revoke this share link? It will no longer be accessible.')) {
      return;
    }

    try {
      await interviewsAPI.revokeShare(shareId);
      setShares(shares.filter(s => s.id !== shareId));
      success('Share link revoked');
    } catch (error) {
      console.error('Error revoking share:', error);
      showError('Failed to revoke share link');
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const isExpired = (expiresAt: string) => {
    return new Date(expiresAt) < new Date();
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Share Interview Results"
      size="lg"
    >
      <div className="space-y-6">
        {/* Description */}
        <p className="text-text-secondary text-sm">
          Create a shareable link to your interview results. Links expire after 7 days and can be revoked at any time.
        </p>

        {/* Create New Share Button */}
        <div className="flex justify-center">
          <Button
            variant="primary"
            onClick={handleCreateShare}
            disabled={creating}
            leftIcon={creating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Share2 className="w-4 h-4" />}
          >
            {creating ? 'Creating Link...' : 'Create New Share Link'}
          </Button>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-8 h-8 animate-spin text-electric-blue" />
          </div>
        )}

        {/* Existing Shares */}
        {!loading && shares.length > 0 && (
          <div className="space-y-4">
            <h3 className="font-semibold text-text-primary">Active Share Links</h3>
            <div className="space-y-3">
              {shares.map((share) => {
                const expired = isExpired(share.expires_at);
                const shareUrl = `${window.location.origin}/shared/${share.token}`;

                return (
                  <Card
                    key={share.id}
                    className={`p-4 ${expired ? 'opacity-60 bg-surface-tertiary' : ''}`}
                  >
                    <div className="space-y-3">
                      {/* Header with status */}
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Share2 className="w-4 h-4 text-electric-blue" />
                          <span className="text-sm font-medium text-text-primary">
                            {expired ? 'Expired' : 'Active'}
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          <div className="flex items-center gap-1 text-xs text-text-secondary">
                            <Eye className="w-3 h-3" />
                            <span>{share.view_count} views</span>
                          </div>
                        </div>
                      </div>

                      {/* Share URL */}
                      <div className="flex items-center gap-2">
                        <input
                          type="text"
                          readOnly
                          value={shareUrl}
                          className="flex-1 px-3 py-2 bg-surface-secondary text-text-secondary text-sm rounded-lg border border-border-light focus:outline-none"
                        />
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => handleCopyLink(share.token)}
                          leftIcon={
                            copiedToken === share.token
                              ? <Check className="w-4 h-4" />
                              : <Copy className="w-4 h-4" />
                          }
                        >
                          {copiedToken === share.token ? 'Copied' : 'Copy'}
                        </Button>
                      </div>

                      {/* Metadata */}
                      <div className="flex items-center justify-between text-xs text-text-secondary">
                        <div className="flex items-center gap-1">
                          <Calendar className="w-3 h-3" />
                          <span>Expires: {formatDate(share.expires_at)}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <a
                            href={shareUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 text-electric-blue hover:underline"
                          >
                            <ExternalLink className="w-3 h-3" />
                            <span>Preview</span>
                          </a>
                          <button
                            onClick={() => handleRevokeShare(share.id)}
                            className="inline-flex items-center gap-1 text-status-error hover:underline"
                          >
                            <Trash2 className="w-3 h-3" />
                            <span>Revoke</span>
                          </button>
                        </div>
                      </div>
                    </div>
                  </Card>
                );
              })}
            </div>
          </div>
        )}

        {/* Empty State */}
        {!loading && shares.length === 0 && (
          <div className="text-center py-8">
            <Share2 className="w-12 h-12 text-text-tertiary mx-auto mb-3 opacity-50" />
            <p className="text-text-secondary text-sm">
              No share links yet. Create one to share your interview results.
            </p>
          </div>
        )}
      </div>
    </Modal>
  );
}
