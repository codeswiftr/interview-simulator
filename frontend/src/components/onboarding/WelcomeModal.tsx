import { useState, useEffect } from 'react';
import { X, ChevronRight, ChevronLeft, Users } from 'lucide-react';
import { cn } from '../../lib/utils';
import { useFocusTrap } from '../../hooks/useFocusTrap';
import {
  WelcomeIllustration,
  RecordingIllustration,
  GrowthIllustration,
} from './OnboardingIllustrations';

interface WelcomeModalProps {
  isOpen: boolean;
  onClose: () => void;
  onStartInterview: () => void;
  userName?: string;
}

interface OnboardingStep {
  id: string;
  title: string;
  subtitle?: string;
  description: string;
  highlight?: {
    icon?: React.ReactNode;
    text: string;
  };
  illustration: React.ComponentType<{ className?: string; animate?: boolean }>;
}

const steps: OnboardingStep[] = [
  {
    id: 'welcome',
    title: "You've Got This",
    subtitle: 'Interview preparation, reimagined',
    description:
      "Nervous about interviews? You're not alone. We'll help you practice until you feel confident and ready.",
    highlight: {
      icon: <Users size={14} />,
      text: 'Join thousands of engineers who improved their interview skills',
    },
    illustration: WelcomeIllustration,
  },
  {
    id: 'how-it-works',
    title: 'Speak Naturally',
    subtitle: "We'll listen and analyze",
    description:
      'Record your answers just like a real interview. Our AI analyzes your content, structure, and delivery in real-time.',
    highlight: {
      text: 'No typing required - just speak your answers naturally',
    },
    illustration: RecordingIllustration,
  },
  {
    id: 'start',
    title: 'Track Your Growth',
    subtitle: 'Every practice session counts',
    description:
      'Watch your scores improve over time. Get personalized recommendations and focus on areas that need work.',
    highlight: {
      text: 'Most users see improvement within their first 3 sessions',
    },
    illustration: GrowthIllustration,
  },
];

export default function WelcomeModal({
  isOpen,
  onClose,
  onStartInterview,
  userName,
}: WelcomeModalProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [animationKey, setAnimationKey] = useState(0);
  const containerRef = useFocusTrap({
    isActive: isOpen,
    onEscape: onClose,
  });

  // Reset animation on step change
  useEffect(() => {
    setAnimationKey((k) => k + 1);
  }, [currentStep]);

  if (!isOpen) return null;

  const step = steps[currentStep];
  const Illustration = step.illustration;
  const isLastStep = currentStep === steps.length - 1;
  const isFirstStep = currentStep === 0;

  // Format name properly (avoid truncation)
  const displayName = userName && userName.length > 20 ? userName.split(' ')[0] : userName;

  const handleNext = () => {
    if (isLastStep) {
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
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 z-50 animate-fade-in">
      <div
        ref={containerRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="welcome-modal-title"
        className="bg-gradient-to-b from-slate-900 via-slate-800 to-slate-900 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950 rounded-2xl shadow-2xl max-w-lg w-full overflow-hidden animate-scale-in border border-white/5"
      >
        {/* Close button */}
        <button
          onClick={handleSkip}
          className="absolute top-4 right-4 z-10 p-2 text-white/50 hover:text-white/80 transition-colors rounded-lg hover:bg-white/5"
          aria-label="Close onboarding"
        >
          <X size={20} />
        </button>

        {/* Main content area */}
        <div className="relative">
          {/* Ambient glow */}
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-electric-blue/15 via-transparent to-transparent pointer-events-none" />

          {/* Illustration */}
          <div
            key={`illustration-${animationKey}`}
            className="relative h-48 flex items-center justify-center pt-8 onboarding-step-enter"
          >
            <Illustration className="w-40 h-40" animate={true} />
          </div>

          {/* Content */}
          <div
            key={`content-${animationKey}`}
            className="px-8 pb-6 pt-2 text-center onboarding-step-enter"
            style={{ animationDelay: '0.1s' }}
          >
            {/* Step indicator - above title */}
            <div className="flex justify-center gap-2 mb-6">
              {steps.map((_, index) => (
                <button
                  key={index}
                  onClick={() => setCurrentStep(index)}
                  className={cn(
                    'h-1.5 rounded-full transition-all duration-300',
                    index === currentStep
                      ? 'w-8 bg-electric-blue'
                      : 'w-1.5 bg-white/20 hover:bg-white/30'
                  )}
                  aria-label={`Go to step ${index + 1}`}
                />
              ))}
            </div>

            {/* Title */}
            <h2
              id="welcome-modal-title"
              className="text-2xl font-bold text-white mb-1"
            >
              {isFirstStep && displayName
                ? `${displayName}, ${step.title}`
                : step.title}
            </h2>

            {/* Subtitle */}
            {step.subtitle && (
              <p className="text-electric-blue font-medium text-sm mb-3">
                {step.subtitle}
              </p>
            )}

            {/* Description */}
            <p className="text-white/70 text-sm leading-relaxed mb-6 max-w-sm mx-auto">
              {step.description}
            </p>

            {/* Highlight box */}
            {step.highlight && (
              <div className="bg-white/5 border border-white/10 rounded-xl p-4 mb-6">
                <p className="text-electric-blue font-medium text-sm flex items-center justify-center gap-2">
                  {step.highlight.icon}
                  {step.highlight.text}
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="px-8 pb-8 flex items-center gap-3">
          {!isFirstStep && (
            <button
              onClick={handlePrev}
              className="p-3 rounded-xl text-white/60 hover:text-white hover:bg-white/5 transition-all"
              aria-label="Previous step"
            >
              <ChevronLeft size={20} />
            </button>
          )}

          <div className="flex-1" />

          {!isLastStep && (
            <button
              onClick={handleSkip}
              className="px-4 py-2.5 text-sm text-white/50 hover:text-white/70 transition-colors"
            >
              Skip Tour
            </button>
          )}

          <button
            onClick={handleNext}
            className={cn(
              'flex items-center gap-2 px-6 py-3 rounded-xl font-semibold transition-all',
              'bg-electric-blue hover:bg-sky-500 text-white',
              'hover:translate-y-[-1px] hover:shadow-lg hover:shadow-electric-blue/25',
              'active:translate-y-0 active:shadow-none'
            )}
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
    </div>
  );
}
