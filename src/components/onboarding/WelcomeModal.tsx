import { useState } from 'react';
import { X, Mic, BarChart2, MessageSquare, Sparkles, ChevronRight, ChevronLeft } from 'lucide-react';
import { cn } from '../../lib/utils';

interface WelcomeModalProps {
  isOpen: boolean;
  onClose: () => void;
  onStartInterview: () => void;
  userName?: string;
}

const steps = [
  {
    icon: Sparkles,
    title: 'Ace Your Next Behavioral Interview',
    description: 'Engineers who practice with structured AI feedback land offers 2× faster. You\'re about to get that edge — starting with your first 5-minute session.',
    highlight: 'Outcome-focused coaching, not just practice reps.',
  },
  {
    icon: Mic,
    title: 'Record Your Answers',
    description: 'Answer interview questions by recording your voice. Speak naturally as if you\'re in a real interview setting.',
    highlight: 'No typing required - just speak your answers.',
  },
  {
    icon: BarChart2,
    title: 'Get AI Analysis',
    description: 'Our AI analyzes your speech patterns, content quality, and delivery. Receive detailed scores and actionable feedback.',
    highlight: 'Understand your strengths and areas to improve.',
  },
  {
    icon: MessageSquare,
    title: 'Track Your Progress',
    description: 'Complete multiple practice sessions to see your improvement over time. Focus on recommended areas for maximum growth.',
    highlight: 'Get better with each practice session.',
  },
];

export default function WelcomeModal({ isOpen, onClose, onStartInterview, userName }: WelcomeModalProps) {
  const [currentStep, setCurrentStep] = useState(0);

  if (!isOpen) return null;

  const step = steps[currentStep];
  const Icon = step.icon;
  const isLastStep = currentStep === steps.length - 1;
  const isFirstStep = currentStep === 0;

  const handleNext = () => {
    if (isLastStep) {
      // On last step, complete welcome and trigger next onboarding step
      onStartInterview();
    } else {
      setCurrentStep((prev) => prev + 1);
    }
  };

  const handlePrev = () => {
    if (!isFirstStep) {
      setCurrentStep((prev) => prev - 1);
    }
  };

  const handleSkip = () => {
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center p-4 z-50 animate-fade-in">
      <div className="bg-white dark:bg-surface-secondary rounded-2xl shadow-2xl max-w-lg w-full overflow-hidden animate-scale-in">
        {/* Header */}
        <div className="bg-gradient-to-br from-electric-blue to-sky-500 p-6 text-white relative">
          <button
            onClick={handleSkip}
            className="absolute top-4 right-4 text-white/80 hover:text-white transition-colors"
            aria-label="Close"
          >
            <X size={24} />
          </button>

          <div className="w-16 h-16 rounded-2xl bg-white/20 flex items-center justify-center mb-4">
            <Icon size={32} />
          </div>

          <h2 className="text-2xl font-bold mb-2">
            {currentStep === 0 && userName ? `${userName}, let's get you hired` : step.title}
          </h2>

          <p className="text-white/90 text-sm">
            {step.description}
          </p>
        </div>

        {/* Content */}
        <div className="p-6">
          {/* Highlight Box */}
          <div className="bg-electric-blue/5 border border-electric-blue/20 rounded-lg p-4 mb-6">
            <p className="text-sky-600 dark:text-electric-blue font-medium text-sm flex items-center gap-2">
              <Sparkles size={16} />
              {step.highlight}
            </p>
          </div>

          {/* Step Indicators */}
          <div className="flex justify-center gap-2 mb-6">
            {steps.map((_, index) => (
              <button
                key={index}
                onClick={() => setCurrentStep(index)}
                className={cn(
                  'w-2 h-2 rounded-full transition-all duration-200',
                  index === currentStep
                    ? 'w-6 bg-electric-blue'
                    : 'bg-gray-300 hover:bg-gray-400'
                )}
                aria-label={`Go to step ${index + 1}`}
              />
            ))}
          </div>

          {/* Actions */}
          <div className="flex gap-3">
            {!isFirstStep && (
              <button
                onClick={handlePrev}
                className="btn-ghost flex items-center gap-1"
              >
                <ChevronLeft size={18} />
                Back
              </button>
            )}

            <div className="flex-1" />

            {!isLastStep && (
              <button
                onClick={handleSkip}
                className="btn-ghost text-text-tertiary"
              >
                Skip Tour
              </button>
            )}

            <button
              onClick={handleNext}
              className="btn-primary flex items-center gap-1"
            >
              {isLastStep ? (
                <>
                  Start Practicing
                  <ChevronRight size={18} />
                </>
              ) : (
                <>
                  Next
                  <ChevronRight size={18} />
                </>
              )}
            </button>
          </div>
        </div>

        {/* Free Tier Info (on last step) */}
        {isLastStep && (
          <div className="bg-surface-secondary px-6 py-4 border-t border-border-light">
            <p className="text-sm text-text-secondary text-center">
              <span className="font-medium text-text-primary">Free tier:</span> 3 interviews per month.{' '}
              <span className="text-electric-blue cursor-pointer hover:underline">Upgrade to Pro</span> for unlimited access.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
