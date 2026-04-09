/**
 * 阅读器顶部工具栏
 *
 * 包含：返回、目录切换、标题、翻译切换等
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { useReaderStore } from '../../store/reader';
import { translateFile } from '../../api/content';
import { ReaderSettingsMenu } from './ReaderSettingsMenu';

export function ReaderToolbar() {
  const navigate = useNavigate();
  const tocVisible = useReaderStore((state) => state.tocVisible);
  const toggleToc = useReaderStore((state) => state.toggleToc);
  const contentMeta = useReaderStore((state) => state.contentMeta);
  const contentId = useReaderStore((state) => state.contentId);
  const currentFileIdx = useReaderStore((state) => state.currentFileIdx);
  const lang = useReaderStore((state) => state.lang);
  const setLang = useReaderStore((state) => state.setLang);
  const reloadCurrentFile = useReaderStore((state) => state.reloadCurrentFile);
  const getCurrentLocation = useReaderStore((state) => state.getCurrentLocation);

  const [isTranslating, setIsTranslating] = useState(false);
  const [showSettings, setShowSettings] = useState(false);

  const title = contentMeta?.title;

  const handleToggleTranslation = async () => {
    if (!contentId) return;

    try {
      setIsTranslating(true);
      const currentLocation = getCurrentLocation?.();

      if (lang) {
        // Switch back to original
        setLang(null);
        await reloadCurrentFile?.(currentLocation || undefined);
      } else {
        // Trigger translation, then switch to translated
        const res = await translateFile(contentId, currentFileIdx);
        if (res.status === 'same_language') {
          toast.info('内容已是您的偏好语言');
          return;
        }
        setLang(res.lang);
        await reloadCurrentFile?.(currentLocation || undefined);
      }
    } catch (error) {
      console.error('Translation failed:', error);
    } finally {
      setIsTranslating(false);
    }
  };

  return (
    <div className="flex items-center justify-between px-4 py-3 bg-transparent">
      {/* 左侧：返回 + 目录按钮 */}
      <div className="flex items-center gap-2">
        <button
          onClick={() => navigate(-1)}
          className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
          title="返回"
        >
          <svg className="w-5 h-5 text-gray-700 dark:text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </button>

        <button
          onClick={toggleToc}
          className={`p-2 rounded-lg transition-colors ${tocVisible
            ? 'bg-blue-100 text-blue-600 dark:bg-blue-900 dark:text-blue-400'
            : 'hover:bg-gray-100 text-gray-700 dark:hover:bg-gray-800 dark:text-gray-300'}`}
          title="目录"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
      </div>

      {/* 中间：标题 */}
      {title && (
        <div className="hidden md:block flex-1 px-4">
          <h1 className="text-lg font-medium text-gray-900 dark:text-gray-100 truncate text-center">
            {title}
          </h1>
        </div>
      )}

      {/* 右侧：工具按钮 */}
      <div className="flex items-center gap-2">
        {/* 翻译按钮 */}
        <button
          onClick={handleToggleTranslation}
          disabled={isTranslating}
          className={`p-2 rounded-lg transition-colors ${lang
            ? 'bg-blue-100 text-blue-600 dark:bg-blue-900 dark:text-blue-400'
            : 'hover:bg-gray-100 text-gray-700 dark:hover:bg-gray-800 dark:text-gray-300'}
            ${isTranslating ? 'opacity-50' : ''}`}
          title={isTranslating ? '翻译中...' : lang ? '显示原文' : '翻译'}
        >
          {isTranslating ? (
            <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
          ) : (
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" />
            </svg>
          )}
        </button>

        {/* 设置按钮 */}
        <div className="relative">
          <button
            onClick={() => setShowSettings(!showSettings)}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors cursor-pointer"
            title="设置"
          >
            <svg className="w-5 h-5 text-gray-700 dark:text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </button>
          {showSettings && <ReaderSettingsMenu onClose={() => setShowSettings(false)} />}
        </div>
      </div>
    </div>
  );
}
