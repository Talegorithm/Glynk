/**
 * 阅读器目录侧边栏（连续滚动模式）
 *
 * 支持嵌套目录的折叠/展开
 * 点击目录项跳转到对应 span_id
 * 高亮当前阅读位置对应的 TOC 项
 *
 * 从 Brainow 迁移，适配 Glynk TOCItem（使用 href 字段）
 */

import { useState, useEffect } from 'react';
import { useReaderStore } from '../../store/reader';
import type { TOCItem } from '../../types/reader';
import { useT } from '../../i18n';

export function ReaderTOC() {
  const t = useT();
  const toc = useReaderStore((state) => state.toc);
  const flatToc = useReaderStore((state) => state.flatToc);
  const isLoading = useReaderStore((state) => state.isLoading);
  const jumpToLocation = useReaderStore((state) => state.jumpToLocation);
  const toggleToc = useReaderStore((state) => state.toggleToc);

  const [collapsed, setCollapsed] = useState<Set<string>>(new Set());
  const [currentLocation, setCurrentLocation] = useState<string | null>(null);

  const handleToggleCollapse = (itemKey: string) => {
    setCollapsed((prev) => {
      const next = new Set(prev);
      if (next.has(itemKey)) {
        next.delete(itemKey);
      } else {
        next.add(itemKey);
      }
      return next;
    });
  };

  const handleTocClick = async (href: string) => {
    if (!href) return;

    // 跳转到 TOC 项的 href (span_id)
    await jumpToLocation(href);

    // 移动端点击后关闭抽屉
    if (window.innerWidth < 768) {
      toggleToc();
    }
  };

  // 监听滚动位置，更新当前 TOC 高亮
  useEffect(() => {
    const scrollContainer = document.querySelector('[data-reader-scroll]');
    if (!scrollContainer || toc.length === 0) return;

    // 从 flatToc 收集所有 href
    const allAnchors: string[] = flatToc
      .map((item) => item.href)
      .filter(Boolean);

    if (allAnchors.length === 0) {
      // 回退：递归收集
      const collected: string[] = [];
      const collect = (items: TOCItem[]) => {
        items.forEach((item) => {
          if (item.href) collected.push(item.href);
          if (item.children?.length) collect(item.children);
        });
      };
      collect(toc);
      allAnchors.push(...collected);
    }

    const handleScroll = () => {
      const containerRect = scrollContainer.getBoundingClientRect();
      const viewportCenter = containerRect.top + containerRect.height / 3;

      let closestAnchor: string | null = null;
      let closestDistance = Infinity;

      allAnchors.forEach((anchor) => {
        const element = document.getElementById(anchor);
        if (element) {
          const rect = element.getBoundingClientRect();
          const distance = Math.abs(rect.top - viewportCenter);

          // 只考虑在视口上方或视口内的元素
          if (rect.top <= viewportCenter && distance < closestDistance) {
            closestDistance = distance;
            closestAnchor = anchor;
          }
        }
      });

      if (closestAnchor !== currentLocation) {
        setCurrentLocation(closestAnchor);
      }
    };

    // 初始检查
    handleScroll();

    scrollContainer.addEventListener('scroll', handleScroll);
    return () => {
      scrollContainer.removeEventListener('scroll', handleScroll);
    };
  }, [toc, flatToc, currentLocation]);

  // 当 currentLocation 变化时，滚动高亮项到视野内
  useEffect(() => {
    if (!currentLocation) return;

    setTimeout(() => {
      const activeElement = document.querySelector(
        '.toc-item [data-active="true"]'
      ) as HTMLElement;
      if (activeElement) {
        activeElement.scrollIntoView({
          behavior: 'smooth',
          block: 'nearest',
          inline: 'nearest',
        });
      }
    }, 100);
  }, [currentLocation]);

  // 加载中
  if (isLoading && toc.length === 0) {
    return (
      <div className="flex justify-center items-center py-8">
        <div className="text-gray-500 dark:text-gray-400 text-sm">{t('reader.toc.loading')}</div>
      </div>
    );
  }

  // 目录为空
  if (toc.length === 0) {
    return (
      <div className="flex justify-center items-center py-8">
        <div className="text-gray-400 dark:text-gray-500 text-sm">{t('reader.toc.empty')}</div>
      </div>
    );
  }

  // 递归渲染 TOC 项
  const renderTOCItem = (item: TOCItem, level: number = 0, parentKey: string = '') => {
    const itemKey = `${parentKey}-${item.title}`;
    const hasChildren = item.children && item.children.length > 0;
    const isCollapsed = collapsed.has(itemKey);
    const isActive = item.href === currentLocation;

    return (
      <div key={itemKey} className="toc-item">
        <div
          data-active={isActive}
          className={`flex items-center py-1.5 px-3 transition-all duration-200 group relative ${
            isActive
              ? 'bg-blue-500/10 border-l-2 border-blue-500 dark:bg-blue-400/10 dark:border-blue-400 font-medium'
              : 'hover:bg-gray-500/10 border-l-2 border-transparent hover:border-gray-300/50'
          }`}
          style={{ paddingLeft: `${12 + level * 16}px` }}
        >
          {hasChildren && (
            <button
              onClick={() => handleToggleCollapse(itemKey)}
              className={`mr-1 w-4 h-4 flex items-center justify-center transition-colors ${
                isActive
                  ? 'text-blue-600 dark:text-blue-400'
                  : 'text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300'
              }`}
            >
              {isCollapsed ? '\u25B8' : '\u25BE'}
            </button>
          )}
          {!hasChildren && <span className="mr-1 w-4" />}

          <button
            onClick={() => handleTocClick(item.href)}
            className={`flex-1 text-left text-sm transition-colors truncate ${
              isActive
                ? 'text-blue-600 font-medium dark:text-blue-400'
                : 'text-gray-700 hover:text-blue-600 dark:text-gray-300 dark:hover:text-blue-400'
            }`}
          >
            {item.title}
          </button>
        </div>

        {hasChildren && !isCollapsed && (
          <div className="toc-children">
            {item.children!.map((child, idx) =>
              renderTOCItem(child, level + 1, `${itemKey}-${idx}`)
            )}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="py-4">
      <div className="px-4 mb-4">
        <h2 className="text-sm font-bold text-gray-700 dark:text-gray-300 uppercase tracking-wide">
          {t('reader.toc')}
        </h2>
      </div>

      <nav className="space-y-0.5">
        {toc.map((item, index) => renderTOCItem(item, 0, `root-${index}`))}
      </nav>
    </div>
  );
}
