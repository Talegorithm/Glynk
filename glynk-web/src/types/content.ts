export interface Content {
  content_id: string;
  title: string;
  author?: string;
  language?: string;
  cover_url?: string;
  source_url?: string;
  created_at?: string;
  updated_at?: string;
}

export interface TOCItem {
  id: string;
  title: string;
  level: number;
  anchor?: string;
  children?: TOCItem[];
}

export interface ReadResponse {
  content_id: string;
  title: string;
  author?: string;
  language?: string;
  body: string;
  toc?: TOCItem[];
}

export interface OutlineItem {
  id: string;
  title: string;
  level: number;
  anchor?: string;
  children?: OutlineItem[];
}
