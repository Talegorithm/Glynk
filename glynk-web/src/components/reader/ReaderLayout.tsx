/**
 * 阅读器布局容器（连续滚动模式）
 *
 * 响应式设计：
 * - 桌面端：左侧 TOC/大纲切换（可调整宽度）+ 中间内容（连续滚动）+ 工具栏
 * - 移动端：全屏内容（连续滚动）+ 抽屉 TOC/大纲
 */

import { type ReactNode, useState, useRef, useEffect } from 'react';
import { useReaderStore } from '../../store/reader';

interface ReaderLayoutProps {
  toolbar: ReactNode;     // 顶部工具栏
  toc: ReactNode;         // 目录组件
  outline: ReactNode;     // 大纲组件
  content: ReactNode;     // 内容组件（连续滚动）
}

export function ReaderLayout({ toolbar, toc, outline, content }: ReaderLayoutProps) {
  const tocVisible = useReaderStore((state) => state.tocVisible);
  const toggleToc = useReaderStore((state) => state.toggleToc);

  // Tab 状态：'toc' | 'outline'（默认大纲）
  const [activeTab, setActiveTab] = useState<'toc' | 'outline'>('outline');

  // 侧边栏宽度（响应式）
  const [sidebarWidth, setSidebarWidth] = useState(() => {
    const screenWidth = window.innerWidth;
    return Math.max(300, Math.min(600, screenWidth * 0.2));
  });
  const isResizing = useRef(false);
  const startX = useRef(0);
  const startWidth = useRef(0);

  // 拖拽开始
  const handleMouseDown = (e: React.MouseEvent) => {
    isResizing.current = true;
    startX.current = e.clientX;
    startWidth.current = sidebarWidth;
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
  };

  // 拖拽中 + 拖拽结束 + 窗口 resize
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing.current) return;

      const delta = e.clientX - startX.current;
      const newWidth = Math.max(200, Math.min(800, startWidth.current + delta));
      setSidebarWidth(newWidth);
    };

    const handleMouseUp = () => {
      if (isResizing.current) {
        isResizing.current = false;
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
      }
    };

    const handleResize = () => {
      if (!isResizing.current) {
        const screenWidth = window.innerWidth;
        const newWidth = Math.max(300, Math.min(600, screenWidth * 0.2));
        setSidebarWidth(newWidth);
      }
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
    window.addEventListener('resize', handleResize);

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      window.removeEventListener('resize', handleResize);
    };
  }, []);

  return (
    <div className="flex flex-col h-[calc(100vh-57px)] relative overflow-hidden bg-transparent">
      {/* Remove the hardcoded subtle background gradient so we can see the glorious dynamic sky */}
      <div className="absolute inset-0 bg-white/30 dark:bg-gray-900/40 pointer-events-none" />

      {/* 顶部工具栏 - 毛玻璃 */}
      <div className="flex-shrink-0 relative z-20 bg-white/70 dark:bg-gray-900/70 backdrop-blur-md border-b border-gray-200/50 dark:border-gray-700/50 shadow-sm">
        {toolbar}
      </div>

      {/* 主内容区 */}
      <div className="flex flex-1 overflow-hidden relative z-10">
        {/* 目录/大纲侧边栏（桌面端）- 毛玻璃 */}
        {tocVisible && (
          <div
            className="hidden md:flex flex-col flex-shrink-0 bg-white/60 dark:bg-gray-900/60 backdrop-blur-lg border-r border-gray-200/50 dark:border-gray-700/50 relative shadow-[4px_0_24px_rgba(0,0,0,0.02)]"
            style={{ width: `${sidebarWidth}px` }}
          >
            {/* Tab 切换器 */}
            <div className="sticky top-0 bg-transparent border-b border-gray-200/50 dark:border-gray-700/50 px-4 py-3 flex gap-2 z-10">
              <button
                onClick={() => setActiveTab('toc')}
                className={`flex-1 px-3 py-1.5 text-sm font-medium rounded transition-all duration-200 ${
                  activeTab === 'toc'
                    ? 'bg-blue-100/80 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300 shadow-sm'
                    : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100/80 dark:hover:bg-gray-800/80'
                }`}
              >
                目录
              </button>
              <button
                onClick={() => setActiveTab('outline')}
                className={`flex-1 px-3 py-1.5 text-sm font-medium rounded transition-all duration-200 ${
                  activeTab === 'outline'
                    ? 'bg-blue-100/80 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300 shadow-sm'
                    : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100/80 dark:hover:bg-gray-800/80'
                }`}
              >
                大纲
              </button>
            </div>

            {/* 内容区（可滚动）*/}
            <div className="flex-1 overflow-y-auto">
              {activeTab === 'toc' ? toc : outline}
            </div>

            {/* 拖拽分隔条 */}
            <div
              onMouseDown={handleMouseDown}
              className="absolute right-0 top-0 bottom-0 w-1 cursor-col-resize hover:bg-blue-500/80 dark:hover:bg-blue-400/80 transition-colors"
              style={{ touchAction: 'none' }}
            />
          </div>
        )}

        {/* 内容区（连续滚动）- 保持纯净无毛玻璃 */}
        <div
          className="flex-1 overflow-y-auto reader-content-scroll scroll-smooth"
          data-reader-scroll
        >
          <div className="max-w-4xl mx-auto px-6 md:px-8 py-8">
            {content}
          </div>
        </div>
      </div>

      {/* 移动端目录/大纲抽屉 */}
      {tocVisible && (
        <div
          className="md:hidden fixed inset-0 z-50 bg-black/50"
          onClick={toggleToc}
        >
          <div
            className="absolute left-0 top-0 bottom-0 w-80 max-w-full bg-white dark:bg-gray-900 shadow-xl overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            {/* 头部：关闭按钮 + Tab 切换 */}
            <div className="sticky top-0 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 z-10">
              <div className="px-4 py-3 flex justify-between items-center">
                <span className="font-bold text-lg text-gray-900 dark:text-gray-100">
                  {activeTab === 'toc' ? '目录' : '大纲'}
                </span>
                <button
                  onClick={toggleToc}
                  className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg text-gray-600 dark:text-gray-400"
                >
                  ✕
                </button>
              </div>

              {/* Tab 切换器 */}
              <div className="px-4 pb-3 flex gap-2">
                <button
                  onClick={() => setActiveTab('toc')}
                  className={`flex-1 px-3 py-1.5 text-sm font-medium rounded transition-colors ${
                    activeTab === 'toc'
                      ? 'bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300'
                      : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'
                  }`}
                >
                  目录
                </button>
                <button
                  onClick={() => setActiveTab('outline')}
                  className={`flex-1 px-3 py-1.5 text-sm font-medium rounded transition-colors ${
                    activeTab === 'outline'
                      ? 'bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300'
                      : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'
                  }`}
                >
                  大纲
                </button>
              </div>
            </div>

            {/* 内容区 */}
            {activeTab === 'toc' ? toc : outline}
          </div>
        </div>
      )}
    </div>
  );
}
