export interface TextSelectionAnchor {
  type: 'text_selection';
  spans: string[];
  startSpanId: string;
  endSpanId: string;
  startOffset: number;
  endOffset: number;
  color: string;            // 'yellow' | 'green' | 'blue' | 'pink'
  note?: string;            // 用户笔记（可选）
  [key: string]: unknown;   // index signature for Record<string, unknown> compat
}

export interface Annotation {
  id: string;
  content_id: string;
  anchor: TextSelectionAnchor | Record<string, unknown>;
  type: string;  // 'highlight' | 'hook' | 'note' | 'reaction'
  text: string;
  tags: string[];
  contextuality: string;
  source: string;
  visibility: string;
  created_at?: string;
}
