import { ChevronDown, ChevronUp } from 'lucide-react';
import { useInterview } from '../../contexts/InterviewContext';
import TranscriptionDisplay from './TranscriptionDisplay';

export default function TranscriptionPanel() {
  const {
    submittedResponses,
    showTranscriptionPanel,
    setShowTranscriptionPanel,
  } = useInterview();

  if (submittedResponses.length === 0) {
    return null;
  }

  const hasProcessing = submittedResponses.some(
    r => r.processingStatus !== 'completed' && r.processingStatus !== 'failed'
  );

  return (
    <div className="mt-8 mb-12">
      <button
        onClick={() => setShowTranscriptionPanel(!showTranscriptionPanel)}
        className="w-full flex items-center justify-between p-4 bg-white/60 backdrop-blur-sm rounded-xl border border-white/50 hover:bg-white/80 transition-all shadow-sm"
        aria-expanded={showTranscriptionPanel}
        aria-controls="transcription-panel-content"
      >
        <div className="flex items-center gap-3">
          <span className="text-sm font-semibold text-text-primary">
            Your Transcriptions ({submittedResponses.length})
          </span>
          {hasProcessing && (
            <span className="flex items-center gap-1.5 text-xs bg-electric-blue/10 text-electric-blue px-2.5 py-1 rounded-full font-medium">
              <span className="w-1.5 h-1.5 rounded-full bg-electric-blue animate-pulse" aria-hidden="true"></span>
              Processing
            </span>
          )}
        </div>
        {showTranscriptionPanel ? (
          <ChevronUp size={20} className="text-text-tertiary" />
        ) : (
          <ChevronDown size={20} className="text-text-tertiary" />
        )}
      </button>

      {showTranscriptionPanel && (
        <div id="transcription-panel-content" className="mt-4 space-y-4 animate-slide-up">
          {submittedResponses.map((response) => (
            <TranscriptionDisplay
              key={response.id}
              processingStatus={response.processingStatus}
              transcript={response.transcript}
              processingError={response.processingError}
              questionNumber={response.questionIndex + 1}
            />
          ))}
        </div>
      )}
    </div>
  );
}
