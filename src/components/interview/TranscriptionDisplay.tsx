import { Loader2, FileText, AlertCircle, CheckCircle, Mic } from 'lucide-react';
import type { ProcessingStatus } from '../../types';

interface TranscriptionDisplayProps {
  processingStatus: ProcessingStatus;
  transcript?: string;
  processingError?: string;
  questionNumber: number;
  className?: string;
}

export default function TranscriptionDisplay({
  processingStatus,
  transcript,
  processingError,
  questionNumber,
  className = ''
}: TranscriptionDisplayProps) {
  const getStatusDisplay = () => {
    switch (processingStatus) {
      case 'pending':
        return (
          <div className="flex items-center gap-2 text-text-tertiary">
            <Loader2 size={16} className="animate-spin" />
            <span>Waiting to process...</span>
          </div>
        );
      case 'transcribing':
        return (
          <div className="flex items-center gap-2 text-electric-blue">
            <Mic size={16} className="animate-pulse" />
            <span>Transcribing your answer...</span>
          </div>
        );
      case 'analyzing':
        return (
          <div className="flex items-center gap-2 text-amber-500">
            <Loader2 size={16} className="animate-spin" />
            <span>Analyzing content...</span>
          </div>
        );
      case 'completed':
        return (
          <div className="flex items-center gap-2 text-status-success">
            <CheckCircle size={16} />
            <span>Transcription complete</span>
          </div>
        );
      case 'failed':
        return (
          <div className="flex items-center gap-2 text-status-error">
            <AlertCircle size={16} />
            <span>Processing failed</span>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className={`bg-surface-secondary rounded-lg p-4 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <FileText size={18} className="text-text-tertiary" />
          <span className="text-sm font-medium text-text-primary">
            Answer {questionNumber} Transcription
          </span>
        </div>
        {getStatusDisplay()}
      </div>

      {/* Transcript Content */}
      {processingStatus === 'completed' && transcript && (
        <div className="mt-3 p-3 bg-white dark:bg-surface-tertiary rounded border border-border-light">
          <p className="text-sm text-text-secondary leading-relaxed whitespace-pre-wrap">
            {transcript}
          </p>
        </div>
      )}

      {/* Error Message */}
      {processingStatus === 'failed' && processingError && (
        <div className="mt-3 p-3 bg-status-error/10 rounded border border-status-error/20">
          <p className="text-sm text-status-error">{processingError}</p>
        </div>
      )}

      {/* Processing Message */}
      {(processingStatus === 'pending' || processingStatus === 'transcribing' || processingStatus === 'analyzing') && (
        <div className="mt-3 p-3 bg-surface-tertiary rounded">
          <p className="text-xs text-text-tertiary text-center">
            Your answer is being processed. The transcription will appear here when ready.
          </p>
        </div>
      )}
    </div>
  );
}
