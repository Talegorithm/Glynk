import { useState } from 'react';
import { toast } from 'sonner';
import { useT } from '../../i18n';
import { createThought } from '../../api/content';

interface DropEditorProps {
  onSuccess?: () => void;
}

export function DropEditor({ onSuccess }: DropEditorProps) {
  const t = useT();
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!text.trim()) return;

    setLoading(true);
    try {
      await createThought({ text: text.trim() });
      setText('');
      toast.success(t('notes.drop_success', { defaultValue: 'Idea dropped successfully' }));
      onSuccess?.();
    } catch {
      toast.error(t('notes.drop_error', { defaultValue: 'Failed to drop idea' }));
    } finally {
      setLoading(false);
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      handleSubmit(e);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="mb-8">
      <div className="p-4 rounded-xl glass-panel relative">
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={t('notes.drop_placeholder', { defaultValue: 'Write down an idea or note... (Cmd+Enter to save)' })}
          className="w-full bg-transparent border-none outline-none resize-none min-h-[80px] text-gray-800 dark:text-gray-200 placeholder-gray-400 dark:placeholder-gray-500 text-base"
        />
        <div className="flex justify-end mt-2">
          <button
            type="submit"
            disabled={!text.trim() || loading}
            className="px-4 py-1.5 rounded-full bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900 text-sm font-medium transition-transform active:scale-95 disabled:opacity-50 disabled:active:scale-100 cursor-pointer"
          >
            {loading ? t('common.loading', { defaultValue: 'Loading...' }) : t('notes.drop_submit', { defaultValue: 'Drop' })}
          </button>
        </div>
      </div>
    </form>
  );
}
