import client from './client';

export interface SemanticSearchParams {
  text: string;
  types?: string[];
  content_ids?: string[];
  top_k?: number;
}

export interface SemanticSearchResult {
  id: string;
  text: string;
  tags: string[];
  score: number;
  crowd_count: number;
  browse_url: string;

  // "target" = 卡片应以"原文那段"为主角（highlight 类）
  // "unit"   = 卡片应以 Unit 本身为主角（note / summary / reply / hook / 独立）
  default_view: 'target' | 'unit';

  // 这个 Unit 指向的"原文位置"。null = standalone（没有 anchor 的 authored Unit）。
  // 和下面的 anchor（= anchor_metadata 遗留字段）不是一回事。
  target: {
    role: string;
    unit: string;
    span: string | null;
  } | null;

  // 便于展示"在 XX 上"——从 target.unit 反查出来的内容元信息；
  // standalone 时为空字符串。
  content_id: string;
  content_title: string;
  content_author: string;

  // 等于 target.role（standalone 时为空）
  type: string;

  // anchor metadata（color / spans / offsets 等），由创建者决定内容。
  // 注意：这是 anchor 创建时传的 metadata，不是"指向哪里"。"指向哪里"见 target。
  anchor: { type?: string; spans?: string[]; color?: string; [k: string]: unknown };
}

export async function semanticSearch(params: SemanticSearchParams): Promise<{
  query_id: string;
  results: SemanticSearchResult[];
}> {
  const res = await client.post<{ query_id: string; results: SemanticSearchResult[] }>('/units/search', params);
  return res.data;
}
