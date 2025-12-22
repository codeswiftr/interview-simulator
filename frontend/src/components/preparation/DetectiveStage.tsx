import { useState, useEffect, useRef } from 'react';
import { Loader2, Mic, MicOff, Volume2, VolumeX, MessageSquare, User, Bot, ChevronRight } from 'lucide-react';
import { usePreparation } from '../../contexts/PreparationContext';
import { useSpeechSynthesis } from '../../hooks/useSpeechSynthesis';
import { useSpeechRecognition } from '../../hooks/useSpeechRecognition';
import { useVoicePreferences } from '../../hooks/useVoicePreferences';
import { cn } from '../../lib/utils';

// Estimated total questions for progress display
const ESTIMATED_QUESTIONS = 5;

interface ConversationMessage {
  id: string;
  role: 'mentor' | 'user';
  text: string;
  timestamp: Date;
  isInterim?: boolean;
}

export default function DetectiveStage() {
  const {
    currentQuestion,
    currentAnswer,
    setCurrentAnswer,
    qnaList,
    isLoading,
    handleSubmitAnswer,
  } = usePreparation();

  // Voice settings
  const { settings: voiceSettings, updateSettings: updateVoiceSettings } = useVoicePreferences();
  const [voiceEnabled, setVoiceEnabled] = useState(voiceSettings.enabled);
  const [isAutoListening, setIsAutoListening] = useState(false);

  // Conversation transcript for display
  const [conversationHistory, setConversationHistory] = useState<ConversationMessage[]>([]);
  const [userInterimText, setUserInterimText] = useState('');
  const conversationEndRef = useRef<HTMLDivElement>(null);

  // TTS for mentor voice
  const tts = useSpeechSynthesis();
  const {
    speak,
    stop: stopSpeaking,
    isSpeaking,
    isSupported: isTTSSupported,
    error: ttsError,
    setVoice,
    setRate,
    setPitch,
    setVolume,
    voices,
  } = tts;

  // STT for user input
  const stt = useSpeechRecognition({
    onResult: (transcript, isFinal) => {
      if (isFinal) {
        // Final result - update the answer field
        const finalText = transcript.trim();
        if (finalText) {
          setCurrentAnswer(finalText);
          // Clear interim after React commits the update to avoid flash of empty
          // Use setTimeout to ensure it runs after the current render cycle
          setTimeout(() => {
            setUserInterimText('');
          }, 0);
        } else {
          // Empty final result - clear interim
          setUserInterimText('');
        }
      } else {
        // Interim result - show live transcription
        // Only update interim if we don't have a final answer yet
        if (!currentAnswer.trim()) {
          setUserInterimText(transcript);
        }
      }
    },
    onError: (error) => {
      console.error('[DetectiveStage] Speech recognition error:', error);
      // Don't clear interim on error - let user see what was captured
    },
  });

  // Scroll to bottom of conversation
  useEffect(() => {
    conversationEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [conversationHistory, userInterimText]);

  // Add message to conversation history
  const addMessage = (role: 'mentor' | 'user', text: string) => {
    setConversationHistory(prev => [
      ...prev,
      {
        id: `${role}-${Date.now()}`,
        role,
        text,
        timestamp: new Date(),
      }
    ]);
  };

  // When a new question arrives, add it to conversation and speak it
  useEffect(() => {
    if (!currentQuestion) return;

    // Add mentor question to conversation
    addMessage('mentor', currentQuestion);

    // Speak the question if voice is enabled
    if (voiceEnabled && isTTSSupported) {
      speak(currentQuestion);
    }
  }, [currentQuestion]); // Only trigger on new question

  // When mentor finishes speaking, auto-start listening
  useEffect(() => {
    if (isAutoListening && !isSpeaking && voiceEnabled && stt.isSupported && currentQuestion) {
      // Small delay before starting to listen
      const timer = setTimeout(() => {
        stt.startListening();
      }, 500);
      return () => clearTimeout(timer);
    }
  }, [isSpeaking, isAutoListening, voiceEnabled, stt.isSupported, currentQuestion]);

  // Sync voice settings
  useEffect(() => {
    setVoiceEnabled(voiceSettings.enabled);
    setRate(voiceSettings.rate);
    setPitch(voiceSettings.pitch);
    setVolume(voiceSettings.volume);

    if (voiceSettings.voiceName && voices.length > 0) {
      const match = voices.find((v) => v.name === voiceSettings.voiceName);
      if (match) setVoice(match);
    }
  }, [setPitch, setRate, setVoice, setVolume, voiceSettings, voices]);

  // Cleanup on unmount
  useEffect(() => () => {
    stopSpeaking();
    stt.stopListening();
  }, [stopSpeaking, stt]);

  // Handle answer submission
  const handleSubmit = async () => {
    if (!currentAnswer.trim()) return;

    stt.stopListening();
    setUserInterimText('');
    await handleSubmitAnswer();
    stt.resetTranscript();
  };

  // Toggle voice mentor
  const toggleVoice = () => {
    const newState = !voiceEnabled;
    setVoiceEnabled(newState);
    updateVoiceSettings({ enabled: newState });

    if (!newState) {
      stopSpeaking();
      stt.stopListening();
      setIsAutoListening(false);
    } else if (currentQuestion) {
      speak(currentQuestion);
    }
  };

  // Toggle microphone listening
  const toggleListening = () => {
    if (stt.isListening) {
      stt.stopListening();
      setIsAutoListening(false);
    } else {
      stt.startListening();
      setIsAutoListening(true);
    }
  };

  // Calculate progress
  const completedQuestions = qnaList.length;
  const currentQuestionNum = completedQuestions + 1;
  const progressPercent = Math.min((completedQuestions / ESTIMATED_QUESTIONS) * 100, 100);

  return (
    <div className="space-y-6">
      {/* Header with Progress */}
      <div className="card p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="heading-card flex items-center gap-2">
              <MessageSquare className="text-electric-blue" size={24} />
              Conversation with AI Mentor
            </h2>
            <p className="text-text-secondary text-sm mt-1">
              Answer questions to help craft your personalized response
            </p>
          </div>
          <div className="text-right">
            <div className="text-2xl font-bold text-electric-blue">
              {currentQuestionNum} <span className="text-text-tertiary text-base font-normal">of ~{ESTIMATED_QUESTIONS}</span>
            </div>
            <div className="text-xs text-text-tertiary">questions</div>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="h-2 bg-surface-secondary rounded-full overflow-hidden">
          <div
            className="h-full bg-electric-blue transition-all duration-500 ease-out"
            style={{ width: `${progressPercent}%` }}
          />
        </div>
      </div>

      {/* Voice Controls */}
      <div className="card p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            {/* Mentor Voice Toggle */}
            <button
              onClick={toggleVoice}
              disabled={!isTTSSupported}
              className={cn(
                "flex items-center gap-2 px-4 py-2 rounded-lg transition-all",
                voiceEnabled
                  ? "bg-electric-blue text-white"
                  : "bg-surface-secondary text-text-secondary hover:bg-surface-tertiary"
              )}
            >
              {voiceEnabled ? <Volume2 size={18} /> : <VolumeX size={18} />}
              <span className="text-sm font-medium">
                {voiceEnabled ? 'Mentor Voice ON' : 'Mentor Voice OFF'}
              </span>
            </button>

            {/* Microphone Toggle */}
            <button
              onClick={toggleListening}
              disabled={!stt.isSupported || isLoading}
              className={cn(
                "flex items-center gap-2 px-4 py-2 rounded-lg transition-all",
                stt.isListening
                  ? "bg-status-error text-white animate-pulse"
                  : "bg-surface-secondary text-text-secondary hover:bg-surface-tertiary"
              )}
            >
              {stt.isListening ? <Mic size={18} /> : <MicOff size={18} />}
              <span className="text-sm font-medium">
                {stt.isListening ? 'Listening...' : 'Start Mic'}
              </span>
            </button>
          </div>

          {/* Status Indicators */}
          <div className="flex items-center gap-3 text-sm">
            {isSpeaking && (
              <span className="flex items-center gap-2 text-electric-blue">
                <Loader2 size={14} className="animate-spin" />
                Mentor speaking...
              </span>
            )}
            {ttsError && (
              <span className="text-status-error text-xs">Voice error</span>
            )}
          </div>
        </div>
      </div>

      {/* Conversation Transcript */}
      <div className="card p-6">
        <h3 className="text-sm font-medium text-text-tertiary uppercase tracking-wider mb-4">
          Conversation Transcript
        </h3>

        <div className="space-y-4 max-h-[400px] overflow-y-auto pr-2">
          {/* Previous Q&A from context */}
          {qnaList.map((qna, index) => (
            <div key={`qna-${index}-${qna.order}`} className="space-y-3">
              {/* Mentor Message */}
              <div className="flex gap-3">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-electric-blue/20 flex items-center justify-center">
                  <Bot size={16} className="text-electric-blue" />
                </div>
                <div className="flex-1 bg-electric-blue/10 rounded-2xl rounded-tl-sm p-4">
                  <p className="text-sm font-medium text-electric-blue mb-1">AI Mentor</p>
                  <p className="text-text-primary">{qna.question}</p>
                </div>
              </div>
              {/* User Response */}
              <div className="flex gap-3 justify-end">
                <div className="flex-1 bg-surface-secondary rounded-2xl rounded-tr-sm p-4 max-w-[85%] ml-auto">
                  <p className="text-sm font-medium text-text-tertiary mb-1">You</p>
                  <p className="text-text-primary">{qna.answer}</p>
                </div>
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-surface-tertiary flex items-center justify-center">
                  <User size={16} className="text-text-secondary" />
                </div>
              </div>
            </div>
          ))}

          {/* Current Question from Mentor */}
          {currentQuestion && (
            <div className="flex gap-3">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-electric-blue/20 flex items-center justify-center">
                <Bot size={16} className="text-electric-blue" />
              </div>
              <div className="flex-1 bg-electric-blue/10 rounded-2xl rounded-tl-sm p-4">
                <div className="flex items-center gap-2 mb-1">
                  <p className="text-sm font-medium text-electric-blue">AI Mentor</p>
                  {isSpeaking && (
                    <span className="flex items-center gap-1 text-xs text-electric-blue/70">
                      <Volume2 size={12} className="animate-pulse" />
                      speaking
                    </span>
                  )}
                </div>
                <p className="text-text-primary">{currentQuestion}</p>
              </div>
            </div>
          )}

          {/* User's Current Response (with interim) */}
          {(currentAnswer || userInterimText) && (
            <div className="flex gap-3 justify-end">
              <div className={cn(
                "flex-1 rounded-2xl rounded-tr-sm p-4 max-w-[85%] ml-auto",
                userInterimText && !currentAnswer
                  ? "bg-surface-secondary/50 border-2 border-dashed border-border-light"
                  : "bg-surface-secondary"
              )}>
                <div className="flex items-center gap-2 mb-1">
                  <p className="text-sm font-medium text-text-tertiary">You</p>
                  {stt.isListening && (
                    <span className="flex items-center gap-1 text-xs text-status-error">
                      <span className="w-2 h-2 rounded-full bg-status-error animate-pulse" />
                      listening
                    </span>
                  )}
                </div>
                <p className={cn(
                  "text-text-primary",
                  userInterimText && !currentAnswer && "text-text-secondary italic"
                )}>
                  {currentAnswer || userInterimText || '...'}
                </p>
              </div>
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-surface-tertiary flex items-center justify-center">
                <User size={16} className="text-text-secondary" />
              </div>
            </div>
          )}

          {/* Loading state for next question */}
          {isLoading && !currentQuestion && (
            <div className="flex gap-3">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-electric-blue/20 flex items-center justify-center">
                <Bot size={16} className="text-electric-blue" />
              </div>
              <div className="flex-1 bg-electric-blue/10 rounded-2xl rounded-tl-sm p-4">
                <p className="text-sm font-medium text-electric-blue mb-2">AI Mentor</p>
                <div className="flex items-center gap-2">
                  <Loader2 size={16} className="animate-spin text-electric-blue" />
                  <span className="text-text-secondary">
                    Thinking of the next question based on your answers...
                  </span>
                </div>
              </div>
            </div>
          )}

          <div ref={conversationEndRef} />
        </div>
      </div>

      {/* Answer Input Area */}
      {currentQuestion && (
        <div className="card p-6">
          <div className="flex items-center justify-between mb-3">
            <label className="block text-sm font-medium text-text-primary">
              Your Answer
            </label>
            {stt.isListening && (
              <span className="flex items-center gap-2 text-sm text-status-error">
                <span className="relative flex h-3 w-3">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-status-error opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-status-error"></span>
                </span>
                Recording your voice...
              </span>
            )}
          </div>

          {/* Real-time transcript preview */}
          {userInterimText && (
            <div className="mb-3 p-3 bg-electric-blue/5 border border-electric-blue/20 rounded-lg">
              <p className="text-xs text-electric-blue font-medium mb-1">Hearing you say:</p>
              <p className="text-text-primary italic">{userInterimText}</p>
            </div>
          )}

          <textarea
            value={currentAnswer}
            onChange={(e) => setCurrentAnswer(e.target.value)}
            placeholder={stt.isListening
              ? "Speak your answer - it will appear here automatically..."
              : "Type your answer or click 'Start Mic' to speak..."
            }
            className="w-full min-h-[120px] p-4 border border-border-light rounded-lg bg-surface-primary text-text-primary resize-none focus:outline-none focus:ring-2 focus:ring-electric-blue"
            disabled={isLoading}
          />

          <div className="flex items-center gap-3 mt-4">
            <button
              onClick={handleSubmit}
              disabled={isLoading || !currentAnswer.trim()}
              className="btn-primary flex-1 flex items-center justify-center gap-2"
            >
              {isLoading ? (
                <>
                  <Loader2 size={18} className="animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  Submit Answer
                  <ChevronRight size={18} />
                </>
              )}
            </button>
          </div>

          {/* Processing Status */}
          {isLoading && (
            <div className="mt-4 p-3 bg-surface-secondary rounded-lg">
              <div className="flex items-center gap-2 text-sm text-text-secondary">
                <Loader2 size={14} className="animate-spin" />
                <span>Analyzing your response and preparing the next question...</span>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Initial Loading State */}
      {isLoading && !currentQuestion && qnaList.length === 0 && (
        <div className="card p-8 text-center">
          <Loader2 size={40} className="animate-spin text-electric-blue mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-text-primary mb-2">
            Starting Your Mentoring Session
          </h3>
          <p className="text-text-secondary">
            The AI mentor is preparing personalized questions based on the interview question...
          </p>
        </div>
      )}
    </div>
  );
}
