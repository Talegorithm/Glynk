/**
 * TOC（目录）工具函数
 */

import type { TOCItem, FlatTOCItem } from '../../types/reader';

/**
 * 将树形 TOC 扁平化为数组
 */
export function flattenTOC(toc: TOCItem[]): FlatTOCItem[] {
  const result: FlatTOCItem[] = [];
  let index = 0;

  function traverse(items: TOCItem[], depth: number) {
    items.forEach((item) => {
      result.push({
        ...item,
        index,
        depth,
      });
      index++;

      if (item.children && item.children.length > 0) {
        traverse(item.children, depth + 1);
      }
    });
  }

  traverse(toc, 0);
  return result;
}

/**
 * 根据当前 location 查找对应的 TOC 索引（用于高亮当前章节）
 */
export function findTOCIndex(
  flatToc: FlatTOCItem[],
  currentLocation: string
): number | null {
  for (let i = flatToc.length - 1; i >= 0; i--) {
    if (flatToc[i].href <= currentLocation) {
      return i;
    }
  }
  return flatToc.length > 0 ? 0 : null;
}
