/**
 * 文本选择和 span_id 提取工具
 * 从 Brainow 迁移，去除 iOS debug 日志
 */

/**
 * 选中文本的范围信息
 */
export interface SelectionRange {
  text: string;              // 选中的文本
  spanIds: string[];         // 涉及的所有 span_id（按顺序）
  startSpanId: string;       // 起始 span_id
  endSpanId: string;         // 结束 span_id
  startOffset: number;       // 起始字符偏移量（相对于 startSpan 的文本内容）
  endOffset: number;         // 结束字符偏移量（相对于 endSpan 的文本内容）
  boundingRect: DOMRect;     // 选中区域的边界框（用于定位工具栏）
}

/**
 * 获取当前选中文本的范围信息
 */
export function getSelectionRange(): SelectionRange | null {
  const selection = window.getSelection();

  if (!selection || selection.isCollapsed || selection.rangeCount === 0) {
    return null;
  }

  const range = selection.getRangeAt(0);
  const text = selection.toString().trim();

  if (!text) {
    return null;
  }

  // 收集所有涉及的 span 元素
  const spans = collectSpansInRange(range);

  if (spans.length === 0) {
    return null;
  }

  // 提取所有 span_id
  const spanIds = spans
    .map(span => span.id)
    .filter(id => id);

  if (spanIds.length === 0) {
    return null;
  }

  // 计算起始和结束偏移量
  const startSpan = spans[0];
  const endSpan = spans[spans.length - 1];

  const startOffset = calculateOffset(range.startContainer, range.startOffset, startSpan);
  const endOffset = calculateOffset(range.endContainer, range.endOffset, endSpan);

  // 获取选中区域的边界框
  const boundingRect = range.getBoundingClientRect();

  return {
    text,
    spanIds,
    startSpanId: spanIds[0],
    endSpanId: spanIds[spanIds.length - 1],
    startOffset,
    endOffset,
    boundingRect,
  };
}

/**
 * 计算文本节点在 span 元素中的字符偏移量
 */
function calculateOffset(
  node: Node,
  offset: number,
  spanElement: HTMLElement
): number {
  const spanText = spanElement.textContent || '';

  if (node === spanElement) {
    return offset;
  }

  let currentOffset = 0;
  const walker = document.createTreeWalker(
    spanElement,
    NodeFilter.SHOW_TEXT,
    null
  );

  let currentNode = walker.nextNode();
  while (currentNode) {
    if (currentNode === node) {
      return currentOffset + offset;
    }
    currentOffset += currentNode.textContent?.length || 0;
    currentNode = walker.nextNode();
  }

  return spanText.length;
}

/**
 * 收集 Range 中的所有 span 元素
 */
function collectSpansInRange(range: Range): HTMLElement[] {
  const spans: HTMLElement[] = [];
  const container = range.commonAncestorContainer;

  const containerElement = container.nodeType === Node.ELEMENT_NODE
    ? container as HTMLElement
    : container.parentElement;

  if (!containerElement) {
    return spans;
  }

  // 查找所有 span 元素
  let allSpans = containerElement.querySelectorAll('span[id]');

  // 如果容器内没有找到，尝试向上查找到 reader-content
  if (allSpans.length === 0) {
    const readerContent = containerElement.closest('.reader-content');
    if (readerContent) {
      allSpans = readerContent.querySelectorAll('span[id]');
    }
  }

  // 检查每个 span 是否与选中范围相交
  allSpans.forEach((span) => {
    if (isNodeInRange(span, range)) {
      spans.push(span as HTMLElement);
    }
  });

  return spans;
}

/**
 * 检查节点是否在 Range 范围内
 */
function isNodeInRange(node: Node, range: Range): boolean {
  try {
    const nodeRange = document.createRange();
    nodeRange.selectNode(node);
    const startToEnd = range.compareBoundaryPoints(Range.START_TO_END, nodeRange);
    const endToStart = range.compareBoundaryPoints(Range.END_TO_START, nodeRange);
    return startToEnd > 0 && endToStart < 0;
  } catch {
    return false;
  }
}

/**
 * 清除当前选中状态
 */
export function clearSelection(): void {
  const selection = window.getSelection();
  if (selection) {
    selection.removeAllRanges();
  }
}

/**
 * 根据 span_id 范围和字符偏移量精确高亮文本
 */
export function highlightSpanRange(
  startSpanId: string,
  endSpanId: string,
  startOffset: number,
  endOffset: number,
  color: string = 'rgba(255, 237, 160, 0.5)',
  annotationId?: string
): void {
  const startSpan = document.getElementById(startSpanId);
  const endSpan = document.getElementById(endSpanId);

  if (!startSpan || !endSpan) {
    return;
  }

  // 如果是同一个 span
  if (startSpanId === endSpanId) {
    highlightWithinSpan(startSpan, startOffset, endOffset, color, annotationId);
    return;
  }

  // 跨多个 span：高亮起始 span 的后半部分
  highlightWithinSpan(startSpan, startOffset, startSpan.textContent?.length || 0, color, annotationId);

  // 高亮中间的所有 span
  const allSpans = collectSpansBetween(startSpan, endSpan);
  allSpans.forEach(span => {
    if (span !== startSpan && span !== endSpan) {
      highlightWithinSpan(span, 0, span.textContent?.length || 0, color, annotationId);
    }
  });

  // 高亮结束 span 的前半部分
  highlightWithinSpan(endSpan, 0, endOffset, color, annotationId);
}

/**
 * 在单个 span 内高亮指定范围的文本
 */
function highlightWithinSpan(
  span: HTMLElement,
  startOffset: number,
  endOffset: number,
  color: string,
  annotationId?: string
): void {
  const text = span.textContent || '';

  if (startOffset < 0 || endOffset > text.length || startOffset >= endOffset) {
    return;
  }

  // 如果是整个 span，直接设置背景色
  if (startOffset === 0 && endOffset === text.length) {
    if (color === 'ghost') {
      span.classList.add('reader-ghost-highlight');
    } else {
      span.style.backgroundColor = color;
    }
    span.setAttribute('data-highlighted', 'true');
    if (annotationId) {
      span.setAttribute('data-annotation-id', annotationId);
      span.style.cursor = 'pointer';
    }
    return;
  }

  // 部分高亮：需要分割文本节点
  const before = text.substring(0, startOffset);
  const highlighted = text.substring(startOffset, endOffset);
  const after = text.substring(endOffset);

  const highlightSpan = document.createElement('span');
  if (color === 'ghost') {
    highlightSpan.classList.add('reader-ghost-highlight');
  } else {
    highlightSpan.style.backgroundColor = color;
  }
  highlightSpan.setAttribute('data-highlighted', 'true');
  highlightSpan.textContent = highlighted;
  if (annotationId) {
    highlightSpan.setAttribute('data-annotation-id', annotationId);
    highlightSpan.style.cursor = 'pointer';
  }

  span.style.backgroundColor = '';
  span.removeAttribute('data-highlighted');
  span.removeAttribute('data-annotation-id');
  span.style.cursor = '';
  span.innerHTML = '';
  if (before) span.appendChild(document.createTextNode(before));
  span.appendChild(highlightSpan);
  if (after) span.appendChild(document.createTextNode(after));
}

/**
 * 收集两个 span 之间的所有 span 元素（包括首尾）
 */
function collectSpansBetween(startSpan: HTMLElement, endSpan: HTMLElement): HTMLElement[] {
  const container = findCommonAncestor(startSpan, endSpan);
  if (!container) {
    return [startSpan, endSpan];
  }

  const allSpans = Array.from(container.querySelectorAll('span[id]'));
  const startIndex = allSpans.indexOf(startSpan);
  const endIndex = allSpans.indexOf(endSpan);

  if (startIndex === -1 || endIndex === -1) {
    return [startSpan, endSpan];
  }

  return allSpans.slice(startIndex, endIndex + 1) as HTMLElement[];
}

/**
 * 查找两个节点的共同祖先
 */
function findCommonAncestor(node1: HTMLElement, node2: HTMLElement): HTMLElement | null {
  const parents1 = getParents(node1);
  const parents2 = getParents(node2);

  for (let i = 0; i < Math.min(parents1.length, parents2.length); i++) {
    if (parents1[i] !== parents2[i]) {
      return i > 0 ? parents1[i - 1] as HTMLElement : null;
    }
  }

  return parents1[parents1.length - 1] as HTMLElement;
}

function getParents(node: HTMLElement): Node[] {
  const parents: Node[] = [];
  let current: Node | null = node;
  while (current) {
    parents.unshift(current);
    current = current.parentNode;
  }
  return parents;
}

/**
 * 移除高亮样式
 */
export function removeHighlight(startSpanId: string, endSpanId: string): void {
  const startSpan = document.getElementById(startSpanId);
  const endSpan = document.getElementById(endSpanId);

  if (!startSpan || !endSpan) {
    return;
  }

  const allSpans = collectSpansBetween(startSpan, endSpan);

  allSpans.forEach(span => {
    span.style.backgroundColor = '';
    span.classList.remove('reader-ghost-highlight');
    span.removeAttribute('data-highlighted');
    span.removeAttribute('data-annotation-id');
    span.style.cursor = '';

    const innerHighlights = span.querySelectorAll('span[data-highlighted]');
    innerHighlights.forEach(highlight => {
      const textNode = document.createTextNode(highlight.textContent || '');
      highlight.parentNode?.replaceChild(textNode, highlight);
    });

    span.normalize();
  });
}

/**
 * 根据 annotation ID 移除高亮样式
 */
export function removeHighlightById(annotationId: string): void {
  const elements = document.querySelectorAll(`[data-annotation-id="${annotationId}"]`);

  elements.forEach(element => {
    const htmlElement = element as HTMLElement;

    if (htmlElement.tagName === 'SPAN') {
      if (htmlElement.hasAttribute('data-highlighted') && htmlElement.parentElement?.id) {
        const parent = htmlElement.parentNode;
        const textNode = document.createTextNode(htmlElement.textContent || '');
        parent?.replaceChild(textNode, htmlElement);
        (parent as HTMLElement)?.normalize();
      } else {
        htmlElement.style.backgroundColor = '';
        htmlElement.classList.remove('reader-ghost-highlight');
        htmlElement.removeAttribute('data-highlighted');
        htmlElement.removeAttribute('data-annotation-id');
        htmlElement.style.cursor = '';

        const innerHighlights = htmlElement.querySelectorAll('span[data-highlighted]');
        innerHighlights.forEach(inner => {
          const textNode = document.createTextNode(inner.textContent || '');
          inner.parentNode?.replaceChild(textNode, inner);
        });

        htmlElement.normalize();
      }
    }
  });
}
