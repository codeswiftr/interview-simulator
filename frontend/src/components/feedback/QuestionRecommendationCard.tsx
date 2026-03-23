import { ArrowRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Card } from '../ui/Card';
import type { Question } from '../../types';

interface QuestionRecommendationCardProps {
  question: Question;
}

const categoryColors: Record<string, { bg: string; text: string; border: string }> = {
  behavioral: {
    bg: 'bg-blue-500/10 dark:bg-blue-500/20',
    text: 'text-blue-600 dark:text-blue-400',
    border: 'border-blue-500/20 dark:border-blue-500/30',
  },
  technical: {
    bg: 'bg-purple-500/10 dark:bg-purple-500/20',
    text: 'text-purple-600 dark:text-purple-400',
    border: 'border-purple-500/20 dark:border-purple-500/30',
  },
  system_design: {
    bg: 'bg-indigo-500/10 dark:bg-indigo-500/20',
    text: 'text-indigo-600 dark:text-indigo-400',
    border: 'border-indigo-500/20 dark:border-indigo-500/30',
  },
};

const difficultyColors: Record<string, { bg: string; text: string }> = {
  easy: {
    bg: 'bg-emerald-500/10 dark:bg-emerald-500/20',
    text: 'text-emerald-600 dark:text-emerald-400',
  },
  medium: {
    bg: 'bg-amber-500/10 dark:bg-amber-500/20',
    text: 'text-amber-600 dark:text-amber-400',
  },
  hard: {
    bg: 'bg-rose-500/10 dark:bg-rose-500/20',
    text: 'text-rose-600 dark:text-rose-400',
  },
};

const categoryLabels: Record<string, string> = {
  behavioral: 'Behavioral',
  technical: 'Technical',
  system_design: 'System Design',
};

export default function QuestionRecommendationCard({ question }: QuestionRecommendationCardProps) {
  const navigate = useNavigate();

  const categoryColor = categoryColors[question.category] || categoryColors.behavioral;
  const difficultyColor = difficultyColors[question.difficulty] || difficultyColors.medium;

  const handlePractice = () => {
    // Navigate to create a quick practice session with this question
    navigate('/interview', { state: { questionId: question.id } });
  };

  return (
    <Card className="p-5 hover:shadow-lg transition-all hover:scale-[1.02] duration-300 flex flex-col">
      <div className="flex items-start gap-3 mb-3">
        <div className={`px-3 py-1 rounded-full text-xs font-medium border ${categoryColor.bg} ${categoryColor.text} ${categoryColor.border}`}>
          {categoryLabels[question.category] || question.category}
        </div>
        <div className={`px-3 py-1 rounded-full text-xs font-medium ${difficultyColor.bg} ${difficultyColor.text}`}>
          {question.difficulty.charAt(0).toUpperCase() + question.difficulty.slice(1)}
        </div>
      </div>

      <p className="text-sm text-text-primary mb-4 flex-1 line-clamp-3">
        {question.content}
      </p>

      <button
        onClick={handlePractice}
        className="btn-primary w-full inline-flex items-center justify-center gap-2 py-2.5 text-sm font-medium shadow-sm hover:shadow-electric-blue/25 transition-all"
      >
        Practice Now
        <ArrowRight className="w-4 h-4" />
      </button>
    </Card>
  );
}
