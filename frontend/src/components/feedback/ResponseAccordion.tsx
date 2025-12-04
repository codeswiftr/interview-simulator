import { useState } from 'react';
import { ChevronDown, CheckCircle, AlertTriangle, Play, Lightbulb } from 'lucide-react';
import AudioPlayer from './AudioPlayer';
import SampleAnswerModal from './SampleAnswerModal';

interface ResponseAccordionProps {
  question: string;
  transcript?: string;
  feedback: string;
  score?: number;
  suggestions: string[];
  questionNumber: number;
  audioUrl?: string;
  sampleAnswer?: string;
}

export default function ResponseAccordion({
  question,
  transcript,
  feedback,
  score,
  suggestions,
  questionNumber,
  audioUrl,
  sampleAnswer,
}: ResponseAccordionProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [showSampleModal, setShowSampleModal] = useState(false);

  const getScoreColor = (s: number): string => {
    if (s >= 80) return 'text-score-excellent';
    if (s >= 70) return 'text-score-good';
    if (s >= 60) return 'text-score-average';
    return 'text-score-needs-work';
  };

  return (
    <div className="card overflow-hidden">
      {/* Header */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-6 py-4 flex items-center justify-between hover:bg-surface-secondary dark:hover:bg-dark-surface-tertiary transition-colors"
      >
        <div className="flex items-start gap-4 flex-1 text-left">
          <span className="flex-shrink-0 w-8 h-8 rounded-full bg-electric-blue/10 text-electric-blue flex items-center justify-center font-semibold text-sm">
            {questionNumber}
          </span>
          <div className="flex-1 min-w-0">
            <h3 className="body-large font-semibold text-text-primary dark:text-dark-text-primary mb-1">
              {question}
            </h3>
            {score !== undefined && (
              <span className={`body-small font-semibold ${getScoreColor(score)}`}>
                Score: {score}/100
              </span>
            )}
          </div>
        </div>

        <ChevronDown
          className={`w-5 h-5 text-text-secondary flex-shrink-0 ml-4 transition-transform ${
            isOpen ? 'transform rotate-180' : ''
          }`}
        />
      </button>

      {/* Content */}
      <div
        className={`transition-all duration-300 ease-in-out overflow-hidden ${
          isOpen ? 'max-h-[2000px] opacity-100' : 'max-h-0 opacity-0'
        }`}
      >
        <div className="px-6 pb-6 space-y-6">
          {/* Audio Player */}
          {audioUrl && (
            <div>
              <h4 className="body-small font-semibold text-text-secondary dark:text-dark-text-secondary uppercase tracking-wide mb-2 flex items-center gap-2">
                <Play className="w-4 h-4" />
                Your Recording
              </h4>
              <AudioPlayer audioUrl={audioUrl} />
            </div>
          )}

          {/* Transcript */}
          {transcript && (
            <div>
              <h4 className="body-small font-semibold text-text-secondary dark:text-dark-text-secondary uppercase tracking-wide mb-2">
                Your Response
              </h4>
              <div className="bg-surface-secondary dark:bg-dark-surface-tertiary rounded-lg p-4">
                <p className="body-default text-text-primary dark:text-dark-text-primary whitespace-pre-wrap">
                  {transcript}
                </p>
              </div>
            </div>
          )}

          {/* Feedback */}
          <div>
            <h4 className="body-small font-semibold text-text-secondary dark:text-dark-text-secondary uppercase tracking-wide mb-2">
              Feedback
            </h4>
            <div className="bg-status-info/5 border border-status-info/20 rounded-lg p-4">
              <p className="body-default text-text-primary dark:text-dark-text-primary">{feedback}</p>
            </div>
          </div>

          {/* Suggestions */}
          {suggestions.length > 0 && (
            <div>
              <h4 className="body-small font-semibold text-text-secondary dark:text-dark-text-secondary uppercase tracking-wide mb-3 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4" />
                Areas for Improvement
              </h4>
              <ul className="space-y-2">
                {suggestions.map((suggestion, idx) => (
                  <li key={idx} className="flex items-start gap-3">
                    <CheckCircle className="w-5 h-5 text-status-warning flex-shrink-0 mt-0.5" />
                    <span className="body-default text-text-primary dark:text-dark-text-primary flex-1">
                      {suggestion}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Sample Answer Button */}
          {sampleAnswer && (
            <div className="pt-4 border-t border-border-light dark:border-dark-border">
              <button
                onClick={() => setShowSampleModal(true)}
                className="btn-secondary w-full flex items-center justify-center gap-2"
              >
                <Lightbulb size={18} />
                View Sample Answer
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Sample Answer Modal */}
      {sampleAnswer && (
        <SampleAnswerModal
          isOpen={showSampleModal}
          onClose={() => setShowSampleModal(false)}
          question={question}
          sampleAnswer={sampleAnswer}
          questionNumber={questionNumber}
        />
      )}
    </div>
  );
}
