import client from './client';

export interface SemanticSearchParams {
  text: string;
  types?: string[];
  content_ids?: string[];
  top_k?: number;
}

export interface SemanticSearchResult {
  id: string;
  type: string;
  text: string;
  score: number;
  content_id?: string;
  content_title?: string;
}

export async function semanticSearch(params: SemanticSearchParams): Promise<SemanticSearchResult[]> {
  const res = await client.post<SemanticSearchResult[]>('/search/semantic', params);
  return res.data;
}
