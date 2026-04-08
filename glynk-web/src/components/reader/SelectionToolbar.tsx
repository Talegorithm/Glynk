/**
 * 文本选择工具栏 - 从 Brainow 迁移
 */

import { useEffect, useState, useRef } from 'react';
import { createPortal } from 'react-dom';
import type { SelectionRange } from '../../utils/reader/selection';
import { USER_SELECTABLE_COLORS } from '../../config/colors';

interface SelectionToolbarProps {
  selectionRange: SelectionRange | null;
  onHighlight: (colorKey?: string) => void;
  onAnnotate: () => void;
  onCopy: () => void;
  onClose: () => void;
}

export function SelectionToolbar({
  selectionRange,
  onHighlight,
  onAnnotate,
  onCopy,
  onClose,
}: SelectionToolbarProps) {
  const [position, setPosition] = useState<{ top: number; left: number } | null>(null);
  const [showColorPicker, setShowColorPicker] = useState(false);
  const toolbarRef = useRef<HTMLDivElement>(null);
  const savedRangeRef = useRef<SelectionRange | null>(null);

  useEffect(() => {
    if (!selectionRange) {
      setPosition(null);
      setShowColorPicker(false);
      savedRangeRef.current = null;
      return;
    }

    savedRangeRef.current = selectionRange;

    const rect = selectionRange.boundingRect;
    const toolbarWidth = 240;
    const toolbarHeight = 48;

    let left = rect.left + rect.width / 2 - toolbarWidth / 2;
    let top = rect.top - toolbarHeight - 8;

    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;

    if (left < 8) left = 8;
    if (left + toolbarWidth > viewportWidth - 8) left = viewportWidth - toolbarWidth - 8;
    if (top < 8) top = rect.bottom + 8;
    if (top + toolbarHeight > viewportHeight - 8) top = viewportHeight / 2 - toolbarHeight / 2;

    setPosition({ top, left });
  }, [selectionRange]);

  useEffect(() => {
    if (!selectionRange) return;

    const handleClickOutside = (e: MouseEvent) => {
      if (toolbarRef.current?.contains(e.target as Node)) return;
      const selection = window.getSelection();
      if (selection && !selection.isCollapsed) return;
      onClose();
    };

    const timer = setTimeout(() => {
      document.addEventListener('mousedown', handleClickOutside);
    }, 100);

    return () => {
      clearTimeout(timer);
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [selectionRange, onClose]);

  if (!selectionRange || !position) return null;

  const handleHighlight = (colorKey?: string) => {
    onHighlight(colorKey);
    setShowColorPicker(false);
  };

  const handleToolbarMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
  };

  const toolbar = (
    <div
      ref={toolbarRef}
      className="fixed"
      style={{
        top: `${position.top}px`,
        left: `${position.left}px`,
        zIndex: 2147483647,
        pointerEvents: 'auto',
        userSelect: 'none',
      }}
      onMouseDown={handleToolbarMouseDown}
    >
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-1 p-2">
          <button
            className="flex items-center gap-1.5 px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors cursor-pointer"
            onClick={() => setShowColorPicker(!showColorPicker)}
            title="高亮"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01" />
            </svg>
            高亮
          </button>

          <button
            className="flex items-center gap-1.5 px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors cursor-pointer"
            onClick={onAnnotate}
            title="添加笔记"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
            </svg>
            笔记
          </button>

          <button
            className="flex items-center gap-1.5 px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors cursor-pointer"
            onClick={onCopy}
            title="复制"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
            复制
          </button>

          <div className="w-px h-6 bg-gray-200 dark:bg-gray-600" />

          <button
            className="px-2 py-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors cursor-pointer"
            onClick={onClose}
            title="关闭"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {showColorPicker && (
          <div className="border-t border-gray-200 dark:border-gray-700 p-2">
            <div className="text-xs text-gray-500 mb-2 px-1">选择颜色</div>
            <div className="flex gap-2">
              {USER_SELECTABLE_COLORS.map((color) => (
                <button
                  key={color.key}
                  className="w-8 h-8 rounded border-2 border-gray-200 dark:border-gray-600 hover:border-gray-400 transition-colors cursor-pointer"
                  style={{ backgroundColor: color.highlight }}
                  onClick={() => handleHighlight(color.key)}
                  title={color.name}
                />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );

  return createPortal(toolbar, document.body);
}
