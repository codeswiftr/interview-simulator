import { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { CheckCircle, Sparkles, Loader2, Edit2, Save, X } from 'lucide-react';
import { usePreparation } from '../../contexts/PreparationContext';
import { VoiceInputButton } from '../common/VoiceInputButton';
import ContextualTooltip from '../common/ContextualTooltip';

interface DraftStageProps {
  showGenerateButton?: boolean;
}

export default function DraftStage({ showGenerateButton = false }: DraftStageProps) {
  const navigate = useNavigate();
  const {
    draft,
    isGenerating,
    isLoading,
    isSavingDraft,
    handleGenerateDraft,
    handleStartPractice,
    handleSaveDraft,
  } = usePreparation();

  const [isEditingDraft, setIsEditingDraft] = useState(false);
  const [editedDraft, setEditedDraft] = useState<string>('');
  const [draftInterimTranscript, setDraftInterimTranscript] = useState<string>('');
  const draftTextareaRef = useRef<HTMLTextAreaElement>(null);

  const handleStartEdit = () => {
    setEditedDraft(draft);
    setIsEditingDraft(true);
  };

  const handleCancelEdit = () => {
    setIsEditingDraft(false);
    setEditedDraft('');
  };

  const handleSave = async () => {
    await handleSaveDraft(editedDraft);
    setIsEditingDraft(false);
    setEditedDraft('');
  };

  // Show generate button if no draft yet
  if (showGenerateButton && !draft) {
    return (
      <div className="card p-8 text-center">
        <CheckCircle size={48} className="text-electric-blue mx-auto mb-4" />
        <h2 className="heading-card mb-2">Questions Complete!</h2>
        <p className="text-text-secondary mb-6">
          We have enough information. Ready to generate your personalized draft?
        </p>
        <button
          onClick={handleGenerateDraft}
          disabled={isGenerating}
          className="btn-primary"
        >
          {isGenerating ? (
            <>
              <Loader2 size={16} className="animate-spin" />
              <span className="flex items-center gap-2">
                Generating Draft...
                <span className="text-xs opacity-75">(10-15 seconds)</span>
              </span>
            </>
          ) : (
            <>
              <Sparkles size={16} />
              Generate Draft
            </>
          )}
        </button>
      </div>
    );
  }

  // Show draft review
  return (
    <div className="card p-8">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <h2 className="heading-card">Your Personalized Draft</h2>
            <ContextualTooltip
              content="This draft was generated using your answers from the questions above. It follows the STAR method (Situation, Task, Action, Result) and is tailored to your experience level. You can edit it before practicing."
              position="right"
              trigger="click"
              title="AI-Generated Draft"
            />
          </div>
          <p className="text-text-secondary">
            Review and edit your draft answer. You can practice delivering it next.
          </p>
        </div>
        {!isEditingDraft && (
          <button
            onClick={handleStartEdit}
            className="btn-ghost flex items-center gap-2"
          >
            <Edit2 size={16} />
            Edit
          </button>
        )}
      </div>

      {isEditingDraft ? (
        <div className="mb-6">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <label className="block text-sm font-medium text-text-primary">
                Edit Draft
              </label>
              <span className="text-xs text-text-tertiary">
                (Select text to replace, or click to append)
              </span>
            </div>
            <VoiceInputButton
              onTranscript={(text) => {
                const textarea = draftTextareaRef.current;
                if (!textarea) return;

                const start = textarea.selectionStart;
                const end = textarea.selectionEnd;
                const currentValue = editedDraft;

                if (start !== end) {
                  // Replace selection mode
                  const newValue =
                    currentValue.substring(0, start) +
                    text +
                    currentValue.substring(end);
                  setEditedDraft(newValue);
                  setTimeout(() => {
                    textarea.focus();
                    textarea.setSelectionRange(start + text.length, start + text.length);
                  }, 0);
                } else {
                  // Append mode
                  const insertText = start === currentValue.length || currentValue[start - 1] === ' ' || currentValue[start - 1] === '\n'
                    ? text
                    : ` ${text}`;
                  const newValue =
                    currentValue.substring(0, start) +
                    insertText +
                    currentValue.substring(end);
                  setEditedDraft(newValue);
                  setTimeout(() => {
                    textarea.focus();
                    textarea.setSelectionRange(start + insertText.length, start + insertText.length);
                  }, 0);
                }
                setDraftInterimTranscript('');
              }}
              onInterim={(text) => {
                setDraftInterimTranscript(text);
              }}
              disabled={isSavingDraft}
              placeholder="Listening..."
              size="sm"
            />
          </div>
          <textarea
            ref={draftTextareaRef}
            value={editedDraft}
            onChange={(e) => setEditedDraft(e.target.value)}
            className="w-full min-h-[300px] p-4 border border-border-light rounded-lg bg-surface-primary text-text-primary font-mono text-sm resize-none focus:outline-none focus:ring-2 focus:ring-electric-blue"
            placeholder="Edit your draft answer..."
          />
          {draftInterimTranscript && (
            <div className="mt-2 p-2 bg-electric-blue/10 border border-electric-blue/20 rounded text-sm text-text-secondary italic">
              <span className="text-electric-blue">Preview:</span> {draftInterimTranscript}
            </div>
          )}
          <div className="flex items-center gap-4 mt-4">
            <button
              onClick={handleSave}
              disabled={isSavingDraft || !editedDraft.trim()}
              className="btn-primary flex items-center gap-2"
            >
              {isSavingDraft ? (
                <>
                  <Loader2 size={16} className="animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Save size={16} />
                  Save Changes
                </>
              )}
            </button>
            <button
              onClick={handleCancelEdit}
              disabled={isSavingDraft}
              className="btn-secondary flex items-center gap-2"
            >
              <X size={16} />
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <div className="bg-surface-secondary p-6 rounded-lg mb-6">
          <div className="prose prose-sm max-w-none dark:prose-invert">
            <pre className="whitespace-pre-wrap font-sans text-text-primary">{draft}</pre>
          </div>
        </div>
      )}

      {!isEditingDraft && (
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/questions')}
            className="btn-secondary"
          >
            Done
          </button>
          <button
            onClick={handleStartPractice}
            disabled={isLoading}
            className="btn-primary"
          >
            {isLoading ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                Starting...
              </>
            ) : (
              'Start Practice'
            )}
          </button>
        </div>
      )}
    </div>
  );
}
