import { useRef, useEffect } from 'react';
import { useThemeStore } from '../../store/theme';
import { useReaderSettingsStore } from '../../store/readerSettings';
import { useReaderStore } from '../../store/reader';
import { useT } from '../../i18n';

interface ReaderSettingsMenuProps {
  onClose: () => void;
}

export function ReaderSettingsMenu({ onClose }: ReaderSettingsMenuProps) {
  const t = useT();
  const menuRef = useRef<HTMLDivElement>(null);
  const { theme, setTheme } = useThemeStore();
  const { fontSize, fontFamily, setFontSize, setFontFamily } = useReaderSettingsStore();
  const getCurrentLocation = useReaderStore((state) => state.getCurrentLocation);

  const handleFontSizeChange = (newSize: number) => {
    const loc = getCurrentLocation();
    setFontSize(newSize);
    
    // Anchor scroll after DOM reflow
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        if (!loc) return;
        const targetSpan = document.getElementById(loc);
        const scrollContainer = document.querySelector('[data-reader-scroll]');
        if (targetSpan && scrollContainer) {
          const containerRect = scrollContainer.getBoundingClientRect();
          const elementRect = targetSpan.getBoundingClientRect();
          const scrollOffset = scrollContainer.scrollTop + (elementRect.top - containerRect.top) - 100;
          scrollContainer.scrollTo({ top: scrollOffset, behavior: 'instant' });
        }
      });
    });
  };

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        onClose();
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [onClose]);

  return (
    <div
      ref={menuRef}
      className="absolute right-4 top-14 w-72 glass-panel rounded-2xl p-4 shadow-2xl z-50 animate-in fade-in slide-in-from-top-4 duration-200"
    >
      <div className="flex flex-col gap-5">
        {/* Theme Settings */}
        <div>
          <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2 block">{t('settings.appearance')}</span>
          <div className="flex bg-gray-100/50 dark:bg-gray-800/50 rounded-xl p-1 gap-1">
            <button
              onClick={() => setTheme('light')}
              className={`flex-1 flex justify-center py-1.5 rounded-lg text-sm font-medium transition-all ${
                theme === 'light' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
              }`}
            >
              {t('settings.theme.light')}
            </button>
            <button
              onClick={() => setTheme('dark')}
              className={`flex-1 flex justify-center py-1.5 rounded-lg text-sm font-medium transition-all ${
                theme === 'dark' ? 'bg-gray-900 text-white shadow-sm' : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
              }`}
            >
              {t('settings.theme.dark')}
            </button>
            <button
              onClick={() => setTheme('sky')}
              className={`flex-1 flex justify-center py-1.5 rounded-lg text-sm font-medium transition-all ${
                theme === 'sky' ? 'bg-blue-500 text-white shadow-sm' : 'text-gray-500 hover:text-blue-500'
              }`}
            >
              {t('settings.theme.auto')}
            </button>
          </div>
        </div>

        {/* Typography */}
        <div>
          <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2 block">{t('settings.font')}</span>
          <div className="flex bg-gray-100/50 dark:bg-gray-800/50 rounded-xl p-1 gap-1 mb-3">
            <button
              onClick={() => setFontFamily('sans-serif')}
              className={`flex-1 py-1.5 rounded-lg text-sm font-medium transition-all ${
                fontFamily === 'sans-serif' ? 'bg-white dark:bg-gray-700 shadow-sm text-gray-900 dark:text-gray-100' : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
              }`}
            >
              {t('settings.font.sans')}
            </button>
            <button
              onClick={() => setFontFamily('serif')}
              className={`flex-1 py-1.5 rounded-lg text-sm font-medium transition-all ${
                fontFamily === 'serif' ? 'bg-white dark:bg-gray-700 shadow-sm text-gray-900 dark:text-gray-100' : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
              }`}
            >
              {t('settings.font.serif')}
            </button>
          </div>

          {/* Font Size */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => handleFontSizeChange(fontSize - 1)}
              className="flex-1 py-2 bg-gray-100/50 dark:bg-gray-800/50 hover:bg-gray-200/50 dark:hover:bg-gray-700/50 rounded-xl text-gray-700 dark:text-gray-300 transition-colors flex justify-center items-center font-medium"
            >
              A-
            </button>
            <span className="text-sm font-medium text-gray-600 dark:text-gray-400 w-8 text-center">{fontSize}</span>
            <button
              onClick={() => handleFontSizeChange(fontSize + 1)}
              className="flex-1 py-2 bg-gray-100/50 dark:bg-gray-800/50 hover:bg-gray-200/50 dark:hover:bg-gray-700/50 rounded-xl text-gray-700 dark:text-gray-300 transition-colors flex justify-center items-center font-medium text-lg"
            >
              A+
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
