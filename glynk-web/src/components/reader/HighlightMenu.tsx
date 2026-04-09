/**
 * 高亮区域点击菜单 - 从 Brainow 迁移
 */

import { useRef, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { useT } from '../../i18n';

interface HighlightMenuProps {
  annotationId: string;
  position: { top: number; left: number };
  hasNote: boolean;
  onDelete: () => void;
  onEdit: () => void;
  onClose: () => void;
}

export function HighlightMenu({
  position,
  hasNote,
  onDelete,
  onEdit,
  onClose,
}: HighlightMenuProps) {
  const t = useT();
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        onClose();
      }
    };

    const timer = setTimeout(() => {
      document.addEventListener('mousedown', handleClickOutside);
      document.addEventListener('touchstart', handleClickOutside as EventListener);
    }, 100);

    return () => {
      clearTimeout(timer);
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('touchstart', handleClickOutside as EventListener);
    };
  }, [onClose]);

  const menu = (
    <div
      ref={menuRef}
      className="fixed z-[2147483647]"
      style={{
        top: `${position.top}px`,
        left: `${position.left}px`,
      }}
    >
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 overflow-hidden min-w-[120px]">
        <button
          className="w-full flex items-center gap-2 px-4 py-2.5 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-left cursor-pointer"
          onClick={() => { onEdit(); onClose(); }}
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
          </svg>
          {hasNote ? t('annotation.edit') : t('annotation.add')}
        </button>

        <div className="border-t border-gray-100 dark:border-gray-700" />

        <button
          className="w-full flex items-center gap-2 px-4 py-2.5 text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors text-left cursor-pointer"
          onClick={() => { onDelete(); onClose(); }}
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
          {t('annotation.delete')}
        </button>
      </div>
    </div>
  );

  return createPortal(menu, document.body);
}
