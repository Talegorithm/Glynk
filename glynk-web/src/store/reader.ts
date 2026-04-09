/**
 * 阅读器状态管理（连续滚动模式）
 * 从 Brainow 迁移，适配 Glynk API
 */

import { create } from 'zustand';
import type { FileContent, ContentMeta, TOCItem, FlatTOCItem, OutlineItem } from '../types/reader';
import { readFile, getContentDetail } from '../api/content';
import { flattenTOC } from '../utils/reader/toc';

interface ReaderState {
  contentId: string | null;
  contentMeta: ContentMeta | null;
  loadedFiles: Map<number, FileContent>;
  toc: TOCItem[];
  flatToc: FlatTOCItem[];
  outline: OutlineItem[];
  currentFileIdx: number;
  isLoading: boolean;
  isJumping: boolean;
  tocVisible: boolean;
  lang: string | null;

  init: (contentId: string) => Promise<void>;
  loadFile: (fileIdx: number, fromSpan?: string) => Promise<void>;
  loadNextFile: () => Promise<void>;
  loadPreviousFile: () => Promise<void>;
  jumpToLocation: (spanId: string) => Promise<void>;
  reloadCurrentFile: (location?: string) => Promise<void>;
  getCurrentLocation: () => string;
  setLang: (lang: string | null) => void;
  toggleToc: () => void;
  reset: () => void;
}

/**
 * 从 span_id 解析 file_idx
 * 格式: {content_id}-{file_idx}-p{n}-s{m}
 * 考虑到 content_id 本身可能包含连字符 (如 uuid)，使用正则从末尾匹配
 */
function parseFileIdx(spanId: string): number {
  const match = spanId.match(/-(\d+)-p\d+-s\d+$/);
  if (match) {
    console.log(`[DEBUG parseFileIdx] spanId: ${spanId}, match: ${match[1]}, parsed: ${parseInt(match[1], 10)}`);
    return parseInt(match[1], 10);
  }
  // Fallback
  const parts = spanId.split('-');
  const fallback = parts.length >= 2 ? parseInt(parts[parts.length - 3] || parts[1], 10) : 0;
  console.log(`[DEBUG parseFileIdx] spanId: ${spanId}, match: fallback, parsed: ${fallback}`);
  return fallback;
}

export const useReaderStore = create<ReaderState>((set, get) => ({
  contentId: null,
  contentMeta: null,
  loadedFiles: new Map<number, FileContent>(),
  toc: [],
  flatToc: [],
  outline: [],
  currentFileIdx: 0,
  isLoading: false,
  isJumping: false,
  tocVisible: false,
  lang: null,

  /**
   * 初始化阅读器：加载元数据 + 首文件 + TOC + outline
   */
  init: async (contentId) => {
    set({ isLoading: true, contentId });

    try {
      // 并行加载元数据和首文件
      const [detail, firstFile] = await Promise.all([
        getContentDetail(contentId),
        readFile(contentId, undefined, get().lang || undefined),
      ]);

      const meta: ContentMeta = {
        contentId,
        title: detail.title || '',
        author: detail.author || '',
        fileCount: detail.file_count || 0,
        totalChars: detail.total_chars || 0,
      };

      const toc = detail.toc || [];
      const flatToc = flattenTOC(toc);
      const outline = detail.outline || [];

      // 解析首文件的 fileIdx
      const fileIdx = firstFile.from ? parseFileIdx(firstFile.from) : 0;
      const fileContent: FileContent = {
        fileIdx,
        html: firstFile.content,
        fromSpan: firstFile.from,
        toSpan: firstFile.to,
        charCount: firstFile.char_count,
        hasMore: firstFile.has_more,
        nextFrom: firstFile.next_from,
        translationStatus: firstFile.translation_status,
      };

      const loadedFiles = new Map<number, FileContent>();
      loadedFiles.set(fileIdx, fileContent);

      set({
        contentMeta: meta,
        loadedFiles,
        toc,
        flatToc,
        outline,
        currentFileIdx: fileIdx,
        isLoading: false,
      });

      // 首文件太短时自动加载后续文件（避免用户只看到版权页）
      if (fileContent.charCount < 2000 && fileContent.hasMore) {
        await get().loadNextFile();
      }
    } catch (error) {
      console.error('初始化阅读器失败:', error);
      set({ isLoading: false });
    }
  },

  /**
   * 加载指定文件
   */
  loadFile: async (fileIdx, fromSpan?) => {
    const state = get();
    const alreadyHasFile = Array.from(state.loadedFiles.values()).some((f) => f.fileIdx === fileIdx);
    if (alreadyHasFile) return;
    if (!state.contentId) return;

    set({ isLoading: true });

    try {
      // 构造 from span: 如果没有提供，用 content_id-fileIdx-p0-s0 格式
      const from = fromSpan || `${state.contentId}-${fileIdx}-p0-s0`;
      const response = await readFile(state.contentId, from, state.lang || undefined);

      const actualFileIdx = response.from ? parseFileIdx(response.from) : fileIdx;
      const fileContent: FileContent = {
        fileIdx: actualFileIdx,
        html: response.content,
        fromSpan: response.from,
        toSpan: response.to,
        charCount: response.char_count,
        hasMore: response.has_more,
        nextFrom: response.next_from,
        translationStatus: response.translation_status,
      };

      const newLoadedFiles = new Map(state.loadedFiles);
      newLoadedFiles.set(actualFileIdx, fileContent);

      set({
        loadedFiles: newLoadedFiles,
        currentFileIdx: actualFileIdx,
        isLoading: false,
      });
    } catch (error) {
      console.error('加载文件失败:', error);
      set({ isLoading: false });
    }
  },

  /**
   * 加载下一文件（滚动到底部时触发）
   * 如果文件很短（< 2000 chars），自动继续加载后续文件直到有足够内容
   */
  loadNextFile: async () => {
    const state = get();
    if (!state.contentId || state.isLoading) return;

    const contentId = state.contentId;
    set({ isLoading: true });

    try {
      let totalChars = 0;
      const minChars = 3000; // 累积至少这么多内容才停
      const maxFiles = 15;

      for (let i = 0; i < maxFiles; i++) {
        const currentState = get();
        
        // Find last chronological chunk based on fileIdx
        const chunks = Array.from(currentState.loadedFiles.values()).sort((a, b) => a.fileIdx - b.fileIdx);
        if (chunks.length === 0) break;
        const lastFile = chunks[chunks.length - 1];

        if (!lastFile?.hasMore || !lastFile?.nextFrom) break;

        const response = await readFile(contentId, lastFile.nextFrom, get().lang || undefined);
        const actualFileIdx = response.from ? parseFileIdx(response.from) : lastFile.fileIdx + 1;
        
        // Each chunk becomes its own FileContent entry in the map.

        const fileContent: FileContent = {
          fileIdx: actualFileIdx,
          html: response.content,
          fromSpan: response.from,
          toSpan: response.to,
          charCount: response.char_count,
          hasMore: response.has_more,
          nextFrom: response.next_from,
          translationStatus: response.translation_status,
        };

        const newLoadedFiles = new Map(currentState.loadedFiles);
        newLoadedFiles.set(actualFileIdx, fileContent);
        set({ loadedFiles: newLoadedFiles, currentFileIdx: actualFileIdx });

        totalChars += response.char_count;
        if (totalChars >= minChars) break;
      }
    } catch (error) {
      console.error('加载下一文件失败:', error);
    } finally {
      set({ isLoading: false });
    }
  },

  /**
   * 加载前一文件（滚动到顶部时触发）
   */
  loadPreviousFile: async () => {
    const state = get();
    if (!state.contentId) return;

    const chunks = Array.from(state.loadedFiles.values());
    if (chunks.length === 0) return;
    const minLoadedIdx = Math.min(...chunks.map((c) => c.fileIdx));

    if (minLoadedIdx <= 0) return;

    await get().loadFile(minLoadedIdx - 1);
  },

  /**
   * 跳转到指定 span_id
   */
  jumpToLocation: async (spanId) => {
    if (!spanId) return;

    const state = get();
    if (!state.contentId) return;

    set({ isLoading: true, loadedFiles: new Map() });

    try {
      const fileIdx = parseFileIdx(spanId);
      const from = `${state.contentId}-${fileIdx}-p0-s0`;
      const response = await readFile(state.contentId, from, state.lang || undefined);

      const fileContent: FileContent = {
        fileIdx,
        html: response.content,
        fromSpan: response.from,
        toSpan: response.to,
        charCount: response.char_count,
        hasMore: response.has_more,
        nextFrom: response.next_from,
        translationStatus: response.translation_status,
      };

      const newLoadedFiles = new Map<number, FileContent>();
      newLoadedFiles.set(fileIdx, fileContent);

      set({
        currentFileIdx: fileIdx,
        loadedFiles: newLoadedFiles,
        isLoading: false,
      });

      // 等待 DOM 渲染，然后定位
      set({ isJumping: true });

      // 轮询等待目标元素渲染完成
      const startTime = Date.now();
      const maxWaitTime = 5000;

      const checkAndScroll = () => {
        const elapsed = Date.now() - startTime;

        const targetSpan = document.getElementById(spanId);
        if (!targetSpan) {
          if (elapsed < maxWaitTime) setTimeout(checkAndScroll, 100);
          else set({ isJumping: false });
          return;
        }

        // scrollIntoView 比手动计算更可靠（不受图片加载影响）
        targetSpan.scrollIntoView({ block: 'center', behavior: 'smooth' });

        // 脉冲高亮效果
        const originalOutline = targetSpan.style.outline || '';
        const originalOutlineOffset = targetSpan.style.outlineOffset || '';
        let pulseCount = 0;

        const pulseInterval = setInterval(() => {
          if (pulseCount % 2 === 0) {
            targetSpan.style.outline = '2px solid rgba(59, 130, 246, 0.6)';
            targetSpan.style.outlineOffset = '2px';
          } else {
            targetSpan.style.outline = originalOutline;
            targetSpan.style.outlineOffset = originalOutlineOffset;
          }
          pulseCount++;

          if (pulseCount >= 6) {
            clearInterval(pulseInterval);
            targetSpan.style.outline = originalOutline;
            targetSpan.style.outlineOffset = originalOutlineOffset;
            set({ isJumping: false });
          }
        }, 500);
      };

      setTimeout(checkAndScroll, 200);
    } catch (error) {
      console.error('跳转失败:', error);
      set({ isLoading: false, isJumping: false });
    }
  },

  /**
   * 重新加载当前文件（翻译模式切换后）
   */
  reloadCurrentFile: async (location?: string) => {
    const state = get();
    if (!state.contentId) return;

    try {
      set({ isLoading: true });

      const newLoadedFiles = new Map(state.loadedFiles);
      
      // Keep only chunks that match state.currentFileIdx
      const chunksToDelete = [];
      for (const [key, value] of newLoadedFiles.entries()) {
        if (value.fileIdx === state.currentFileIdx) {
          chunksToDelete.push(key);
        }
      }
      for (const key of chunksToDelete) {
        newLoadedFiles.delete(key);
      }

      set({ loadedFiles: newLoadedFiles });

      const jumpId = location || state.getCurrentLocation();
      await get().jumpToLocation(jumpId);
      
    } catch (error) {
      console.error('重新加载文件失败:', error);
      set({ isLoading: false });
    }
  },

  /**
   * 获取当前第一个可见的 span id
   */
  getCurrentLocation: () => {
    const scrollContainer = document.querySelector('[data-reader-scroll]');
    if (!scrollContainer) return '';

    const spans = scrollContainer.querySelectorAll('span[id]');
    const containerRect = scrollContainer.getBoundingClientRect();

    for (const span of Array.from(spans)) {
      const rect = span.getBoundingClientRect();
      if (rect.top >= containerRect.top && rect.top < containerRect.top + containerRect.height / 2) {
        return span.id;
      }
    }

    return spans[0]?.id || '';
  },

  setLang: (lang) => {
    set({ lang });
  },

  toggleToc: () => {
    set((state) => ({ tocVisible: !state.tocVisible }));
  },

  reset: () => {
    set({
      contentId: null,
      contentMeta: null,
      loadedFiles: new Map(),
      toc: [],
      flatToc: [],
      outline: [],
      currentFileIdx: 0,
      isLoading: false,
      isJumping: false,
      tocVisible: false,
      lang: null,
    });
  },
}));
