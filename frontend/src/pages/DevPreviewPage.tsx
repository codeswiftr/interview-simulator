/**
 * DevPreviewPage - Development-only page for previewing components
 * This page is only available in development mode.
 */
import { useState } from 'react';
import RecordingDeck from '../components/interview/RecordingDeck';
import QuestionDisplay from '../components/interview/QuestionDisplay';
import type { Question } from '../types';

// Mock data for preview
const mockQuestion: Question = {
  id: 'preview-question-1',
  content: 'Tell me about a time when you had to work with a difficult team member. How did you handle the situation?',
  category: 'behavioral',
  difficulty: 'medium',
  expected_duration_seconds: 180,
  is_active: true,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
};

export default function DevPreviewPage() {
  const [recordingState, setRecordingState] = useState<'idle' | 'recording' | 'paused'>('idle');
  const [duration, setDuration] = useState(0);
  const [showCoach, setShowCoach] = useState(true);

  // Only available in development
  if (import.meta.env.PROD) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p>This page is only available in development mode.</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-surface-primary">
      {/* Controls */}
      <div className="fixed top-0 right-0 z-[100] bg-black/80 text-white p-4 rounded-bl-lg text-sm space-y-2">
        <h3 className="font-bold mb-2">Dev Controls</h3>
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={showCoach}
            onChange={(e) => setShowCoach(e.target.checked)}
          />
          Show Coach
        </label>
        <div className="flex gap-2">
          <button
            onClick={() => setRecordingState('idle')}
            className={`px-2 py-1 rounded ${recordingState === 'idle' ? 'bg-blue-500' : 'bg-gray-600'}`}
          >
            Idle
          </button>
          <button
            onClick={() => setRecordingState('recording')}
            className={`px-2 py-1 rounded ${recordingState === 'recording' ? 'bg-red-500' : 'bg-gray-600'}`}
          >
            Recording
          </button>
          <button
            onClick={() => setRecordingState('paused')}
            className={`px-2 py-1 rounded ${recordingState === 'paused' ? 'bg-yellow-500' : 'bg-gray-600'}`}
          >
            Paused
          </button>
        </div>
        <div>
          <label>Duration: {duration}s</label>
          <input
            type="range"
            min={0}
            max={300}
            value={duration}
            onChange={(e) => setDuration(Number(e.target.value))}
            className="w-full"
          />
        </div>
      </div>

      {/* Mock Header */}
      <header className="bg-white/90 dark:bg-surface-dark/90 backdrop-blur-xl border-b border-border-light dark:border-white/5 sticky top-0 z-50 shadow-sm">
        <div className="container mx-auto px-4 sm:px-6">
          <div className="flex items-center justify-between h-14 sm:h-16">
            {/* Timer - Compact */}
            <div className="flex items-center gap-2 sm:gap-3 min-w-[120px] sm:min-w-[140px]">
              <span className="text-lg sm:text-xl font-mono font-bold text-text-primary tabular-nums">
                {Math.floor(duration / 60)}:{(duration % 60).toString().padStart(2, '0')}
              </span>
            </div>

            {/* Progress - Unified design */}
            <div className="flex-1 max-w-[200px] sm:max-w-xs mx-3 sm:mx-8">
              <div className="flex items-center justify-between text-[10px] sm:text-xs font-medium text-text-tertiary mb-1 sm:mb-1.5 uppercase tracking-wider">
                <span>Progress</span>
                <span className="tabular-nums">50%</span>
              </div>
              <div className="h-1.5 sm:h-2 bg-surface-tertiary dark:bg-white/5 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-electric-blue to-indigo-500 transition-all duration-700 ease-out rounded-full"
                  style={{ width: '50%' }}
                />
              </div>
            </div>

            {/* Controls */}
            <div className="flex items-center gap-1.5 sm:gap-3">
              <button
                onClick={() => setShowCoach(!showCoach)}
                className={`p-2 sm:p-2.5 rounded-lg transition-all min-w-[44px] min-h-[44px] flex items-center justify-center ${
                  showCoach
                    ? 'bg-electric-blue/15 text-electric-blue ring-2 ring-electric-blue/30'
                    : 'text-text-tertiary hover:text-text-secondary hover:bg-surface-secondary'
                }`}
              >
                <svg className="w-[18px] h-[18px]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
              </button>
              <button className="p-2 sm:p-2.5 rounded-lg text-text-tertiary hover:text-status-error hover:bg-status-error/10 transition-all min-w-[44px] min-h-[44px] flex items-center justify-center gap-2">
                <svg className="w-[18px] h-[18px]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
                <span className="hidden sm:inline text-sm font-medium">Exit</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 container mx-auto px-6 py-8 max-w-4xl flex flex-col justify-center min-h-[calc(100vh-80px)]">
        {/* Question Display */}
        <div className="mb-12">
          <QuestionDisplay
            question={mockQuestion}
            questionNumber={1}
            totalQuestions={3}
          />
        </div>

        {/* Recording Section */}
        <div className="relative z-20">
          <RecordingDeck
            isRecording={recordingState === 'recording'}
            recordingState={recordingState}
            duration={duration}
            mediaStream={null}
            onStart={() => setRecordingState('recording')}
            onStop={() => setRecordingState('idle')}
            onPause={() => setRecordingState('paused')}
            onResume={() => setRecordingState('recording')}
            onCancel={() => setRecordingState('idle')}
            onConfirm={() => setRecordingState('idle')}
            onSkip={() => console.log('Skip question clicked')}
            disabled={false}
          />

          {/* Skip Question - Desktop only (mobile is inside RecordingDeck) */}
          <div className="mt-6 hidden sm:flex justify-center">
            <button className="btn-ghost flex items-center justify-center gap-2 text-text-tertiary hover:text-text-secondary">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 5l7 7-7 7M5 5l7 7-7 7" />
              </svg>
              Skip Question
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
