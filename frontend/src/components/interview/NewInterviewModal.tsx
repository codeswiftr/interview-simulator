import { useState } from 'react';
import { X } from 'lucide-react';
import type { CreateInterviewFormData } from '../../types';

interface NewInterviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: CreateInterviewFormData) => Promise<void>;
}

const categories = [
  { value: 'behavioral', label: 'Behavioral', description: 'Focus on past experiences and soft skills' },
  { value: 'technical', label: 'Technical', description: 'Programming and problem-solving questions' },
  { value: 'system_design', label: 'System Design', description: 'Architecture and design discussions' },
] as const;

const difficulties = [
  { value: 'easy', label: 'Easy', description: 'Entry-level questions' },
  { value: 'medium', label: 'Medium', description: 'Mid-level complexity' },
  { value: 'hard', label: 'Hard', description: 'Advanced topics' },
] as const;

const questionCounts = [5, 10, 15];

export default function NewInterviewModal({ isOpen, onClose, onSubmit }: NewInterviewModalProps) {
  const [formData, setFormData] = useState<CreateInterviewFormData>({
    category: 'behavioral',
    difficulty: 'medium',
    question_count: 5,
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
        category: 'behavioral',
        difficulty: 'medium',
        question_count: 5,
      });
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to create interview session');
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
          {/* Category Selection */}
          <div>
            <label className="label mb-3 block">Interview Type</label>
            <div className="grid gap-3">
              {categories.map((cat) => (
                <label
                  key={cat.value}
                  className={`card-interactive p-4 flex items-start gap-3 ${
                    formData.category === cat.value ? 'border-electric-blue bg-electric-blue/5' : ''
                  }`}
                >
                  <input
                    type="radio"
                    name="category"
                    value={cat.value}
                    checked={formData.category === cat.value}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value as any })}
                    className="mt-1"
                  />
                  <div className="flex-1">
                    <div className="font-semibold mb-1">{cat.label}</div>
                    <div className="body-small text-text-secondary">{cat.description}</div>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* Difficulty Selection */}
          <div>
            <label className="label mb-3 block">Difficulty Level</label>
            <div className="grid grid-cols-3 gap-3">
              {difficulties.map((diff) => (
                <label
                  key={diff.value}
                  className={`card-interactive p-4 text-center ${
                    formData.difficulty === diff.value ? 'border-electric-blue bg-electric-blue/5' : ''
                  }`}
                >
                  <input
                    type="radio"
                    name="difficulty"
                    value={diff.value}
                    checked={formData.difficulty === diff.value}
                    onChange={(e) => setFormData({ ...formData, difficulty: e.target.value as any })}
                    className="sr-only"
                  />
                  <div className="font-semibold mb-1">{diff.label}</div>
                  <div className="body-small text-text-secondary">{diff.description}</div>
                </label>
              ))}
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
