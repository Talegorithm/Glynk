import client from './client';
import type { Annotation, QueryResponse } from '../types/annotation';

export async function createAnnotation(data: Omit<Annotation, 'annotation_id' | 'created_at' | 'updated_at'>): Promise<Annotation> {
  const res = await client.post<Annotation>('/annotations', data);
  return res.data;
}

export async function createBatchAnnotations(
  annotations: Omit<Annotation, 'annotation_id' | 'created_at' | 'updated_at'>[],
): Promise<Annotation[]> {
  const res = await client.post<Annotation[]>('/annotations/batch', { annotations });
  return res.data;
}

export async function getMyAnnotations(params?: {
  content_id?: string;
  type?: string;
  limit?: number;
  offset?: number;
}): Promise<QueryResponse> {
  const res = await client.get<QueryResponse>('/annotations', { params });
  return res.data;
}

export async function searchMyAnnotations(query: string): Promise<QueryResponse> {
  const res = await client.get<QueryResponse>('/annotations/search', { params: { q: query } });
  return res.data;
}
