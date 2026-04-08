export interface Content {
  content_id: string;
  title: string;
  author?: string;
  source_type?: string;
  source_url?: string;
  file_count?: number;
  total_chars?: number;
  abstract?: string;
  created_at?: string;
  updated_at?: string;
}

export interface ContentDetail extends Content {
  toc: TOCItem[];
  outline: OutlineItem[];
}

export interface TOCItem {
  title: string;
  href: string;     // span_id (摄入时已从 EPUB href 转换)
  level?: number;
  children?: TOCItem[];
}

export interface ReadContentResponse {
  content: string;           // HTML body
  from: string;              // 起始 span_id
  to: string;                // 结束 span_id
  char_count: number;
  has_more: boolean;
  next_from: string | null;
  translation_status: string;
  annotations: import('./annotation').Annotation[];
}

export interface OutlineItem {
  title: string;
  description?: string;
  location?: string;         // span_id
  children?: OutlineItem[];
}
