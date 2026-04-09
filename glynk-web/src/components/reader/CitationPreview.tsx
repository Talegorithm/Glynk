/**
 * 引用预览浮窗 - 从 Brainow 迁移
 */

import { useEffect, useState } from 'react';
import { useT } from '../../i18n';

interface CitationPreviewProps {
  targetSpanId: string | null;
  onClose: () => void;
}

export function CitationPreview({ targetSpanId, onClose }: CitationPreviewProps) {
  const t = useT();
  const [content, setContent] = useState<string>('');
  const [position, setPosition] = useState<{ top: number; left: number } | null>(null);

  useEffect(() => {
    if (!targetSpanId) {
      setContent('');
      setPosition(null);
      return;
    }

    const clickedLink = document.querySelector(`a.reference-link[data-target-span="${targetSpanId}"]`);
    if (!clickedLink) return;

    const refContent = clickedLink.getAttribute('data-ref-content');
    if (refContent) {
      setContent(refContent);
    } else {
      const targetSpan = document.getElementById(targetSpanId);
      if (!targetSpan) {
        setContent(t('citation.not_loaded'));
      } else {
        const paragraph = targetSpan.closest('p');
        if (!paragraph) {
          setContent(targetSpan.textContent || '');
        } else {
          const fullText = paragraph.textContent || '';
          const targetText = targetSpan.textContent || '';
          const targetIndex = fullText.indexOf(targetText);
          if (targetIndex === -1) {
            setContent(targetText);
          } else {
            const start = Math.max(0, targetIndex - 50);
            const end = Math.min(fullText.length, targetIndex + targetText.length + 50);
            let ctx = fullText.substring(start, end);
            if (start > 0) ctx = '...' + ctx;
            if (end < fullText.length) ctx = ctx + '...';
            setContent(ctx);
          }
        }
      }
    }

    const rect = clickedLink.getBoundingClientRect();
    const viewportWidth = window.innerWidth;
    const maxWidth = 448;
    let left = rect.left;
    if (left + maxWidth > viewportWidth - 20) left = viewportWidth - maxWidth - 20;
    left = Math.max(20, left);

    setPosition({ top: rect.bottom + 5, left });
  }, [targetSpanId]);

  if (!targetSpanId || !content || !position) return null;

  return (
    <>
      <div className="fixed inset-0 z-40" onClick={onClose} />
      <div
        className="fixed z-50 max-w-md bg-white dark:bg-gray-800 rounded-lg shadow-2xl border border-gray-200 dark:border-gray-700 p-4"
        style={{ top: `${position.top}px`, left: `${position.left}px` }}
      >
        <div className="flex items-start justify-between mb-2">
          <span className="text-xs text-gray-500 font-medium">{t('citation.preview')}</span>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors cursor-pointer"
          >
            ✕
          </button>
        </div>
        <div className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
          {content}
        </div>
        <div
          className="absolute w-3 h-3 bg-white dark:bg-gray-800 border-l border-t border-gray-200 dark:border-gray-700 transform rotate-45"
          style={{ top: '-6px', left: '20px' }}
        />
      </div>
    </>
  );
}
