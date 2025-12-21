import { useState } from 'react';
import { X, Zap, BarChart2, Target, Building2, MessageSquare, Terminal, Server, Layers, CheckCircle2, ChevronDown } from 'lucide-react';
import { useTheme } from '../../contexts/ThemeContext';
import { useFocusTrap } from '../../hooks/useFocusTrap';
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
  const { resolvedTheme } = useTheme();
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
    <div className="fixed inset-0 bg-charcoal/60 backdrop-blur-md z-50 flex items-center justify-center p-4 animate-fade-in">
      <div
        ref={containerRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="new-interview-modal-title"
        className="backdrop-blur-xl max-w-4xl w-full rounded-2xl shadow-2xl border border-white/20 dark:border-white/10 overflow-hidden flex flex-col max-h-[90vh] animate-scale-in"
        style={{ backgroundColor: resolvedTheme === 'dark' ? 'rgba(17, 24, 39, 0.95)' : 'rgba(255, 255, 255, 0.95)' }}
      >

        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-border-light dark:border-white/10">
          <div>
            <h2 id="new-interview-modal-title" className="heading-section text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-electric-blue to-indigo-600">
              New Interview Session
            </h2>
            <p className="body-small text-text-secondary dark:text-gray-400 mt-1">
              Customize your practice environment
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-text-tertiary hover:text-text-primary hover:bg-surface-secondary dark:text-gray-400 dark:hover:text-white dark:hover:bg-white/10 rounded-full transition-colors"
            disabled={isSubmitting}
          >
            <X size={24} />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          <form onSubmit={handleSubmit} className="flex flex-col lg:flex-row gap-8">

            {/* Left Column: Interview Type */}
            <div className="flex-1 space-y-4">
              <label className="text-sm font-semibold text-text-tertiary dark:text-gray-400 uppercase tracking-wider flex items-center gap-2">
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
                          ? `border-electric-blue bg-electric-blue/5 dark:bg-electric-blue/10 shadow-lg shadow-electric-blue/10`
                          : 'border-transparent bg-surface-secondary dark:bg-[#1F2937] hover:bg-surface-tertiary dark:hover:bg-[#334155]'
                        }
                      `}
                    >
                      <div className={`
                        w-10 h-10 rounded-lg flex items-center justify-center mb-3 transition-colors
                        ${isSelected ? 'bg-electric-blue text-white' : type.bg + ' ' + type.color}
                      `}>
                        <Icon size={20} />
                      </div>
                      <div className={`font-semibold mb-1 ${isSelected ? 'text-text-primary dark:text-white' : 'text-text-primary dark:text-gray-200'}`}>{type.label}</div>
                      <div className={`text-xs ${isSelected ? 'text-text-secondary dark:text-gray-300' : 'text-text-secondary dark:text-gray-400'}`}>{type.description}</div>

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
            <div className="flex-1 space-y-8 lg:border-l border-border-light dark:border-white/10 lg:pl-8">

              {/* Target Company */}
              <div className="space-y-3">
                <label className="text-sm font-semibold text-text-tertiary dark:text-gray-400 uppercase tracking-wider">
                  2. Target Company (Optional)
                </label>
                <div className="relative group">
                  <div className="absolute left-3 top-1/2 -translate-y-1/2 text-text-tertiary group-hover:text-electric-blue transition-colors">
                    <Building2 size={18} />
                  </div>
                  <select
                    value={formData.target_company || ''}
                    onChange={(e) => setFormData({ ...formData, target_company: e.target.value || undefined })}
                    className="w-full pl-10 pr-10 py-3 bg-surface-secondary dark:bg-[#1F2937] border border-transparent hover:border-border-medium dark:hover:border-[#334155] focus:border-electric-blue rounded-xl text-text-primary dark:text-white outline-none transition-all appearance-none cursor-pointer"
                  >
                    {targetCompanies.map((company) => (
                      <option key={company.value} value={company.value}>
                        {company.label}
                      </option>
                    ))}
                  </select>
                  <div className="absolute right-3 top-1/2 -translate-y-1/2 text-text-tertiary pointer-events-none">
                    <ChevronDown size={16} />
                  </div>
                </div>
              </div>

              {/* Difficulty */}
              <div className="space-y-3">
                <label className="text-sm font-semibold text-text-tertiary dark:text-gray-400 uppercase tracking-wider">
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
                            ? `border-current ${level.color} bg-current/5`
                            : 'border-transparent bg-surface-secondary dark:bg-[#1F2937] hover:bg-surface-tertiary dark:hover:bg-[#334155] text-text-secondary dark:text-gray-400'
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
                <label className="text-sm font-semibold text-text-tertiary dark:text-gray-400 uppercase tracking-wider">
                  4. Number of Questions
                </label>
                <div className="flex justify-between bg-surface-secondary dark:bg-[#1F2937] p-1 rounded-xl">
                  {questionCounts.map((count) => {
                    const isSelected = formData.question_count === count;
                    return (
                      <button
                        key={count}
                        type="button"
                        onClick={() => setFormData({ ...formData, question_count: count })}
                        className={`
                          flex-1 py-2 rounded-lg text-sm font-bold transition-all duration-200
                          ${isSelected
                            ? 'bg-white dark:bg-[#334155] text-electric-blue dark:text-white shadow-sm scale-105'
                            : 'text-text-secondary dark:text-gray-400 hover:text-text-primary dark:hover:text-gray-200'
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
        <div className="p-6 border-t border-border-light dark:border-white/10 bg-surface-primary dark:bg-[#111827] flex justify-end gap-3">
          <button
            type="button"
            onClick={onClose}
            className="px-6 py-2.5 rounded-xl font-medium text-text-secondary dark:text-gray-400 hover:bg-surface-secondary dark:hover:bg-white/10 transition-colors"
            disabled={isSubmitting}
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            className="px-8 py-2.5 rounded-xl font-bold bg-gradient-to-r from-electric-blue to-indigo-600 text-white shadow-lg shadow-electric-blue/25 hover:shadow-electric-blue/40 hover:-translate-y-0.5 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            disabled={isSubmitting}
          >
            {isSubmitting ? 'Starting...' : 'Start Interview'}
          </button>
        </div>

      </div>
    </div>
  );
}
