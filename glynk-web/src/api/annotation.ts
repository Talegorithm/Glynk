import client from './client';
import type { Annotation } from '../types/annotation';

export async function createAnnotation(data: {
  content_id: string;
  anchor: Record<string, unknown>;
  type: string;
  text: string;
  tags?: string[];
  contextuality?: string;
  visibility?: string;
}): Promise<Annotation> {
  const res = await client.post<Annotation>('/annotate', data);
  return res.data;
}

export async function createBatchAnnotations(
  annotations: Array<{
    content_id: string;
    anchor: Record<string, unknown>;
    type: string;
    text: string;
    tags?: string[];
  }>,
): Promise<{ created: number; ids: string[] }> {
  const res = await client.post<{ created: number; ids: string[] }>('/annotate/batch', { annotations });
  return res.data;
}

export async function getMyAnnotations(params?: {
  content_id?: string;
  type?: string;
  limit?: number;
  offset?: number;
}): Promise<{ annotations: Annotation[]; total: number }> {
  const res = await client.get<{ annotations: Annotation[]; total: number }>('/annotations', { params });
  return res.data;
}

export async function getContentAnnotations(contentId: string): Promise<Annotation[]> {
  const res = await client.get<{ annotations: Annotation[]; total: number }>('/annotations', {
    params: { content_id: contentId, limit: 200 },
  });
  return res.data.annotations;
}

export async function deleteAnnotation(annotationId: string): Promise<void> {
  await client.delete(`/annotations/${annotationId}`);
}

export async function updateAnnotation(
  annotationId: string,
  data: { text?: string; anchor?: Record<string, unknown> },
): Promise<Annotation> {
  const res = await client.patch<Annotation>(`/annotations/${annotationId}`, data);
  return res.data;
}

export async function searchMyAnnotations(query: string): Promise<{ results: Annotation[] }> {
  const res = await client.post<{ results: Annotation[] }>('/annotations/search', { query });
  return res.data;
}
