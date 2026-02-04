import { describe, it, expect } from 'vitest';
import { render, screen } from '../../../test/utils';
import QuestionDisplay from '../QuestionDisplay';
import type { Question } from '../../../types';

const baseQuestion: Question = {
  id: 'q1',
  content: 'Tell me about a time you led a project.',
  category: 'behavioral',
  difficulty: 'medium',
  expected_duration_seconds: 180,
};

describe('QuestionDisplay', () => {
  it('renders question content and numbering', () => {
    render(
      <QuestionDisplay question={baseQuestion} questionNumber={2} totalQuestions={5} />
    );

    const numbering = screen.getByText((_, element) => {
      if (!element || element.tagName !== 'SPAN') {
        return false;
      }
      return (
        element.classList.contains('rounded-full') &&
        (element.textContent?.includes('Question 2 / 5') ?? false)
      );
    });
    expect(numbering).toBeInTheDocument();
    expect(screen.getByText(baseQuestion.content)).toBeInTheDocument();
  });

  it('renders category and difficulty badges', () => {
    render(
      <QuestionDisplay question={baseQuestion} questionNumber={1} totalQuestions={3} />
    );

    expect(screen.getByText('Behavioral')).toBeInTheDocument();
    expect(screen.getByText('Medium')).toBeInTheDocument();
  });

  it('shows expected duration in minutes', () => {
    render(
      <QuestionDisplay question={baseQuestion} questionNumber={1} totalQuestions={3} />
    );

    expect(screen.getByText(/Suggested duration:/i)).toBeInTheDocument();
    expect(screen.getByText(/3 minutes/)).toBeInTheDocument();
  });
});
