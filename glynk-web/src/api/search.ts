import client from './client';

export interface SemanticSearchParams {
  text: string;
  types?: string[];
  content_ids?: string[];
  top_k?: number;
}

export interface SemanticSearchResult {
  id: string;
  content_id: string;
  content_title: string;
  content_author: string;
  type: string;
  text: string;
  tags: string[];
  anchor: { type: string; spans: string[] };
  score: number;
  crowd_count: number;
  browse_url: string;
}

export async function semanticSearch(params: SemanticSearchParams): Promise<{
  query_id: string;
  results: SemanticSearchResult[];
}> {
  const res = await client.post<{ query_id: string; results: SemanticSearchResult[] }>('/units/search', params);
  return res.data;
}
