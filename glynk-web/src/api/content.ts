import client from './client';
import type { ReadContentResponse, OutlineItem, Content, ContentDetail } from '../types/content';

// --- 内容阅读 ---

export async function readContent(
  contentId: string,
  params?: { from?: string; size?: number; view?: string; lang?: string },
): Promise<ReadContentResponse> {
  const res = await client.get<ReadContentResponse>(`/content/${contentId}/file`, { params });
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
  const res = await client.get<ReadContentResponse>(`/content/${contentId}/file`, { params });
  return res.data;
}

// --- 内容元数据 ---

export async function getContentDetail(contentId: string): Promise<ContentDetail> {
  const res = await client.get<ContentDetail>(`/content/${contentId}`);
  return res.data;
}

export async function getOutline(contentId: string): Promise<OutlineItem[]> {
  const res = await client.get<{ outline: OutlineItem[] }>(`/content/${contentId}/outline`);
  return res.data.outline;
}

export async function listContents(limit = 20, offset = 0): Promise<{ contents: Content[]; total: number }> {
  const res = await client.get<{ contents: Content[]; total: number }>('/contents', { params: { limit, offset } });
  return res.data;
}

// --- 阅读进度 ---

export async function getReadingProgress(contentId: string): Promise<{ span_id: string; updated_at: string } | null> {
  try {
    const res = await client.get<{ span_id: string; updated_at: string }>(`/content/${contentId}/progress`);
    return res.data;
  } catch {
    return null;
  }
}

export async function saveReadingProgress(contentId: string, spanId: string): Promise<void> {
  await client.put(`/content/${contentId}/progress`, { span_id: spanId });
}

// --- 翻译 ---

export async function translateFile(contentId: string, fileIdx: number): Promise<{ lang: string; status: string }> {
  const res = await client.post<{ lang: string; status: string }>(`/content/${contentId}/translate`, { file_idx: fileIdx });
  return res.data;
}

// --- 阅读会话 ---

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
  // 使用 sendBeacon 友好的方式
  await client.put(`/reading-sessions/${sessionId}/end`, {
    duration_seconds: durationSeconds,
  });
}
