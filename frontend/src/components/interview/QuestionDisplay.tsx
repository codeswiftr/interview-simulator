import type { Question } from '../../types';
import { Clock, Tag, BarChart } from 'lucide-react';

interface QuestionDisplayProps {
  question: Question;
  questionNumber: number;
  totalQuestions: number;
}

export default function QuestionDisplay({
  question,
  questionNumber,
  totalQuestions
}: QuestionDisplayProps) {
  const categoryLabels = {
    behavioral: 'Behavioral',
    technical: 'Technical',
    system_design: 'System Design'
  };

  const difficultyColors = {
    easy: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
    medium: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
    hard: 'bg-rose-500/20 text-rose-300 border-rose-500/30'
  };

  return (
    <div className="question-card animate-slide-up relative group">
      {/* Background Glow Effect */}
      <div className="absolute -inset-1 bg-gradient-to-r from-electric-blue/20 to-indigo-500/20 rounded-[1.6rem] blur opacity-0 group-hover:opacity-100 transition duration-1000"></div>
      
      <div className="relative z-10">
        {/* Header with question number and badges */}
        <div className="flex flex-wrap items-start justify-between gap-3 mb-6 sm:mb-8">
          <div className="flex items-center gap-3">
            <span className="px-3 py-1 rounded-full bg-white/10 border border-white/10 text-sm font-medium text-white/80 backdrop-blur-sm">
              Question {questionNumber} <span className="text-white/40 mx-1">/</span> {totalQuestions}
            </span>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <span className={`badge border backdrop-blur-sm ${difficultyColors[question.difficulty]}`}>
              <BarChart className="w-3 h-3 mr-1" />
              {question.difficulty.charAt(0).toUpperCase() + question.difficulty.slice(1)}
            </span>
            <span className="badge bg-electric-blue/10 text-electric-blue border border-electric-blue/20 backdrop-blur-sm">
              <Tag className="w-3 h-3 mr-1" />
              {categoryLabels[question.category]}
            </span>
          </div>
        </div>

        {/* Question Text */}
        <div className="mb-6 sm:mb-8">
          <h2 className="text-lg sm:text-2xl md:text-3xl lg:text-4xl font-bold leading-tight text-white tracking-tight">
            {question.content}
          </h2>
        </div>

        {/* Footer info */}
        <div className="flex items-center gap-2 text-white/50 text-sm font-medium border-t border-white/10 pt-4 sm:pt-6">
          <Clock className="w-4 h-4" />
          <span>Suggested duration: <span className="text-white/80">{Math.ceil(question.expected_duration_seconds / 60)} minutes</span></span>
        </div>
      </div>
    </div>
  );
}
