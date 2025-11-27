import type { Question } from '../../types';

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
    easy: 'bg-status-success/10 text-status-success border-status-success/20',
    medium: 'bg-status-warning/10 text-status-warning border-status-warning/20',
    hard: 'bg-status-error/10 text-status-error border-status-error/20'
  };

  return (
    <div className="question-card animate-[slide-up_0.3s_ease-out]">
      {/* Header with question number and badges */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <span className="label text-white/70">
            Question {questionNumber} of {totalQuestions}
          </span>
          <span className={`badge ${difficultyColors[question.difficulty]}`}>
            {question.difficulty.charAt(0).toUpperCase() + question.difficulty.slice(1)}
          </span>
          <span className="badge bg-electric-blue/10 text-electric-blue border-electric-blue/20">
            {categoryLabels[question.category]}
          </span>
        </div>
      </div>

      {/* Question Text */}
      <h2 className="text-3xl font-bold leading-relaxed mb-4">
        {question.question_text}
      </h2>

      {/* Follow-up questions hint */}
      {question.follow_up_questions && question.follow_up_questions.length > 0 && (
        <div className="mt-6 pt-6 border-t border-white/10">
          <p className="text-sm text-white/60 mb-2">
            Be prepared for follow-up questions
          </p>
        </div>
      )}

      {/* Expected duration hint */}
      <div className="mt-4">
        <p className="text-sm text-white/50">
          Suggested duration: {Math.ceil(question.expected_duration_seconds / 60)} minutes
        </p>
      </div>
    </div>
  );
}
