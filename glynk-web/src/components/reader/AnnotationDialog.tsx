/**
 * 笔记输入对话框 - 从 Brainow 迁移
 */

import { useState, useRef, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { USER_SELECTABLE_COLORS, DEFAULT_COLOR } from '../../config/colors';
import { useT } from '../../i18n';

interface AnnotationDialogProps {
  selectedText: string;
  initialNote?: string;
  initialColorKey?: string;
  isEditing?: boolean;
  onSave: (note: string, colorKey: string) => void;
  onCancel: () => void;
}

export function AnnotationDialog({
  selectedText,
  initialNote = '',
  initialColorKey = DEFAULT_COLOR.key,
  isEditing = false,
  onSave,
  onCancel
}: AnnotationDialogProps) {
  const t = useT();
  const [note, setNote] = useState(initialNote);
  const [selectedColorKey, setSelectedColorKey] = useState(initialColorKey);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    textareaRef.current?.focus();
  }, []);

  const handleSave = () => {
    onSave(note.trim(), selectedColorKey);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      handleSave();
    }
    if (e.key === 'Escape') {
      e.preventDefault();
      onCancel();
    }
  };

  const dialog = (
    <div className="fixed inset-0 z-[2147483646] flex items-center justify-center">
      <div
        className="absolute inset-0 bg-black/30"
        onClick={onCancel}
      />

      <div className="relative bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-lg w-full mx-4 max-h-[80vh] flex flex-col">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">
            {isEditing ? t('annotation.edit') : t('annotation.add')}
          </h3>
        </div>

        <div className="px-6 py-4 flex-1 overflow-y-auto">
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              {t('annotation.selected_text')}
            </label>
            <blockquote className="bg-gray-50 dark:bg-gray-900 border-l-4 border-gray-300 dark:border-gray-600 p-3 text-sm text-gray-700 dark:text-gray-300 italic rounded">
              {selectedText.length > 200
                ? `${selectedText.slice(0, 200)}...`
                : selectedText}
            </blockquote>
          </div>

          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              笔记内容（可选）
            </label>
            <textarea
              ref={textareaRef}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100"
              rows={4}
              placeholder={t('annotation.note_placeholder')}
              value={note}
              onChange={(e) => setNote(e.target.value)}
              onKeyDown={handleKeyDown}
            />
            <p className="mt-1 text-xs text-gray-500">
              {t('annotation.note_hint')}
            </p>
          </div>

          {!isEditing && (
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                {t('annotation.color')}
              </label>
              <div className="flex gap-3">
                {USER_SELECTABLE_COLORS.map((color) => (
                  <button
                    key={color.key}
                    className={`w-10 h-10 rounded-lg border-2 transition-all cursor-pointer ${
                      selectedColorKey === color.key
                        ? 'border-blue-500 ring-2 ring-blue-200'
                        : 'border-gray-200 dark:border-gray-600 hover:border-gray-400'
                    }`}
                    style={{ backgroundColor: color.highlight }}
                    onClick={() => setSelectedColorKey(color.key)}
                    title={color.name}
                  />
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-700 flex justify-end gap-3">
          <button
            className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors cursor-pointer"
            onClick={onCancel}
          >
            {t('annotation.cancel')}
          </button>
          <button
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors cursor-pointer"
            onClick={handleSave}
          >
            {t('annotation.save')}
          </button>
        </div>
      </div>
    </div>
  );

  return createPortal(dialog, document.body);
}
