import client from './client';
import type { ReadContentResponse, OutlineItem, Content, ContentDetail } from '../types/content';

// --- Unit reading (replaces /content/* endpoints) ---

export async function readContent(
  contentId: string,
  params?: { from?: string; size?: number; view?: string; lang?: string },
): Promise<ReadContentResponse> {
  const res = await client.get<ReadContentResponse>(`/units/${contentId}/read`, { params });
  return res.data;
}

export async function readFile(
  contentId: string,
  fromSpan?: string,
  lang?: string,
): Promise<ReadContentResponse> {
  const params: Record<string, string> = {};
  if (fromSpan) params.from = fromSpan;
  if (lang) params.lang = lang;
  const res = await client.get<ReadContentResponse>(`/units/${contentId}/read`, { params });
  return res.data;
}

// --- Unit metadata ---

export async function getContentDetail(contentId: string): Promise<ContentDetail> {
  const res = await client.get<ContentDetail>(`/units/${contentId}`);
  return res.data;
}

export async function getOutline(contentId: string): Promise<OutlineItem[]> {
  const res = await client.get<{ outline: OutlineItem[] }>(`/units/${contentId}/outline`);
  return res.data.outline;
}

export async function listContents(limit = 20, offset = 0): Promise<{ contents: Content[]; total: number }> {
  const res = await client.get<{ contents: Content[]; total: number }>('/units', { params: { limit, offset, origin: 'ingested' } });
  return res.data;
}

export async function createUnit(data: { text: string; metadata?: object }): Promise<{ id: string }> {
  const res = await client.post<{ id: string }>('/units', data);
  return res.data;
}

export async function getAuthoredUnits(limit = 20, offset = 0): Promise<{ contents: Content[]; total: number }> {
  const res = await client.get<{ contents: Content[]; total: number }>('/units', { 
    params: { origin: 'authored', author_id: 'me', limit, offset } 
  });
  return res.data;
}

// --- Reading progress ---

export async function getReadingProgress(contentId: string): Promise<{ span_id: string; updated_at: string } | null> {
  try {
    const res = await client.get<{ span_id: string; updated_at: string }>(`/units/${contentId}/progress`);
    return res.data;
  } catch {
    return null;
  }
}

export async function saveReadingProgress(contentId: string, spanId: string): Promise<void> {
  await client.put(`/units/${contentId}/progress`, { span_id: spanId });
}

// --- Translation ---

export async function translateFile(contentId: string, fileIdx: number): Promise<{ lang: string; status: string }> {
  const res = await client.post<{ lang: string; status: string }>(`/units/${contentId}/translate`, { file_idx: fileIdx });
  return res.data;
}

// --- Reading sessions ---

export async function startReadingSession(
  contentId: string,
  source: string = 'manual',
): Promise<string> {
  const res = await client.post<{ session_id: string }>('/reading-sessions', {
    content_id: contentId,
    source,
  });
  return res.data.session_id;
}

export async function endReadingSession(
  sessionId: string,
  durationSeconds?: number,
): Promise<void> {
  await client.put(`/reading-sessions/${sessionId}/end`, {
    duration_seconds: durationSeconds,
  });
}
