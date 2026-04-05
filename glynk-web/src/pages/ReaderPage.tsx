import { useEffect, useState, useCallback, useRef } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import { toast } from 'sonner';
import { readContent, getOutline } from '../api/content';
import { createAnnotation } from '../api/annotation';
import type { ReadResponse, OutlineItem } from '../types/content';

interface FloatingToolbar {
  top: number;
  left: number;
  text: string;
}

export default function ReaderPage() {
  const { contentId, fileIdx } = useParams<{ contentId: string; fileIdx: string }>();
  const [searchParams] = useSearchParams();
  const spanId = searchParams.get('loc');

  const [data, setData] = useState<ReadResponse | null>(null);
  const [outline, setOutline] = useState<OutlineItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [toolbar, setToolbar] = useState<FloatingToolbar | null>(null);
  const [noteText, setNoteText] = useState('');
  const [showNoteInput, setShowNoteInput] = useState(false);
  const contentRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!contentId) return;

    setLoading(true);
    const fileIdxNum = fileIdx != null ? Number(fileIdx) : undefined;

    Promise.all([
      readContent(contentId, fileIdxNum != null ? { from: fileIdxNum } : undefined),
      getOutline(contentId),
    ])
      .then(([readRes, outlineRes]) => {
        setData(readRes);
        setOutline(outlineRes);
      })
      .catch(() => toast.error('加载内容失败'))
      .finally(() => setLoading(false));
  }, [contentId, fileIdx]);

  // Scroll to span on load
  useEffect(() => {
    if (!spanId || !data) return;
    const el = document.getElementById(spanId);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'center' });
      el.classList.add('bg-yellow-100', 'dark:bg-yellow-900/30');
    }
  }, [spanId, data]);

  const handleMouseUp = useCallback(() => {
    const selection = window.getSelection();
    if (!selection || selection.isCollapsed || !selection.toString().trim()) {
      setToolbar(null);
      setShowNoteInput(false);
      return;
    }

    const range = selection.getRangeAt(0);
    const rect = range.getBoundingClientRect();
    setToolbar({
      top: rect.top + window.scrollY - 48,
      left: rect.left + rect.width / 2,
      text: selection.toString().trim(),
    });
    setShowNoteInput(false);
    setNoteText('');
  }, []);

  async function handleHighlight() {
    if (!toolbar || !contentId) return;
    try {
      await createAnnotation({
        content_id: contentId,
        type: 'highlight',
        text: toolbar.text,
      });
      toast.success('已高亮');
      setToolbar(null);
    } catch {
      toast.error('保存失败');
    }
  }

  async function handleNote() {
    if (!showNoteInput) {
      setShowNoteInput(true);
      return;
    }
    if (!toolbar || !contentId) return;
    try {
      await createAnnotation({
        content_id: contentId,
        type: 'note',
        text: toolbar.text,
        note: noteText,
      });
      toast.success('已保存笔记');
      setToolbar(null);
      setShowNoteInput(false);
      setNoteText('');
    } catch {
      toast.error('保存失败');
    }
  }

  function scrollToAnchor(anchor?: string) {
    if (!anchor) return;
    const el = document.getElementById(anchor);
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-32">
        <p className="text-sm text-gray-400 dark:text-gray-500">加载中...</p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex items-center justify-center py-32">
        <p className="text-sm text-gray-400 dark:text-gray-500">内容未找到</p>
      </div>
    );
  }

  return (
    <div className="flex min-h-[calc(100vh-57px)]">
      {/* Sidebar */}
      {sidebarOpen && outline.length > 0 && (
        <aside className="w-64 shrink-0 border-r border-gray-200 dark:border-gray-800 p-4 overflow-y-auto hidden md:block">
          <h2 className="text-xs font-medium tracking-widest uppercase text-gray-400 dark:text-gray-500 mb-4">
            目录
          </h2>
          <nav className="space-y-1">
            {outline.map((item) => (
              <button
                key={item.id}
                onClick={() => scrollToAnchor(item.anchor)}
                className="block w-full text-left text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 truncate cursor-pointer py-0.5 transition-colors"
                style={{ paddingLeft: `${(item.level - 1) * 12}px` }}
              >
                {item.title}
              </button>
            ))}
          </nav>
        </aside>
      )}

      {/* Main content */}
      <div className="flex-1 max-w-3xl mx-auto px-6 md:px-12 py-10 relative">
        {/* Toggle sidebar on mobile */}
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="md:hidden mb-4 text-xs text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 cursor-pointer"
        >
          {sidebarOpen ? '隐藏目录' : '显示目录'}
        </button>

        {/* Title */}
        <header className="mb-8">
          <h1 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 leading-tight">
            {data.title}
          </h1>
          {data.author && (
            <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">{data.author}</p>
          )}
        </header>

        {/* Content */}
        <div
          ref={contentRef}
          onMouseUp={handleMouseUp}
          className="prose prose-gray dark:prose-invert max-w-none text-base leading-relaxed"
          dangerouslySetInnerHTML={{ __html: data.body }}
        />

        {/* Floating toolbar */}
        {toolbar && (
          <div
            className="fixed z-50 flex items-center gap-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg px-2 py-1.5"
            style={{
              top: `${toolbar.top}px`,
              left: `${toolbar.left}px`,
              transform: 'translateX(-50%)',
            }}
          >
            <button
              onClick={handleHighlight}
              className="px-3 py-1 text-xs text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded cursor-pointer"
            >
              高亮
            </button>
            <button
              onClick={handleNote}
              className="px-3 py-1 text-xs text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded cursor-pointer"
            >
              笔记
            </button>
            {showNoteInput && (
              <input
                value={noteText}
                onChange={(e) => setNoteText(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter') handleNote(); }}
                placeholder="写笔记..."
                autoFocus
                className="ml-1 px-2 py-1 text-xs border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 focus:outline-none w-40"
              />
            )}
          </div>
        )}
      </div>
    </div>
  );
}
