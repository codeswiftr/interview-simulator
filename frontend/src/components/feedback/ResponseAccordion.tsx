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
    if (s >= 80) return 'text-emerald-600 dark:text-emerald-400';
    if (s >= 70) return 'text-green-600 dark:text-green-400';
    if (s >= 60) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-orange-600 dark:text-orange-400';
  };

  return (
    <div className="card overflow-hidden transition-all duration-300 border border-border-light dark:border-white/5 bg-white dark:bg-surface-secondary/40 shadow-sm hover:shadow-md">
      {/* Header */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-6 py-4 flex items-center justify-between hover:bg-surface-secondary/50 dark:hover:bg-white/5 transition-colors group"
      >
        <div className="flex items-start gap-4 flex-1 text-left">
          <span className="flex-shrink-0 w-8 h-8 rounded-full bg-electric-blue/10 dark:bg-electric-blue/20 text-electric-blue dark:text-electric-blue flex items-center justify-center font-semibold text-sm ring-1 ring-electric-blue/20">
            {questionNumber}
          </span>
          <div className="flex-1 min-w-0">
            <h3 className="body-large font-semibold text-[var(--fg-primary)] mb-1 group-hover:text-electric-blue transition-colors">
              {question}
            </h3>
            {score !== undefined && (
              <span className={`body-small font-semibold ${getScoreColor(score)}`}>
                Score: {score}/100
              </span>
            )}
          </div>
        </div>

        <div className={`p-2 rounded-full transition-all duration-300 ${isOpen ? 'bg-electric-blue/10 rotate-180' : 'bg-transparent'}`}>
            <ChevronDown
            className={`w-5 h-5 text-text-secondary dark:text-text-tertiary transition-colors ${
                isOpen ? 'text-electric-blue' : ''
            }`}
            />
        </div>
      </button>

      {/* Content */}
      <div
        className={`transition-[max-height,opacity] duration-300 ease-in-out overflow-hidden ${
          isOpen ? 'max-h-[2000px] opacity-100' : 'max-h-0 opacity-0'
        }`}
      >
        <div className="p-6 space-y-6 bg-surface-secondary/30 dark:bg-[#0F172A] border-t border-border-light dark:border-white/5">
          {/* Audio Player */}
          {audioUrl && (
            <div>
              <h4 className="body-small font-semibold text-text-secondary dark:text-gray-400 uppercase tracking-wide mb-2 flex items-center gap-2">
                <Play className="w-4 h-4" />
                Your Recording
              </h4>
              <div className="bg-white dark:bg-[#1E293B] rounded-xl p-2 border border-border-light dark:border-white/5">
                <AudioPlayer audioUrl={audioUrl} />
              </div>
            </div>
          )}

          {/* Transcript */}
          {transcript && (
            <div>
              <h4 className="body-small font-semibold text-text-secondary dark:text-gray-400 uppercase tracking-wide mb-2">
                Your Response
              </h4>
              <div className="bg-white dark:bg-[#1E293B] rounded-lg p-4 border border-border-light dark:border-white/5 shadow-sm">
                <p className="body-default text-gray-900 dark:text-gray-100 whitespace-pre-wrap leading-relaxed">
                  {transcript}
                </p>
              </div>
            </div>
          )}

          {/* Feedback */}
          <div>
            <h4 className="body-small font-semibold text-text-secondary dark:text-gray-400 uppercase tracking-wide mb-2">
              Feedback
            </h4>
            <div className="bg-electric-blue/5 dark:bg-electric-blue/10 border border-electric-blue/10 dark:border-electric-blue/20 rounded-lg p-4">
              <p className="body-default text-gray-900 dark:text-gray-100 leading-relaxed">{feedback}</p>
            </div>
          </div>

          {/* Suggestions */}
          {suggestions.length > 0 && (
            <div>
              <h4 className="body-small font-semibold text-text-secondary dark:text-gray-400 uppercase tracking-wide mb-3 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4" />
                Areas for Improvement
              </h4>
              <ul className="space-y-2">
                {suggestions.map((suggestion, idx) => (
                  <li key={idx} className="flex items-start gap-3 bg-white dark:bg-[#1E293B] p-3 rounded-lg border border-border-light dark:border-white/10">
                    <CheckCircle className="w-5 h-5 text-status-warning dark:text-amber-500 flex-shrink-0 mt-0.5" />
                    <span className="body-default text-gray-900 dark:text-gray-200 flex-1">
                      {suggestion}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Sample Answer Button */}
          {sampleAnswer && (
            <div className="pt-4 border-t border-border-light dark:border-white/5">
              <button
                onClick={() => setShowSampleModal(true)}
                className="btn-secondary w-full flex items-center justify-center gap-2 hover:bg-white dark:hover:bg-white/5 transition-all"
              >
                <Lightbulb size={18} className="text-yellow-500" />
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
