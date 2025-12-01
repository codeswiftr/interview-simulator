import { Briefcase, Clock, Target, Play } from 'lucide-react';
import { cn } from '../../lib/utils';
import type { Question } from '../../types';

interface QuestionCardProps {
  question: Question;
  onPractice: (question: Question) => void;
}

const difficultyColors = {
  easy: 'bg-green-100 text-green-700',
  medium: 'bg-yellow-100 text-yellow-700',
  hard: 'bg-red-100 text-red-700',
};

const categoryLabels = {
  behavioral: 'Behavioral',
  technical: 'Technical',
  system_design: 'System Design',
};

const categoryColors = {
  behavioral: 'bg-blue-100 text-blue-700',
  technical: 'bg-purple-100 text-purple-700',
  system_design: 'bg-orange-100 text-orange-700',
};

export default function QuestionCard({ question, onPractice }: QuestionCardProps) {
  const expectedMinutes = Math.ceil(question.expected_duration_seconds / 60);

  return (
    <div className="card p-6 hover:border-electric-blue transition-colors">
      {/* Header: Category and Difficulty */}
      <div className="flex items-center gap-2 mb-3">
        <span className={cn('badge', categoryColors[question.category])}>
          {categoryLabels[question.category]}
        </span>
        <span className={cn('badge', difficultyColors[question.difficulty])}>
          {question.difficulty.charAt(0).toUpperCase() + question.difficulty.slice(1)}
        </span>
      </div>

      {/* Question Content */}
      <h3 className="heading-card mb-3 line-clamp-2">{question.content}</h3>

      {/* Meta Info */}
      <div className="flex items-center gap-4 text-sm text-text-secondary mb-4">
        <div className="flex items-center gap-1">
          <Clock size={14} />
          <span>{expectedMinutes} min expected</span>
        </div>
        {question.company_tags && question.company_tags.length > 0 && (
          <div className="flex items-center gap-1">
            <Briefcase size={14} />
            <span>{question.company_tags.length} companies</span>
          </div>
        )}
      </div>

      {/* Company Tags */}
      {question.company_tags && question.company_tags.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-4">
          {question.company_tags.slice(0, 5).map((tag) => (
            <span key={tag} className="badge badge-outline text-xs">
              {tag}
            </span>
          ))}
          {question.company_tags.length > 5 && (
            <span className="badge badge-outline text-xs">
              +{question.company_tags.length - 5} more
            </span>
          )}
        </div>
      )}

      {/* Topic Tags */}
      {question.topic_tags && question.topic_tags.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-4">
          {question.topic_tags.slice(0, 4).map((tag) => (
            <span key={tag} className="text-xs text-text-tertiary">
              #{tag}
            </span>
          ))}
        </div>
      )}

      {/* Action Button */}
      <div className="flex items-center justify-between pt-4 border-t border-border-light">
        <div className="flex items-center gap-2 text-sm text-text-tertiary">
          <Target size={14} />
          <span>Quick practice</span>
        </div>
        <button
          onClick={() => onPractice(question)}
          className="btn-primary flex items-center gap-2 py-2 px-4"
        >
          <Play size={16} />
          Practice
        </button>
      </div>
    </div>
  );
}
