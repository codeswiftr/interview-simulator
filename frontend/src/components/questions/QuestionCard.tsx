import { Briefcase, Clock, Play, Sparkles } from 'lucide-react';
import { cn } from '../../lib/utils';
import type { Question } from '../../types';

interface QuestionCardProps {
  question: Question;
  onPractice: (question: Question) => void;
  onPrepare?: (question: Question) => void;
  prepRemaining?: number; // Show remaining preparations for free tier
}

// Dark mode compatible badge colors
const difficultyColors = {
  easy: 'bg-green-500/15 text-green-600 dark:text-green-400',
  medium: 'bg-yellow-500/15 text-yellow-600 dark:text-yellow-400',
  hard: 'bg-red-500/15 text-red-600 dark:text-red-400',
};

const categoryLabels = {
  behavioral: 'Behavioral',
  technical: 'Technical',
  system_design: 'System Design',
};

const categoryColors = {
  behavioral: 'bg-blue-500/15 text-blue-600 dark:text-blue-400',
  technical: 'bg-purple-500/15 text-purple-600 dark:text-purple-400',
  system_design: 'bg-orange-500/15 text-orange-600 dark:text-orange-400',
};

export default function QuestionCard({ question, onPractice, onPrepare, prepRemaining }: QuestionCardProps) {
  const expectedMinutes = Math.ceil(question.expected_duration_seconds / 60);

  return (
    <div className="bg-[hsl(var(--card))] border border-[hsl(var(--border))] rounded-2xl group relative overflow-hidden transition-all duration-300 hover:shadow-lg hover:border-electric-blue/40 hover:-translate-y-0.5 flex flex-col">
      {/* Subtle gradient overlay on hover */}
      <div className="absolute inset-0 bg-gradient-to-br from-electric-blue/0 to-electric-blue/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none" />

      <div className="relative p-4 sm:p-5 flex flex-col flex-1">
        {/* Header: Category, Difficulty, and Time */}
        <div className="flex items-center justify-between gap-2 mb-3">
          <div className="flex items-center gap-1.5 flex-wrap">
            <span className={cn('px-2 py-0.5 rounded-md text-xs font-semibold', categoryColors[question.category])}>
              {categoryLabels[question.category]}
            </span>
            <span className={cn('px-2 py-0.5 rounded-md text-xs font-semibold', difficultyColors[question.difficulty])}>
              {question.difficulty.charAt(0).toUpperCase() + question.difficulty.slice(1)}
            </span>
          </div>
          <div className="flex items-center gap-1 text-xs text-text-tertiary shrink-0">
            <Clock size={12} />
            <span>{expectedMinutes}m</span>
          </div>
        </div>

        {/* Question Content */}
        <h3 className="text-base sm:text-lg font-semibold text-text-primary mb-3 line-clamp-2 group-hover:text-electric-blue transition-colors leading-snug">
          {question.content}
        </h3>

        {/* Company Tags - Compact */}
        {question.company_tags && question.company_tags.length > 0 && (
          <div className="flex items-center gap-1.5 mb-3 flex-wrap">
            <Briefcase size={12} className="text-text-tertiary shrink-0" />
            <div className="flex gap-1 flex-wrap">
              {question.company_tags.slice(0, 3).map((tag) => (
                <span
                  key={tag}
                  className="text-xs text-text-secondary bg-[hsl(var(--muted)/0.5)] px-1.5 py-0.5 rounded"
                >
                  {tag}
                </span>
              ))}
              {question.company_tags.length > 3 && (
                <span className="text-xs text-electric-blue font-medium">
                  +{question.company_tags.length - 3}
                </span>
              )}
            </div>
          </div>
        )}

        {/* Topic Tags - Minimal */}
        {question.topic_tags && question.topic_tags.length > 0 && (
          <div className="flex gap-2 mb-3 flex-wrap">
            {question.topic_tags.slice(0, 3).map((tag) => (
              <span key={tag} className="text-xs text-text-tertiary">
                #{tag.replace(/_/g, '')}
              </span>
            ))}
            {question.topic_tags.length > 3 && (
              <span className="text-xs text-text-tertiary">
                +{question.topic_tags.length - 3}
              </span>
            )}
          </div>
        )}

        {/* Spacer to push buttons to bottom */}
        <div className="flex-1 min-h-2" />

        {/* Action Buttons - Mobile Optimized */}
        <div className="flex items-center gap-2 pt-3 border-t border-[hsl(var(--border))]">
          {onPrepare && (
            <button
              onClick={() => onPrepare(question)}
              className={cn(
                'flex-1 sm:flex-none flex items-center justify-center gap-1.5 py-2.5 px-3 rounded-xl text-sm font-medium transition-all',
                'bg-[hsl(var(--muted)/0.5)] text-text-secondary border border-[hsl(var(--border))]',
                'hover:bg-electric-blue/10 hover:text-electric-blue hover:border-electric-blue/30',
                'active:scale-95',
                prepRemaining === 0 && 'opacity-40 cursor-not-allowed hover:bg-[hsl(var(--muted)/0.5)] hover:text-text-secondary hover:border-[hsl(var(--border))]'
              )}
              disabled={prepRemaining === 0}
              title={
                prepRemaining !== undefined
                  ? `${prepRemaining} free preparations remaining`
                  : 'Prepare Answer'
              }
            >
              <Sparkles size={14} />
              <span>Prepare</span>
              {prepRemaining !== undefined && prepRemaining > 0 && (
                <span className="text-xs bg-electric-blue/20 text-electric-blue px-1.5 py-0.5 rounded-full font-bold">
                  {prepRemaining}
                </span>
              )}
            </button>
          )}
          <button
            onClick={() => onPractice(question)}
            className={cn(
              'flex-1 sm:flex-none flex items-center justify-center gap-1.5 py-2.5 px-4 rounded-xl text-sm font-semibold transition-all',
              'bg-electric-blue text-white',
              'hover:bg-electric-blue/90',
              'active:scale-95'
            )}
          >
            <Play size={14} />
            <span>Practice</span>
          </button>
        </div>
      </div>
    </div>
  );
}
