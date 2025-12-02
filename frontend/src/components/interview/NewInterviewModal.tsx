import { useState } from 'react';
import { X, Zap, BarChart2, Target } from 'lucide-react';
import type { CreateInterviewFormData } from '../../types';

interface NewInterviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: CreateInterviewFormData) => Promise<void>;
}

const interviewTypes = [
  { value: 'behavioral', label: 'Behavioral', description: 'Focus on past experiences and soft skills' },
  { value: 'technical', label: 'Technical', description: 'Programming and problem-solving questions' },
  { value: 'system_design', label: 'System Design', description: 'Architecture and design discussions' },
  { value: 'mixed', label: 'Mixed', description: 'Combination of all question types' },
] as const;

const difficultyLevels = [
  { value: 'easy', label: 'Easy', icon: Zap, color: 'text-green-500', description: 'Great for beginners' },
  { value: 'medium', label: 'Medium', icon: BarChart2, color: 'text-yellow-500', description: 'Standard difficulty' },
  { value: 'hard', label: 'Hard', icon: Target, color: 'text-red-500', description: 'Challenging questions' },
  { value: 'mixed', label: 'Mixed', icon: BarChart2, color: 'text-blue-500', description: 'Variety of difficulties' },
] as const;

const questionCounts = [3, 5, 10];

export default function NewInterviewModal({ isOpen, onClose, onSubmit }: NewInterviewModalProps) {
  const [formData, setFormData] = useState<CreateInterviewFormData>({
    interview_type: 'behavioral',
    question_count: 5,
    difficulty: 'medium',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      await onSubmit(formData);
      onClose();
      // Reset form
      setFormData({
        interview_type: 'behavioral',
        question_count: 5,
        difficulty: 'medium',
      });
    } catch (err: unknown) {
      const apiError = err as { response?: { data?: { message?: string } } };
      setError(apiError.response?.data?.message || 'Failed to create interview session');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-charcoal/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="card max-w-2xl w-full p-8 animate-[scale-in_0.2s_ease-out]">
        <div className="flex items-center justify-between mb-6">
          <h2 className="heading-section">Start New Interview</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-surface-secondary rounded-lg transition-colors"
            disabled={isSubmitting}
          >
            <X size={24} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Interview Type Selection */}
          <div>
            <label className="label mb-3 block">Interview Type</label>
            <div className="grid gap-3">
              {interviewTypes.map((type) => (
                <label
                  key={type.value}
                  className={`card-interactive p-4 flex items-start gap-3 ${
                    formData.interview_type === type.value ? 'border-electric-blue bg-electric-blue/5' : ''
                  }`}
                >
                  <input
                    type="radio"
                    name="interview_type"
                    value={type.value}
                    checked={formData.interview_type === type.value}
                    onChange={(e) => setFormData({ ...formData, interview_type: e.target.value as any })}
                    className="mt-1"
                  />
                  <div className="flex-1">
                    <div className="font-semibold mb-1">{type.label}</div>
                    <div className="body-small text-text-secondary">{type.description}</div>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* Difficulty Selection */}
          <div>
            <label className="label mb-3 block">Difficulty Level</label>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {difficultyLevels.map((level) => {
                const Icon = level.icon;
                return (
                  <button
                    key={level.value}
                    type="button"
                    onClick={() => setFormData({ ...formData, difficulty: level.value as 'easy' | 'medium' | 'hard' | 'mixed' })}
                    className={`card-interactive p-4 text-center ${
                      formData.difficulty === level.value ? 'border-electric-blue bg-electric-blue/5' : ''
                    }`}
                  >
                    <Icon size={24} className={`mx-auto mb-2 ${level.color}`} />
                    <div className="font-semibold text-sm">{level.label}</div>
                    <div className="text-xs text-text-tertiary mt-1">{level.description}</div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Question Count Selection */}
          <div>
            <label className="label mb-3 block">Number of Questions</label>
            <div className="grid grid-cols-3 gap-3">
              {questionCounts.map((count) => (
                <button
                  key={count}
                  type="button"
                  onClick={() => setFormData({ ...formData, question_count: count })}
                  className={`card-interactive p-4 text-center ${
                    formData.question_count === count ? 'border-electric-blue bg-electric-blue/5' : ''
                  }`}
                >
                  <div className="heading-card">{count}</div>
                  <div className="body-small text-text-secondary">questions</div>
                </button>
              ))}
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="p-4 rounded-lg bg-status-error/10 border border-status-error/20 text-status-error">
              {error}
            </div>
          )}

          {/* Submit Buttons */}
          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="btn-secondary flex-1"
              disabled={isSubmitting}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn-primary flex-1"
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Creating...' : 'Start Interview'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
