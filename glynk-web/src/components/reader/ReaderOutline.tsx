/**
 * 阅读器大纲侧边栏（AI生成的内容结构）
 *
 * 核心逻辑：
 * - 默认全部折叠，仅展开当前阅读位置的路径
 * - 只在最深层级（叶子节点或已折叠的节点）显示描述
 * - 描述完整显示，不截断
 */

import { useState, useEffect, useMemo } from 'react';
import { useReaderStore } from '../../store/reader';
import type { OutlineItem } from '../../types/reader';

export function ReaderOutline() {
  const outline = useReaderStore((state) => state.outline);
  const contentId = useReaderStore((state) => state.contentId);
  const jumpToLocation = useReaderStore((state) => state.jumpToLocation);
  const toggleToc = useReaderStore((state) => state.toggleToc);
  const isLoading = useReaderStore((state) => state.isLoading);

  const [collapsed, setCollapsed] = useState<Set<string>>(new Set());
  const [manuallyExpanded, setManuallyExpanded] = useState<Set<string>>(new Set());
  const [currentLocation, setCurrentLocation] = useState<string | null>(null);

  // 构建 location -> 路径映射（用于展开当前位置的父级）
  const locationPathMap = useMemo(() => {
    const map = new Map<string, string[]>();

    const buildPathMap = (items: OutlineItem[], path: string[] = []) => {
      items.forEach((item, index) => {
        const parentKey = path.length > 0 ? path[path.length - 1] : '';
        const itemKey = parentKey ? `${parentKey}-${item.title}` : `root-${index}-${item.title}`;
        const currentPath = [...path, itemKey];

        if (item.location) {
          map.set(item.location, currentPath);
        }

        if (item.children && item.children.length > 0) {
          buildPathMap(item.children, currentPath);
        }
      });
    };

    buildPathMap(outline);
    return map;
  }, [outline]);

  const handleToggleCollapse = (itemKey: string) => {
    setCollapsed((prev) => {
      const next = new Set(prev);
      const wasCollapsed = next.has(itemKey);

      if (wasCollapsed) {
        next.delete(itemKey);
        setManuallyExpanded((prevExpanded) => {
          const nextExpanded = new Set(prevExpanded);
          nextExpanded.add(itemKey);
          return nextExpanded;
        });
      } else {
        next.add(itemKey);
        setManuallyExpanded((prevExpanded) => {
          const nextExpanded = new Set(prevExpanded);
          nextExpanded.delete(itemKey);
          return nextExpanded;
        });
      }

      return next;
    });
  };

  const handleOutlineClick = async (location?: string) => {
    if (!location || !contentId) return;

    await jumpToLocation(location);

    // 移动端点击后关闭抽屉
    if (window.innerWidth < 768) {
      toggleToc();
    }
  };

  // 监听滚动位置，更新当前大纲高亮
  useEffect(() => {
    const scrollContainer = document.querySelector('[data-reader-scroll]');
    if (!scrollContainer || outline.length === 0) return;

    // 收集所有大纲的 location
    const allLocations: string[] = [];
    const collectLocations = (items: OutlineItem[]) => {
      items.forEach((item) => {
        if (item.location) {
          allLocations.push(item.location);
        }
        if (item.children && item.children.length > 0) {
          collectLocations(item.children);
        }
      });
    };
    collectLocations(outline);

    const handleScroll = () => {
      const containerRect = scrollContainer.getBoundingClientRect();
      const viewportTop = containerRect.top;
      const viewportCenter = viewportTop + containerRect.height / 3;

      let closestLocation: string | null = null;
      let closestDistance = Infinity;

      allLocations.forEach((location) => {
        const element = document.getElementById(location);
        if (element) {
          const rect = element.getBoundingClientRect();
          const distance = Math.abs(rect.top - viewportCenter);

          if (rect.top <= viewportCenter && distance < closestDistance) {
            closestDistance = distance;
            closestLocation = location;
          }
        }
      });

      if (closestLocation !== currentLocation) {
        setCurrentLocation(closestLocation);
      }
    };

    handleScroll();

    scrollContainer.addEventListener('scroll', handleScroll);
    return () => {
      scrollContainer.removeEventListener('scroll', handleScroll);
    };
  }, [outline, currentLocation]);

  // 当 currentLocation 变化时,自动展开其路径并折叠其他(但保留用户手动展开的节点)
  useEffect(() => {
    if (!currentLocation) return;

    const path = locationPathMap.get(currentLocation);
    if (!path) return;

    setCollapsed(() => {
      // 1. 收集所有可折叠的节点
      const allKeys = new Set<string>();
      const collectAllKeys = (items: OutlineItem[], parentKey: string = '') => {
        items.forEach((item) => {
          const itemKey = `${parentKey}-${item.title}`;
          if (item.children && item.children.length > 0) {
            allKeys.add(itemKey);
            collectAllKeys(item.children, itemKey);
          }
        });
      };
      outline.forEach((item, index) => collectAllKeys([item], `root-${index}`));

      // 2. 默认全部折叠
      const next = new Set(allKeys);

      // 3. 展开当前路径
      path.forEach((key) => {
        next.delete(key);
      });

      // 4. 展开用户手动展开的节点
      manuallyExpanded.forEach((key) => {
        next.delete(key);
      });

      return next;
    });

    // 滚动高亮项到视野内
    setTimeout(() => {
      const activeElement = document.querySelector(
        '.outline-item [data-active="true"]'
      ) as HTMLElement;
      if (activeElement) {
        activeElement.scrollIntoView({
          behavior: 'smooth',
          block: 'nearest',
          inline: 'nearest',
        });
      }
    }, 100);
  }, [currentLocation, locationPathMap, outline, manuallyExpanded]);

  // 加载中
  if (isLoading && outline.length === 0) {
    return (
      <div className="flex justify-center items-center py-8">
        <div className="text-gray-500 dark:text-gray-400 text-sm">加载大纲中...</div>
      </div>
    );
  }

  // 大纲为空
  if (outline.length === 0) {
    return (
      <div className="flex justify-center items-center py-8">
        <div className="text-gray-400 dark:text-gray-500 text-sm">暂无大纲</div>
      </div>
    );
  }

  // 递归渲染大纲项
  const renderOutlineItem = (item: OutlineItem, level: number = 0, parentKey: string = '') => {
    const itemKey = `${parentKey}-${item.title}`;
    const hasChildren = item.children && item.children.length > 0;
    const isCollapsed = collapsed.has(itemKey);
    const isActive = item.location === currentLocation;

    // 只在叶子节点或已折叠的节点显示描述
    const shouldShowDescription = !hasChildren || isCollapsed;

    return (
      <div key={itemKey} className="outline-item">
        <div
          data-active={isActive}
          className={`py-2 px-3 transition-colors group ${
            isActive
              ? 'bg-blue-50 dark:bg-blue-900/30 border-l-2 border-blue-600 dark:border-blue-400'
              : 'hover:bg-gray-50 dark:hover:bg-gray-800 border-l-2 border-transparent'
          }`}
          style={{ paddingLeft: `${12 + level * 16}px` }}
        >
          {/* 折叠按钮和标题 */}
          <div className="flex items-start gap-1">
            {hasChildren && (
              <button
                onClick={() => handleToggleCollapse(itemKey)}
                className={`flex-shrink-0 w-4 h-4 flex items-center justify-center transition-colors mt-0.5 ${
                  isActive
                    ? 'text-blue-600 dark:text-blue-400'
                    : 'text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300'
                }`}
              >
                {isCollapsed ? '\u25B8' : '\u25BE'}
              </button>
            )}
            {!hasChildren && <span className="flex-shrink-0 w-4" />}

            <div className="flex-1 min-w-0">
              {/* 标题按钮 */}
              <button
                onClick={() => handleOutlineClick(item.location)}
                className={`w-full text-left text-sm font-medium transition-colors ${
                  isActive
                    ? 'text-blue-600 dark:text-blue-400'
                    : 'text-gray-700 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400'
                }`}
              >
                {item.title}
              </button>

              {/* 描述文本（智能显示）*/}
              {shouldShowDescription && item.description && (
                <p className="mt-1 text-xs text-gray-500 dark:text-gray-400 leading-relaxed whitespace-pre-wrap">
                  {item.description}
                </p>
              )}
            </div>
          </div>
        </div>

        {hasChildren && !isCollapsed && (
          <div className="outline-children">
            {item.children!.map((child) => renderOutlineItem(child, level + 1, itemKey))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="py-4">
      <div className="px-4 mb-4">
        <h2 className="text-sm font-bold text-gray-700 dark:text-gray-300 uppercase tracking-wide">
          大纲
        </h2>
      </div>

      <nav className="space-y-0.5">
        {outline.map((item, index) => renderOutlineItem(item, 0, `root-${index}`))}
      </nav>
    </div>
  );
}
