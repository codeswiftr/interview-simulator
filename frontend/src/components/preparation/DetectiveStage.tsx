import { useState, useEffect } from 'react';
import { Loader2, Mic, MessageCircle } from 'lucide-react';
import { usePreparation } from '../../contexts/PreparationContext';
import { useSpeechSynthesis } from '../../hooks/useSpeechSynthesis';
import { useSpeechRecognition } from '../../hooks/useSpeechRecognition';
import { useVoicePreferences } from '../../hooks/useVoicePreferences';
import { useConversationMode } from '../../hooks/useConversationMode';
import { VoiceInputButton } from '../common/VoiceInputButton';
import ConversationIndicator from '../interview/ConversationIndicator';
import ContextualTooltip from '../common/ContextualTooltip';

export default function DetectiveStage() {
  const {
    currentQuestion,
    currentAnswer,
    setCurrentAnswer,
    qnaList,
    isLoading,
    handleSubmitAnswer,
  } = usePreparation();

  const [interimTranscript, setInterimTranscript] = useState<string>('');
  const { settings: voiceSettings, updateSettings: updateVoiceSettings } = useVoicePreferences();
  const [voiceEnabled, setVoiceEnabled] = useState(voiceSettings.enabled);
  const [conversationModeEnabled, setConversationModeEnabled] = useState(false);

  const tts = useSpeechSynthesis();
  const {
    speak,
    stop: stopSpeaking,
    isSpeaking,
    isSupported: isSpeechSupported,
    error: speechError,
    setVoice,
    setRate,
    setPitch,
    setVolume,
    voices,
  } = tts;

  const stt = useSpeechRecognition({
    onResult: (transcript, isFinal) => {
      if (isFinal && conversationModeEnabled) {
        setCurrentAnswer(transcript);
      }
    },
  });

  const conversation = useConversationMode({
    tts,
    stt,
    autoListen: voiceSettings.autoListen,
    enabled: conversationModeEnabled && voiceEnabled,
    onUserFinish: (transcript) => {
      if (transcript.trim()) {
        setCurrentAnswer(transcript);
      }
    },
  });

  // Auto-speak detective questions when enabled
  useEffect(() => {
    if (!currentQuestion || !voiceEnabled || !isSpeechSupported) {
      stopSpeaking();
      return;
    }

    if (conversationModeEnabled) {
      conversation.startConversation();
      conversation.mentorSay(currentQuestion);
    } else {
      speak(currentQuestion);
    }
  }, [currentQuestion, voiceEnabled, isSpeechSupported, speak, stopSpeaking, conversationModeEnabled, conversation]);

  // Cleanup TTS on unmount
  useEffect(() => () => stopSpeaking(), [stopSpeaking]);

  // Sync speech settings
  useEffect(() => {
    setVoiceEnabled(voiceSettings.enabled);
    setRate(voiceSettings.rate);
    setPitch(voiceSettings.pitch);
    setVolume(voiceSettings.volume);

    if (voiceSettings.voiceName && voices.length > 0) {
      const match = voices.find((v) => v.name === voiceSettings.voiceName);
      if (match) {
        setVoice(match);
      }
    }
  }, [setPitch, setRate, setVoice, setVolume, voiceSettings, voices]);

  const handleSubmit = async () => {
    await handleSubmitAnswer();
    stt.resetTranscript();
  };

  return (
    <div className="card p-8">
      <div className="mb-6">
        <div className="flex items-center gap-2 mb-2">
          <h2 className="heading-card">Step 1: Answer Questions</h2>
          <ContextualTooltip
            content="Our AI coach will ask you 3-5 clarifying questions to understand your experience. Answer honestly and with specific examples - this helps us create a personalized, authentic draft answer for you."
            position="right"
            trigger="click"
            title="How it works"
          />
        </div>
        <p className="text-text-secondary">
          Help us understand your experience so we can create a personalized answer.
        </p>
      </div>

      {/* Q&A History */}
      {qnaList.length > 0 && (
        <div className="mb-6 space-y-4">
          {qnaList.map((qna) => (
            <div key={qna.order} className="bg-surface-secondary p-4 rounded-lg">
              <p className="font-semibold text-text-primary mb-2">Q{qna.order}: {qna.question}</p>
              <p className="text-text-secondary">{qna.answer}</p>
            </div>
          ))}
        </div>
      )}

      {/* Current Question */}
      {currentQuestion && (
        <div className="mb-6">
          <div className="bg-electric-blue/10 border border-electric-blue/20 p-6 rounded-lg mb-4">
            <p className="font-semibold text-text-primary mb-2">
              Question {qnaList.length + 1}:
            </p>
            <p className="text-lg text-text-primary">{currentQuestion}</p>
            <div className="flex flex-wrap items-center gap-3 mt-3">
              <button
                type="button"
                onClick={() => {
                  if (!isSpeechSupported) return;
                  setVoiceEnabled((prev) => {
                    const next = !prev;
                    updateVoiceSettings({ enabled: next });
                    if (!next) {
                      stopSpeaking();
                      conversation.endConversation();
                    } else if (currentQuestion) {
                      speak(currentQuestion);
                    }
                    return next;
                  });
                }}
                className="btn-ghost flex items-center gap-2 text-sm"
                disabled={!isSpeechSupported}
              >
                {voiceEnabled ? 'Mute mentor voice' : 'Enable mentor voice'}
              </button>
              {voiceEnabled && stt.isSupported && (
                <button
                  type="button"
                  onClick={() => {
                    setConversationModeEnabled((prev) => {
                      const next = !prev;
                      if (!next) {
                        conversation.endConversation();
                      }
                      return next;
                    });
                  }}
                  className={`btn-ghost flex items-center gap-2 text-sm ${conversationModeEnabled ? 'text-electric-blue' : ''}`}
                >
                  <MessageCircle size={14} />
                  {conversationModeEnabled ? 'Conversation mode ON' : 'Conversation mode'}
                </button>
              )}
              {!conversationModeEnabled && isSpeaking && (
                <span className="flex items-center gap-1 text-electric-blue text-sm">
                  <Loader2 size={14} className="animate-spin" />
                  Mentor is speaking
                </span>
              )}
              {!isSpeechSupported && (
                <span className="text-xs text-text-secondary">
                  Voice not supported in this browser
                </span>
              )}
              {speechError && (
                <span className="text-xs text-status-error">
                  TTS error: {speechError}
                </span>
              )}
            </div>
          </div>

          {/* Conversation Mode Indicator */}
          {conversationModeEnabled && voiceEnabled && (
            <ConversationIndicator
              mode={conversation.mode}
              mentorName="AI Mentor"
              onInterrupt={conversation.interrupt}
              isListening={stt.isListening}
              className="mt-4"
            />
          )}

          <div className="mb-4">
            <div className="flex items-center justify-between mb-2">
              <label className="block text-sm font-medium text-text-primary">
                Your Answer
              </label>
              {!conversationModeEnabled && (
                <VoiceInputButton
                  onTranscript={(text) => {
                    const newAnswer = currentAnswer.trim() ? `${currentAnswer} ${text}`.trim() : text;
                    setCurrentAnswer(newAnswer);
                    setInterimTranscript('');
                  }}
                  onInterim={(text) => {
                    setInterimTranscript(text);
                  }}
                  disabled={isLoading}
                  placeholder="Listening..."
                  size="sm"
                />
              )}
              {conversationModeEnabled && voiceEnabled && (
                <div className="flex items-center gap-2">
                  {stt.isListening ? (
                    <>
                      <span className="relative flex h-3 w-3">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-status-error opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-3 w-3 bg-status-error"></span>
                      </span>
                      <span className="text-sm text-status-error font-medium">Listening...</span>
                      <button
                        type="button"
                        onClick={() => {
                          if (stt.transcript) {
                            setCurrentAnswer(stt.transcript);
                          }
                          stt.stopListening();
                          conversation.transitionTo('processing');
                        }}
                        className="btn-ghost text-xs text-status-error"
                      >
                        Done speaking
                      </button>
                    </>
                  ) : conversation.mode === 'user_turn' ? (
                    <button
                      type="button"
                      onClick={() => {
                        stt.startListening();
                      }}
                      className="btn-secondary text-xs flex items-center gap-1"
                    >
                      <Mic size={12} />
                      Start speaking
                    </button>
                  ) : (
                    <span className="text-sm text-text-tertiary">
                      {conversation.mode === 'mentor_speaking' ? 'Mentor speaking...' : 'Waiting...'}
                    </span>
                  )}
                </div>
              )}
            </div>
            <textarea
              value={currentAnswer}
              onChange={(e) => setCurrentAnswer(e.target.value)}
              placeholder={conversationModeEnabled ? "Your spoken answer will appear here..." : "Type your answer here or use voice input..."}
              className="w-full min-h-[120px] p-4 border border-border-light rounded-lg bg-surface-primary text-text-primary resize-none focus:outline-none focus:ring-2 focus:ring-electric-blue"
              disabled={isLoading}
            />
            {!conversationModeEnabled && interimTranscript && (
              <div className="mt-2 p-2 bg-electric-blue/10 border border-electric-blue/20 rounded text-sm text-text-secondary italic">
                <span className="text-electric-blue">Preview:</span> {interimTranscript}
              </div>
            )}
            {conversationModeEnabled && stt.isListening && stt.transcript && (
              <div className="mt-2 p-2 bg-electric-blue/10 border border-electric-blue/20 rounded text-sm text-text-secondary italic">
                <span className="text-electric-blue">Hearing:</span> {stt.transcript}
              </div>
            )}
          </div>

          <button
            onClick={handleSubmit}
            disabled={isLoading || !currentAnswer.trim()}
            className="btn-primary w-full"
          >
            {isLoading ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                Submitting...
              </>
            ) : (
              'Submit Answer'
            )}
          </button>
        </div>
      )}

      {/* Loading Next Question */}
      {isLoading && !currentQuestion && (
        <div className="text-center py-8">
          <Loader2 size={32} className="animate-spin text-electric-blue mx-auto mb-4" />
          <p className="text-text-secondary">Generating your personalized question...</p>
          <p className="text-xs text-text-tertiary mt-2">This usually takes 2-3 seconds</p>
        </div>
      )}
    </div>
  );
}
