/**
 * 阅读器内容渲染组件（连续滚动模式）
 * 从 Brainow 迁移，适配 Glynk API
 */

import { useEffect, useRef, useState, memo, useLayoutEffect, useCallback } from 'react';
import { useReaderStore } from '../../store/reader';
import { CitationPreview } from './CitationPreview';
import { SelectionToolbar } from './SelectionToolbar';
import { AnnotationDialog } from './AnnotationDialog';
import { HighlightMenu } from './HighlightMenu';
import { getSelectionRange, clearSelection, highlightSpanRange, removeHighlightById } from '../../utils/reader/selection';
import type { SelectionRange } from '../../utils/reader/selection';
import { createAnnotation, deleteAnnotation, updateAnnotation, getContentAnnotations } from '../../api/annotation';
import { saveReadingProgress } from '../../api/content';
import type { Annotation, TextSelectionAnchor } from '../../types/annotation';
import type { FileContent } from '../../types/reader';
import { getColorByKey, DEFAULT_COLOR } from '../../config/colors';
import { useReaderSettingsStore } from '../../store/readerSettings';
import { useAuthStore } from '../../store/auth';
import { useT } from '../../i18n';

// 单个文件块组件
const FileSection = memo(
  ({ fileIdx, content }: { fileIdx: number; content: FileContent }) => {
    const t = useT();
    const contentRef = useRef<HTMLDivElement>(null);
    const reloadCurrentFile = useReaderStore((state) => state.reloadCurrentFile);

    // 翻译状态轮询
    useEffect(() => {
      if (content.translationStatus === 'pending' || content.translationStatus === 'translating') {
        const intervalId = setInterval(() => {
          reloadCurrentFile?.();
        }, 3000);
        return () => clearInterval(intervalId);
      }
    }, [content.translationStatus, fileIdx, reloadCurrentFile]);

    // KaTeX 渲染
    useEffect(() => {
      if (!contentRef.current) return;

      requestAnimationFrame(() => {
        setTimeout(async () => {
          if (!contentRef.current) return;

          const allFormulas = contentRef.current.querySelectorAll<HTMLElement>(
            'span.formula[data-latex]'
          );
          const unrenderedFormulas = Array.from(allFormulas).filter(
            (span) => !span.querySelector('.katex')
          );

          if (unrenderedFormulas.length === 0) return;

          try {
            const katex = (await import('katex')).default;
            const originalWarn = console.warn;
            console.warn = () => {};

            unrenderedFormulas.forEach((span) => {
              const latex = span.getAttribute('data-latex');
              if (!latex) return;
              try {
                const isDisplay = span.classList.contains('formula-display');
                span.innerHTML = '';
                katex.render(latex, span, {
                  displayMode: isDisplay,
                  throwOnError: false,
                  output: 'html',
                  strict: false,
                  trust: true,
                });
              } catch {
                // ignore render errors
              }
            });

            console.warn = originalWarn;
          } catch {
            // katex not installed, skip
          }
        }, 100);
      });
    }, []);

    return (
      <div data-file-idx={fileIdx} className="reader-file-section">
        {content.translationStatus === 'pending' && (
          <div className="sticky top-0 z-10 bg-blue-50 dark:bg-blue-900/30 border-l-4 border-blue-400 p-3 mb-4 flex items-center gap-2">
            <svg className="w-5 h-5 text-blue-600 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
            <p className="text-sm font-medium text-blue-800 dark:text-blue-200">{t('reader.translation_pending')}</p>
          </div>
        )}

        {content.translationStatus === 'failed' && (
          <div className="sticky top-0 z-10 bg-red-50 dark:bg-red-900/30 border-l-4 border-red-400 p-3 mb-4 flex items-center gap-2">
            <svg className="w-5 h-5 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p className="text-sm font-medium text-red-800 dark:text-red-200">{t('reader.translation_failed')}</p>
          </div>
        )}

        <div
          ref={contentRef}
          className="reader-content prose prose-lg max-w-none"
          dangerouslySetInnerHTML={{ __html: content.html }}
        />
      </div>
    );
  },
  (prevProps, nextProps) => {
    if (prevProps.fileIdx !== nextProps.fileIdx) return false;
    if (prevProps.content.translationStatus !== nextProps.content.translationStatus) return false;
    return true;
  }
);

FileSection.displayName = 'FileSection';


interface ReaderContentProps {
  requestLogin?: () => void;
}

export function ReaderContent({ requestLogin }: ReaderContentProps) {
  const t = useT();
  const token = useAuthStore((state) => state.token);
  const contentId = useReaderStore((state) => state.contentId);
  const { fontSize, fontFamily } = useReaderSettingsStore();
  const loadedFiles = useReaderStore((state) => state.loadedFiles);
  const isLoading = useReaderStore((state) => state.isLoading);
  const isJumping = useReaderStore((state) => state.isJumping);
  const loadNextFile = useReaderStore((state) => state.loadNextFile);
  const loadPreviousFile = useReaderStore((state) => state.loadPreviousFile);

  const topSentinelRef = useRef<HTMLDivElement>(null);
  const bottomSentinelRef = useRef<HTMLDivElement>(null);

  // scrollTop 调整（向上加载时保持视觉位置）
  const scrollAdjustmentRef = useRef<{
    oldScrollHeight: number;
    oldScrollTop: number;
    minFileIdx: number;
  } | null>(null);

  const [citationTarget, setCitationTarget] = useState<string | null>(null);
  const [selectionRange, setSelectionRange] = useState<SelectionRange | null>(null);
  const [annotations, setAnnotations] = useState<Annotation[]>([]);
  const [showAnnotationDialog, setShowAnnotationDialog] = useState(false);
  const [pendingAnnotation, setPendingAnnotation] = useState<SelectionRange | null>(null);
  const [highlightMenu, setHighlightMenu] = useState<{
    annotationId: string;
    position: { top: number; left: number };
    hasNote: boolean;
  } | null>(null);
  const [editingAnnotation, setEditingAnnotation] = useState<Annotation | null>(null);

  // 阅读进度保存（debounce，需要登录）
  const progressTimerRef = useRef<number | null>(null);
  const saveProgress = useCallback(() => {
    if (!contentId || !token) return;
    if (progressTimerRef.current) clearTimeout(progressTimerRef.current);
    progressTimerRef.current = window.setTimeout(() => {
      const location = useReaderStore.getState().getCurrentLocation();
      if (location) {
        saveReadingProgress(contentId, location).catch(() => {});
      }
    }, 2000);
  }, [contentId]);

  // 滚动时保存进度
  useEffect(() => {
    const scrollContainer = document.querySelector('[data-reader-scroll]');
    if (!scrollContainer) return;
    scrollContainer.addEventListener('scroll', saveProgress);
    return () => {
      scrollContainer.removeEventListener('scroll', saveProgress);
      if (progressTimerRef.current) clearTimeout(progressTimerRef.current);
    };
  }, [saveProgress]);

  // scrollTop 调整
  useLayoutEffect(() => {
    const scrollContainer = document.querySelector('[data-reader-scroll]');
    if (!scrollContainer || loadedFiles.size === 0) return;

    const chunks = Array.from(loadedFiles.values());
    const currentMinFileIdx = Math.min(...chunks.map(c => c.fileIdx));

    if (scrollAdjustmentRef.current) {
      const { oldScrollHeight, oldScrollTop, minFileIdx: oldMinFileIdx } = scrollAdjustmentRef.current;
      if (currentMinFileIdx < oldMinFileIdx) {
        const newScrollHeight = scrollContainer.scrollHeight;
        const heightDifference = newScrollHeight - oldScrollHeight;
        if (heightDifference > 0) {
          scrollContainer.scrollTop = oldScrollTop + heightDifference;
        }
      }
    }

    scrollAdjustmentRef.current = {
      oldScrollHeight: scrollContainer.scrollHeight,
      oldScrollTop: scrollContainer.scrollTop,
      minFileIdx: currentMinFileIdx,
    };
  }, [loadedFiles]);

  // 引用链接点击
  useEffect(() => {
    const handleReferenceClick = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      const link = target.closest('a.reference-link') as HTMLAnchorElement;
      if (!link) return;

      e.preventDefault();
      const targetSpanId = link.getAttribute('data-target-span');
      if (!targetSpanId) return;

      const role = link.getAttribute('role');
      if (role === 'navigation') {
        const targetElement = document.getElementById(targetSpanId);
        targetElement?.scrollIntoView({ behavior: 'smooth', block: 'center' });
      } else {
        setCitationTarget(targetSpanId);
      }
    };

    document.addEventListener('click', handleReferenceClick);
    return () => document.removeEventListener('click', handleReferenceClick);
  }, []);

  // 文本选择检测
  useEffect(() => {
    let selectionTimeout: number | null = null;

    const handleSelectionChange = () => {
      if (selectionTimeout) clearTimeout(selectionTimeout);
      selectionTimeout = window.setTimeout(() => {
        const range = getSelectionRange();
        setSelectionRange(range || null);
      }, 200);
    };

    document.addEventListener('selectionchange', handleSelectionChange);
    return () => {
      document.removeEventListener('selectionchange', handleSelectionChange);
      if (selectionTimeout) clearTimeout(selectionTimeout);
    };
  }, [loadedFiles.size]);

  // 阻止原生右键菜单（有选中文本时）
  useEffect(() => {
    const handleContextMenu = (e: Event) => {
      const selection = window.getSelection();
      if (selection && !selection.isCollapsed) {
        e.preventDefault();
        e.stopPropagation();
      }
    };

    document.addEventListener('contextmenu', handleContextMenu, { capture: true });
    return () => document.removeEventListener('contextmenu', handleContextMenu, { capture: true });
  }, []);

  // 加载已保存的 annotations（需要登录）
  useEffect(() => {
    if (!contentId || !token) return;

    getContentAnnotations(contentId)
      .then(setAnnotations)
      .catch(console.error);
  }, [contentId, token, loadedFiles.size]);

  // 应用高亮样式到 DOM
  useEffect(() => {
    if (annotations.length === 0) return;

    setTimeout(() => {
      annotations.forEach((annotation) => {
        try {
          // 跳过已应用的
          if (document.querySelectorAll(`[data-annotation-id="${annotation.id}"]`).length > 0) return;

          const anchor = annotation.anchor as TextSelectionAnchor;

          if (anchor.startSpanId && anchor.endSpanId) {
            // 新格式：精确选区高亮
            const colorConfig = getColorByKey(anchor.color || 'yellow') || DEFAULT_COLOR;
            highlightSpanRange(
              anchor.startSpanId,
              anchor.endSpanId,
              anchor.startOffset ?? 0,
              anchor.endOffset ?? 0,
              colorConfig.highlight,
              annotation.id
            );
          } else if (anchor.spans && anchor.spans.length > 0 && anchor.color) {
            // spans-based 标注（如 agent 创建的 hook）：高亮所有 spans，颜色从 anchor.color 读取
            const spanColorConfig = getColorByKey(anchor.color as string);
            const spanColor = spanColorConfig?.highlight || 'rgba(226, 232, 240, 0.5)';
            anchor.spans.forEach((spanId: string) => {
              const span = document.getElementById(spanId);
              if (!span) return;
              span.style.backgroundColor = spanColor;
              span.setAttribute('data-highlighted', 'true');
              span.setAttribute('data-annotation-id', annotation.id);
              span.style.cursor = 'pointer';
            });
          }
        } catch {
          // ignore
        }
      });
    }, 100);
  }, [annotations, loadedFiles]);

  // 高亮区域点击事件
  useEffect(() => {
    const handleHighlightClick = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      const highlightElement = target.closest('[data-annotation-id]') as HTMLElement;
      if (!highlightElement) return;

      e.preventDefault();
      e.stopPropagation();

      const annotationId = highlightElement.getAttribute('data-annotation-id');
      if (!annotationId) return;

      const annotation = annotations.find(a => a.id === annotationId);
      if (!annotation) return;

      const rect = highlightElement.getBoundingClientRect();
      const menuWidth = 120;
      let left = rect.left + rect.width / 2 - menuWidth / 2;
      let top = rect.top - 108;

      if (left < 8) left = 8;
      if (left + menuWidth > window.innerWidth - 8) left = window.innerWidth - menuWidth - 8;
      if (top < 8) top = rect.bottom + 8;

      const anchor = annotation.anchor as TextSelectionAnchor;
      setHighlightMenu({
        annotationId,
        position: { top, left },
        hasNote: !!anchor.note,
      });
    };

    document.addEventListener('click', handleHighlightClick);
    return () => document.removeEventListener('click', handleHighlightClick);
  }, [annotations]);

  // IntersectionObserver 双向滚动加载
  useEffect(() => {
    if (isJumping || !topSentinelRef.current || !bottomSentinelRef.current) return;

    const scrollContainer = document.querySelector('[data-reader-scroll]');
    if (!scrollContainer) return;

    const bottomObserver = new IntersectionObserver(
      (entries) => { if (entries[0].isIntersecting) loadNextFile(); },
      { root: scrollContainer, rootMargin: '200px', threshold: 0 }
    );

    const topObserver = new IntersectionObserver(
      (entries) => { if (entries[0].isIntersecting) loadPreviousFile(); },
      { root: scrollContainer, rootMargin: '200px', threshold: 0 }
    );

    bottomObserver.observe(bottomSentinelRef.current);
    topObserver.observe(topSentinelRef.current);

    // 内容太短时主动加载
    const timerId = setTimeout(() => {
      if (!bottomSentinelRef.current || !scrollContainer) return;
      const containerRect = scrollContainer.getBoundingClientRect();
      const sentinelRect = bottomSentinelRef.current.getBoundingClientRect();
      if (sentinelRect.top - containerRect.bottom < 500) loadNextFile();
    }, 100);

    return () => {
      clearTimeout(timerId);
      bottomObserver.disconnect();
      topObserver.disconnect();
    };
  }, [loadNextFile, loadPreviousFile, isJumping]);

  // --- 事件处理 ---

  const refreshAnnotations = async () => {
    if (!contentId) return;
    try {
      const updated = await getContentAnnotations(contentId);
      setAnnotations(updated);
    } catch {
      // ignore
    }
  };

  const handleHighlight = async (colorKey?: string) => {
    if (!selectionRange || !contentId) return;
    if (!token) {
      requestLogin?.();
      return;
    }

    const colorConfig = colorKey ? getColorByKey(colorKey) : DEFAULT_COLOR;
    if (!colorConfig) return;

    try {
      const anchor: TextSelectionAnchor = {
        type: 'text_selection',
        spans: selectionRange.spanIds,
        startSpanId: selectionRange.startSpanId,
        endSpanId: selectionRange.endSpanId,
        startOffset: selectionRange.startOffset,
        endOffset: selectionRange.endOffset,
        color: colorConfig.key,
      };

      const newAnnotation = await createAnnotation({
        content_id: contentId,
        anchor,
        type: 'highlight',
        text: selectionRange.text,
      });

      highlightSpanRange(
        selectionRange.startSpanId,
        selectionRange.endSpanId,
        selectionRange.startOffset,
        selectionRange.endOffset,
        colorConfig.highlight,
        newAnnotation.id
      );

      await refreshAnnotations();
    } catch (error) {
      console.error('保存高亮失败:', error);
    }

    clearSelection();
    setSelectionRange(null);
  };

  const handleAnnotate = () => {
    if (!selectionRange) return;
    if (!token) {
      requestLogin?.();
      return;
    }
    setPendingAnnotation(selectionRange);
    setShowAnnotationDialog(true);
    clearSelection();
    setSelectionRange(null);
  };

  const handleSaveAnnotation = async (note: string, colorKey: string) => {
    if (!contentId) return;

    const colorConfig = getColorByKey(colorKey) || DEFAULT_COLOR;

    try {
      if (editingAnnotation) {
        // 编辑现有笔记
        const existingAnchor = editingAnnotation.anchor as TextSelectionAnchor;
        await updateAnnotation(editingAnnotation.id, {
          anchor: { ...existingAnchor, note },
        });
        setEditingAnnotation(null);
      } else if (pendingAnnotation) {
        // 新建笔记
        const anchor: TextSelectionAnchor = {
          type: 'text_selection',
          spans: pendingAnnotation.spanIds,
          startSpanId: pendingAnnotation.startSpanId,
          endSpanId: pendingAnnotation.endSpanId,
          startOffset: pendingAnnotation.startOffset,
          endOffset: pendingAnnotation.endOffset,
          color: colorConfig.key,
          note,
        };

        const newAnnotation = await createAnnotation({
          content_id: contentId,
          anchor,
          type: 'highlight',
          text: pendingAnnotation.text,
        });

        highlightSpanRange(
          pendingAnnotation.startSpanId,
          pendingAnnotation.endSpanId,
          pendingAnnotation.startOffset,
          pendingAnnotation.endOffset,
          colorConfig.highlight,
          newAnnotation.id
        );

        setPendingAnnotation(null);
      }

      await refreshAnnotations();
    } catch (error) {
      console.error('保存笔记失败:', error);
    }

    setShowAnnotationDialog(false);
  };

  const handleCancelAnnotation = () => {
    setShowAnnotationDialog(false);
    setPendingAnnotation(null);
    setEditingAnnotation(null);
  };

  const handleDeleteAnnotation = async () => {
    if (!highlightMenu || !contentId) return;

    try {
      removeHighlightById(highlightMenu.annotationId);
      await deleteAnnotation(highlightMenu.annotationId);
      await refreshAnnotations();
    } catch (error) {
      console.error('删除失败:', error);
    }
  };

  const handleEditAnnotation = () => {
    if (!highlightMenu) return;
    const annotation = annotations.find(a => a.id === highlightMenu.annotationId);
    if (!annotation) return;
    setEditingAnnotation(annotation);
    setShowAnnotationDialog(true);
  };

  const handleCopy = async () => {
    if (!selectionRange) return;
    try {
      await navigator.clipboard.writeText(selectionRange.text);
    } catch {
      const textArea = document.createElement('textarea');
      textArea.value = selectionRange.text;
      textArea.style.position = 'fixed';
      textArea.style.opacity = '0';
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
    }
    clearSelection();
    setSelectionRange(null);
  };

  const handleCloseToolbar = () => {
    clearSelection();
    setSelectionRange(null);
  };

  // --- 渲染 ---

  if (loadedFiles.size === 0 && !isLoading) {
    return (
      <div className="flex justify-center items-center py-20">
        <p className="text-gray-500 dark:text-gray-400">{t('reader.empty')}</p>
      </div>
    );
  }

  const sortedFiles = Array.from(loadedFiles.entries()).sort((a, b) => a[0] - b[0]);
  console.log('[DEBUG ReaderContent] sortedFiles:', sortedFiles.map(f => ({ fileIdx: f[0], len: f[1].charCount, fromSpan: f[1].fromSpan })));

  const editingAnchor = editingAnnotation?.anchor as TextSelectionAnchor | undefined;

  return (
    <div 
      className="reader-content-wrapper relative"
      style={{
        '--reader-font-size': `${fontSize}px`,
        '--reader-font-family': fontFamily === 'serif' ? "'Georgia', 'Songti SC', serif" : "'Inter', 'Helvetica Neue', 'PingFang SC', sans-serif"
      } as any}
    >
      <CitationPreview
        targetSpanId={citationTarget}
        onClose={() => setCitationTarget(null)}
      />

      <SelectionToolbar
        selectionRange={selectionRange}
        onHighlight={handleHighlight}
        onAnnotate={handleAnnotate}
        onCopy={handleCopy}
        onClose={handleCloseToolbar}
      />

      {showAnnotationDialog && (pendingAnnotation || editingAnnotation) && (
        <AnnotationDialog
          selectedText={editingAnnotation?.text || pendingAnnotation?.text || ''}
          initialNote={editingAnchor?.note}
          initialColorKey={editingAnchor?.color}
          isEditing={!!editingAnnotation}
          onSave={handleSaveAnnotation}
          onCancel={handleCancelAnnotation}
        />
      )}

      {highlightMenu && (
        <HighlightMenu
          annotationId={highlightMenu.annotationId}
          position={highlightMenu.position}
          hasNote={highlightMenu.hasNote}
          onDelete={handleDeleteAnnotation}
          onEdit={handleEditAnnotation}
          onClose={() => setHighlightMenu(null)}
        />
      )}

      {/* 顶部哨兵 */}
      <div ref={topSentinelRef} className="h-1" />

      {/* 渲染所有已加载的文件 */}
      {sortedFiles.map(([fileIdx, content]) => (
        <FileSection key={fileIdx} fileIdx={fileIdx} content={content} />
      ))}

      {/* 底部哨兵 */}
      <div ref={bottomSentinelRef} className="h-1" />

      {isLoading && (
        <div className="flex justify-center items-center py-8">
          <div className="text-gray-500 dark:text-gray-400">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-2" />
            <p className="text-sm">{t('reader.loading')}</p>
          </div>
        </div>
      )}

      <style>{`
        :root {
          --reading-bg: #fdfcf8;
          --reading-text: #2c2c2c;
          --reading-h1: #1a1a1a;
          --reading-h2: #222222;
          --reading-p: #3a3a3a;
          --reading-meta: #737373;
          --reading-border: rgba(0,0,0,0.06);
          --reading-highlight: rgba(255, 237, 160, 0.5);
          --reading-code-bg: rgba(0,0,0,0.04);
          --reading-code-text: #cc3344;
          --reading-quote-bg: rgba(0,0,0,0.02);
          --reading-quote-border: rgba(0,0,0,0.1);
        }
        
        :root.dark {
          --reading-bg: transparent;
          --reading-text: #ffffff;
          --reading-h1: #ffffff;
          --reading-h2: #f4f4f5;
          --reading-p: #e4e4e7;
          --reading-meta: #a1a1aa;
          --reading-border: rgba(255,255,255,0.15);
          --reading-highlight: rgba(168, 123, 25, 0.5);
          --reading-code-bg: rgba(255,255,255,0.1);
          --reading-code-text: #ff8f9c;
          --reading-quote-bg: rgba(255,255,255,0.05);
          --reading-quote-border: rgba(255,255,255,0.25);
        }

        .reader-content {
          -webkit-touch-callout: none;
          user-select: text;
          color: var(--reading-text);
          font-size: var(--reader-font-size, 18px);
          line-height: 1.9;
          font-weight: 400;
          letter-spacing: 0.02em;
          font-family: var(--reader-font-family, 'Georgia', 'Songti SC', serif);
        }
        .reader-file-section { margin-bottom: 3rem; }
        .reader-content p { margin-bottom: 1.4em; text-align: justify; color: var(--reading-p); }
        .reader-content h1 { font-family: 'Helvetica Neue', 'PingFang SC', sans-serif; font-size: 1.85em; font-weight: 600; color: var(--reading-h1); margin: 2.2em 0 0.9em; letter-spacing: 0.03em; }
        .reader-content h2 { font-family: 'Helvetica Neue', 'PingFang SC', sans-serif; font-size: 1.5em; font-weight: 600; color: var(--reading-h2); margin: 1.8em 0 0.75em; letter-spacing: 0.02em; }
        .reader-content h3 { font-family: 'Helvetica Neue', 'PingFang SC', sans-serif; font-size: 1.25em; font-weight: 500; color: var(--reading-h2); margin: 1.5em 0 0.6em; }
        .reader-content h4, .reader-content h5, .reader-content h6 { font-family: 'Helvetica Neue', 'PingFang SC', sans-serif; font-size: 1.1em; font-weight: 500; color: var(--reading-h1); margin: 1.2em 0 0.5em; }
        .reader-content strong { font-weight: 600; color: var(--reading-h1); }
        .reader-content em { font-style: italic; color: var(--reading-p); }
        .reader-content mark { background: linear-gradient(to bottom, transparent 50%, var(--reading-highlight) 50%); color: inherit; padding: 0; border-radius: 0; }
        .reader-content code { font-family: 'SF Mono', 'Monaco', 'Courier New', monospace; font-size: 0.88em; background-color: var(--reading-code-bg); color: var(--reading-code-text); padding: 0.15em 0.4em; border-radius: 4px; }
        .reader-content blockquote { margin: 1.5em 0; padding: 0.6em 1em; border-left: 3px solid var(--reading-quote-border); background-color: var(--reading-quote-bg); color: var(--reading-p); }
        .reader-content pre { margin: 1.5em 0; padding: 1.2em; background-color: var(--reading-code-bg); color: var(--reading-text); border-radius: 8px; overflow-x: auto; line-height: 1.6; border: 1px solid var(--reading-border); }
        .reader-content pre code { background: none; color: inherit; padding: 0; font-size: 0.9em; }
        .reader-content ul, .reader-content ol { margin: 1em 0; padding-left: 1.8em; }
        .reader-content li { margin-bottom: 0.4em; color: var(--reading-p); }
        .reader-content ul > li { list-style-type: disc; }
        .reader-content ol > li { list-style-type: decimal; }
        .reader-content table { width: 100%; margin: 1.5em 0; border-collapse: collapse; font-size: 0.94em; }
        .reader-content figure { margin: 2em 0; text-align: center; }
        .reader-content figcaption { margin-top: 0.8em; font-size: 0.9em; color: var(--reading-meta); font-family: 'Helvetica Neue', 'PingFang SC', sans-serif; }
        .reader-content a { color: var(--reading-p); text-decoration: none; word-break: break-word; border-bottom: 1px solid var(--reading-border); transition: all 0.2s ease; }
        .reader-content a:hover { color: var(--reading-h1); border-bottom-color: var(--reading-meta); }
        .reader-content a.citation-ref { color: var(--reading-p); cursor: pointer; border-bottom: 1px dashed var(--reading-border); }
        .reader-content hr { margin: 2.5em 0; border: none; height: 1px; background: linear-gradient(to right, transparent, var(--reading-border), transparent); }
        .reader-content section { margin-bottom: 2em; }
        @media (max-width: 640px) {
          .reader-content { font-size: 0.96em; line-height: 1.8; }
          .reader-content h1 { font-size: 1.6em; }
          .reader-content h2 { font-size: 1.4em; }
          .reader-content h3 { font-size: 1.2em; }
        }
      `}</style>
    </div>
  );
}
