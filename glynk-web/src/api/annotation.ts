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
  in_reply_to?: string;
}): Promise<Annotation> {
  const anchor = data.anchor || {};
  const payload: any = {
    target_unit: data.content_id,
    target_span: anchor.startSpanId || (anchor.spans as string[])?.[0] || anchor.targetSpanId || null,
    role: data.type,
    metadata: anchor,
    text: data.text,
    tags: data.tags || [],
    visibility: data.visibility || 'public',
  };
  if (data.in_reply_to) payload.in_reply_to = data.in_reply_to;
  
  const res = await client.post<Annotation>('/anchors', payload);
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
  const anchors = annotations.map(a => ({
    target_unit: a.content_id,
    target_span: (a.anchor?.startSpanId as string) || ((a.anchor?.spans as string[]) || [])[0] || null,
    role: a.type,
    metadata: a.anchor || {},
    text: a.text,
    tags: a.tags || [],
  }));
  const res = await client.post<{ created: number; ids: string[] }>('/anchors/batch', { anchors });
  return res.data;
}

export async function getMyAnnotations(params?: {
  content_id?: string;
  type?: string;
  limit?: number;
  offset?: number;
}): Promise<{ annotations: Annotation[]; total: number }> {
  const res = await client.get<{ annotations: Annotation[]; total: number }>('/anchors', { params });
  return res.data;
}

export async function getContentAnnotations(contentId: string): Promise<Annotation[]> {
  const res = await client.get<{ annotations: Annotation[]; total: number }>('/anchors', {
    params: { content_id: contentId, limit: 200 },
  });
  return res.data.annotations;
}

export async function getSpanThread(contentId: string, spanId: string): Promise<Annotation[]> {
  const res = await client.get<{ annotations: Annotation[] }>('/anchors/thread', {
    params: { target_unit: contentId, target_span: spanId }
  });
  return res.data.annotations;
}

export async function deleteAnnotation(annotationId: string): Promise<void> {
  await client.delete(`/anchors/${annotationId}`);
}

export async function updateAnnotation(
  annotationId: string,
  data: { text?: string; anchor?: Record<string, unknown> },
): Promise<Annotation> {
  const payload: Record<string, unknown> = {};
  if (data.text !== undefined) payload.text = data.text;
  if (data.anchor !== undefined) payload.metadata = data.anchor;
  const res = await client.patch<Annotation>(`/anchors/${annotationId}`, payload);
  return res.data;
}

export async function searchMyAnnotations(query: string): Promise<{ results: Annotation[] }> {
  const res = await client.post<{ results: Annotation[] }>('/anchors/search', { query });
  return res.data;
}
