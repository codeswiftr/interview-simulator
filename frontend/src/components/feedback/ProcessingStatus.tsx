import { useEffect, useState } from 'react';
import { Loader2, CheckCircle, AlertCircle } from 'lucide-react';
import { feedbackAPI } from '../../lib/api';

interface ProcessingStatusData {
  status_counts: {
    pending: number;
    transcribing: number;
    analyzing: number;
    completed: number;
    failed: number;
  };
  total_responses: number;
  has_session_feedback: boolean;
  all_processed: boolean;
  current_step: string;
}

interface ProcessingStatusProps {
  sessionId: string;
  onComplete?: () => void;
}

const stepLabels: Record<string, string> = {
  idle: 'Waiting to start...',
  transcribing: 'Transcribing audio...',
  analyzing: 'Analyzing speech patterns...',
  generating_feedback: 'Generating AI feedback...',
  complete: 'Processing complete',
  failed: 'Processing failed',
};

export default function ProcessingStatus({ sessionId, onComplete }: ProcessingStatusProps) {
  const [status, setStatus] = useState<ProcessingStatusData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let pollInterval: ReturnType<typeof setInterval> | null = null;
    let isMounted = true;

    const pollStatus = async () => {
      try {
        const response = await feedbackAPI.getSessionStatus(sessionId);
        const data = response.data as ProcessingStatusData;

        if (isMounted) {
          setStatus(data);
          setLoading(false);
          setError(null);

          // Stop polling if all processed or failed
          if (data.all_processed || data.current_step === 'failed' || data.current_step === 'complete') {
            if (pollInterval) {
              clearInterval(pollInterval);
              pollInterval = null;
            }
            if (onComplete && data.current_step === 'complete') {
              onComplete();
            }
          }
        }
      } catch (err: any) {
        if (isMounted) {
          setError(err.response?.data?.message || 'Failed to load processing status');
          setLoading(false);
          if (pollInterval) {
            clearInterval(pollInterval);
            pollInterval = null;
          }
        }
      }
    };

    // Initial poll
    pollStatus();

    // Poll every 2 seconds
    pollInterval = setInterval(pollStatus, 2000);

    return () => {
      isMounted = false;
      if (pollInterval) {
        clearInterval(pollInterval);
      }
    };
  }, [sessionId, onComplete]);

  if (loading && !status) {
    return (
      <div className="card p-6 mb-8">
        <div className="flex items-center gap-3">
          <Loader2 className="w-5 h-5 animate-spin text-electric-blue" />
          <span className="body-default text-text-secondary">Loading processing status...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card p-6 mb-8 border-status-error bg-status-error/10">
        <div className="flex items-center gap-3 text-status-error">
          <AlertCircle className="w-5 h-5" />
          <span className="body-default">{error}</span>
        </div>
      </div>
    );
  }

  if (!status) {
    return null;
  }

  const currentStepLabel = stepLabels[status.current_step] || status.current_step;
  const isComplete = status.current_step === 'complete';
  const isFailed = status.current_step === 'failed';
  const isProcessing = !isComplete && !isFailed && status.total_responses > 0;

  return (
    <div className="card p-6 mb-8">
      <div className="flex items-center justify-between mb-4">
        <h3 className="heading-card">Processing Status</h3>
        {isComplete && (
          <div className="flex items-center gap-2 text-status-success">
            <CheckCircle className="w-5 h-5" />
            <span className="body-small font-medium">Complete</span>
          </div>
        )}
        {isFailed && (
          <div className="flex items-center gap-2 text-status-error">
            <AlertCircle className="w-5 h-5" />
            <span className="body-small font-medium">Failed</span>
          </div>
        )}
        {isProcessing && (
          <div className="flex items-center gap-2 text-electric-blue">
            <Loader2 className="w-5 h-5 animate-spin" />
            <span className="body-small font-medium">Processing</span>
          </div>
        )}
      </div>

      <div className="space-y-3">
        <div>
          <p className="body-default text-text-secondary mb-2">{currentStepLabel}</p>
          {status.total_responses > 0 && (
            <div className="flex items-center gap-4 text-text-tertiary body-small">
              <span>
                {status.status_counts.completed + status.status_counts.failed} / {status.total_responses} responses processed
              </span>
            </div>
          )}
        </div>

        {status.total_responses > 0 && (
          <div className="progress-bar">
            <div
              className="progress-bar-fill bg-electric-blue"
              style={{
                width: `${((status.status_counts.completed + status.status_counts.failed) / status.total_responses) * 100}%`,
              }}
            />
          </div>
        )}
      </div>
    </div>
  );
}

