import { useState } from 'react';
import { X, Zap, BarChart2, Target, Building2, MessageSquare, Terminal, Server, Layers, CheckCircle2, ChevronDown } from 'lucide-react';
import { useFocusTrap } from '../../hooks/useFocusTrap';
import { Card } from '../ui/Card';
import type { CreateInterviewFormData } from '../../types';

interface NewInterviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: CreateInterviewFormData) => Promise<void>;
}

const interviewTypes = [
  { value: 'behavioral', label: 'Behavioral', icon: MessageSquare, color: 'text-purple-500', bg: 'bg-purple-500/10', border: 'border-purple-500/20', description: 'Soft skills & experience' },
  { value: 'technical', label: 'Technical', icon: Terminal, color: 'text-emerald-500', bg: 'bg-emerald-500/10', border: 'border-emerald-500/20', description: 'Coding & algorithms' },
  { value: 'system_design', label: 'System Design', icon: Server, color: 'text-orange-500', bg: 'bg-orange-500/10', border: 'border-orange-500/20', description: 'Architecture & scale' },
  { value: 'mixed', label: 'Mixed', icon: Layers, color: 'text-blue-500', bg: 'bg-blue-500/10', border: 'border-blue-500/20', description: 'All question types' },
] as const;

const targetCompanies = [
  { value: '', label: 'Any Company' },
  { value: 'google', label: 'Google' },
  { value: 'amazon', label: 'Amazon' },
  { value: 'meta', label: 'Meta' },
  { value: 'microsoft', label: 'Microsoft' },
  { value: 'apple', label: 'Apple' },
  { value: 'netflix', label: 'Netflix' },
  { value: 'stripe', label: 'Stripe' },
  { value: 'uber', label: 'Uber' },
  { value: 'airbnb', label: 'Airbnb' },
  { value: 'linkedin', label: 'LinkedIn' },
] as const;

const difficultyLevels = [
  { value: 'easy', label: 'Easy', icon: Zap, color: 'text-emerald-500', bg: 'hover:bg-emerald-500/10', border: 'hover:border-emerald-500/50', description: 'Beginner' },
  { value: 'medium', label: 'Medium', icon: BarChart2, color: 'text-amber-500', bg: 'hover:bg-amber-500/10', border: 'hover:border-amber-500/50', description: 'Standard' },
  { value: 'hard', label: 'Hard', icon: Target, color: 'text-rose-500', bg: 'hover:bg-rose-500/10', border: 'hover:border-rose-500/50', description: 'Expert' },
  { value: 'mixed', label: 'Mixed', icon: Layers, color: 'text-blue-500', bg: 'hover:bg-blue-500/10', border: 'hover:border-blue-500/50', description: 'Varied' },
] as const;

const questionCounts = [1, 2, 3, 5, 10];

export default function NewInterviewModal({ isOpen, onClose, onSubmit }: NewInterviewModalProps) {
  const [formData, setFormData] = useState<CreateInterviewFormData>({
    interview_type: 'behavioral',
    question_count: 2,
    difficulty: 'medium',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const containerRef = useFocusTrap({
    isActive: isOpen,
    onEscape: isSubmitting ? undefined : onClose,
  });

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      await onSubmit(formData);
      onClose();
      // Reset form after a delay to allow animation to finish
      setTimeout(() => {
        setFormData({
          interview_type: 'behavioral',
          question_count: 2,
          difficulty: 'medium',
        });
      }, 300);
    } catch (err: unknown) {
      const apiError = err as { response?: { data?: { message?: string } } };
      setError(apiError.response?.data?.message || 'Failed to create interview session');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-fade-in">
      <Card
        ref={containerRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="new-interview-modal-title"
        variant="elevated"
        className="max-w-4xl w-full overflow-hidden flex flex-col max-h-[90vh] animate-scale-in"
      >

        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-[hsl(var(--border))]">
          <div>
            <h2 id="new-interview-modal-title" className="heading-section text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-electric-blue to-indigo-600 dark:from-electric-blue dark:to-indigo-400">
              New Interview Session
            </h2>
            <p className="body-small text-text-secondary mt-1">
              Customize your practice environment
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-text-tertiary hover:text-text-primary hover:bg-[hsl(var(--muted))] rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-electric-blue focus:ring-offset-2"
            disabled={isSubmitting}
            aria-label="Close modal"
          >
            <X size={24} />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          <form id="new-interview-form" onSubmit={handleSubmit} className="flex flex-col lg:flex-row gap-8">

            {/* Left Column: Interview Type */}
            <div className="flex-1 space-y-4">
              <label className="text-sm font-semibold text-text-tertiary dark:text-text-secondary uppercase tracking-wider flex items-center gap-2">
                1. Select Interview Type
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {interviewTypes.map((type) => {
                  const Icon = type.icon;
                  const isSelected = formData.interview_type === type.value;
                  return (
                    <button
                      key={type.value}
                      type="button"
                      onClick={() => setFormData({ ...formData, interview_type: type.value as CreateInterviewFormData['interview_type'] })}
                      className={`
                        relative group p-4 rounded-xl text-left border-2 transition-all duration-200
                        ${isSelected
                          ? `border-electric-blue bg-electric-blue/5 dark:bg-electric-blue/10 shadow-md shadow-electric-blue/10`
                          : 'border-transparent bg-[hsl(var(--muted))] hover:bg-[hsl(var(--muted))]/80 hover:border-[hsl(var(--border))]'
                        }
                      `}
                    >
                      <div className={`
                        w-10 h-10 rounded-lg flex items-center justify-center mb-3 transition-colors
                        ${isSelected ? 'bg-electric-blue text-white' : type.bg + ' ' + type.color}
                      `}>
                        <Icon size={20} />
                      </div>
                      <div className={`font-semibold mb-1 ${isSelected ? 'text-text-primary dark:text-white' : 'text-text-primary dark:text-text-inverse'}`}>{type.label}</div>
                      <div className={`text-xs ${isSelected ? 'text-text-secondary dark:text-text-tertiary' : 'text-text-secondary dark:text-text-secondary'}`}>{type.description}</div>

                      {isSelected && (
                        <div className="absolute top-3 right-3 text-electric-blue animate-scale-in">
                          <CheckCircle2 size={18} fill="currentColor" className="text-white" />
                        </div>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Right Column: Configuration */}
            <div className="flex-1 space-y-8 lg:border-l border-[hsl(var(--border))] lg:pl-8">

              {/* Target Company */}
              <div className="space-y-3">
                <label className="text-sm font-semibold text-text-tertiary dark:text-text-secondary uppercase tracking-wider">
                  2. Target Company (Optional)
                </label>
                <div className="relative group">
                  <div className="absolute left-3 top-1/2 -translate-y-1/2 text-text-tertiary dark:text-text-secondary group-hover:text-electric-blue transition-colors">
                    <Building2 size={18} />
                  </div>
                  <select
                    value={formData.target_company || ''}
                    onChange={(e) => setFormData({ ...formData, target_company: e.target.value || undefined })}
                    className="w-full pl-10 pr-10 py-3 bg-[hsl(var(--muted))] border border-transparent hover:border-[hsl(var(--border))] focus:border-electric-blue focus:ring-2 focus:ring-electric-blue focus:ring-offset-1 rounded-xl text-text-primary outline-none transition-all appearance-none cursor-pointer"
                  >
                    {targetCompanies.map((company) => (
                      <option key={company.value} value={company.value}>
                        {company.label}
                      </option>
                    ))}
                  </select>
                  <div className="absolute right-3 top-1/2 -translate-y-1/2 text-text-tertiary dark:text-text-secondary pointer-events-none">
                    <ChevronDown size={16} />
                  </div>
                </div>
              </div>

              {/* Difficulty */}
              <div className="space-y-3">
                <label className="text-sm font-semibold text-text-tertiary dark:text-text-secondary uppercase tracking-wider">
                  3. Difficulty Level
                </label>
                <div className="grid grid-cols-4 gap-2">
                  {difficultyLevels.map((level) => {
                    const isSelected = formData.difficulty === level.value;
                    const Icon = level.icon;
                    return (
                      <button
                        key={level.value}
                        type="button"
                        onClick={() => setFormData({ ...formData, difficulty: level.value as CreateInterviewFormData['difficulty'] })}
                        className={`
                          flex flex-col items-center justify-center p-3 rounded-xl border-2 transition-all duration-200
                          ${isSelected
                            ? `border-current ${level.color} bg-current/5 dark:bg-current/10`
                            : 'border-transparent bg-[hsl(var(--muted))] hover:bg-[hsl(var(--muted))]/80 text-text-secondary hover:text-text-primary'
                          }
                        `}
                      >
                        <Icon size={20} className="mb-1" />
                        <span className="text-xs font-semibold">{level.label}</span>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Question Count */}
              <div className="space-y-3">
                <label className="text-sm font-semibold text-text-tertiary dark:text-text-secondary uppercase tracking-wider">
                  4. Number of Questions
                </label>
                <div className="flex justify-between bg-[hsl(var(--muted))] p-1 rounded-xl gap-1">
                  {questionCounts.map((count) => {
                    const isSelected = formData.question_count === count;
                    return (
                      <button
                        key={count}
                        type="button"
                        onClick={() => setFormData({ ...formData, question_count: count })}
                        className={`
                          flex-1 py-2.5 rounded-lg text-sm font-bold transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-electric-blue focus:ring-offset-1
                          ${isSelected
                            ? 'bg-[hsl(var(--card))] text-electric-blue shadow-sm scale-105'
                            : 'text-text-secondary hover:text-text-primary'
                          }
                        `}
                      >
                        {count}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Error Message */}
              {error && (
                <div className="p-3 rounded-lg bg-status-error/10 border border-status-error/20 text-status-error text-sm animate-fade-in">
                  {error}
                </div>
              )}

            </div>
          </form>
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-[hsl(var(--border))] flex justify-end gap-3">
          <button
            type="button"
            onClick={onClose}
            className="btn-secondary"
            disabled={isSubmitting}
          >
            Cancel
          </button>
          <button
            type="submit"
            form="new-interview-form"
            onClick={handleSubmit}
            className="btn-primary"
            disabled={isSubmitting}
          >
            {isSubmitting ? 'Starting...' : 'Start Interview'}
          </button>
        </div>

      </Card>
    </div>
  );
}
