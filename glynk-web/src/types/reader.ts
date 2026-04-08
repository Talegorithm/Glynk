import type { TOCItem, OutlineItem } from './content';

export type { TOCItem, OutlineItem };

export interface FlatTOCItem extends TOCItem {
  index: number;
  depth: number;
}

export interface FileContent {
  fileIdx: number;
  html: string;
  fromSpan: string;
  toSpan: string;
  charCount: number;
  hasMore: boolean;
  nextFrom: string | null;
  translationStatus: string;
}

export interface ContentMeta {
  contentId: string;
  title: string;
  author: string;
  fileCount: number;
  totalChars: number;
}

export interface ReaderState {
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

  init: (contentId: string) => Promise<void>;
  loadFile: (fileIdx: number) => Promise<void>;
  loadNextFile: () => Promise<void>;
  loadPreviousFile: () => Promise<void>;
  jumpToLocation: (spanId: string) => Promise<void>;
  reloadCurrentFile: (location?: string) => Promise<void>;
  getCurrentLocation: () => string | null;
  toggleToc: () => void;
  reset: () => void;
}
