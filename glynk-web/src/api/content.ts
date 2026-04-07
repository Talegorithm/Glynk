import client from './client';
import type { ReadResponse, OutlineItem, Content } from '../types/content';

export async function readContent(
  contentId: string,
  params?: { from?: string; size?: number; view?: string; lang?: string },
): Promise<ReadResponse> {
  const res = await client.get<ReadResponse>(`/content/${contentId}/read`, { params });
  return res.data;
}

export async function getOutline(contentId: string): Promise<{ outline: OutlineItem[] }> {
  const res = await client.get<{ outline: OutlineItem[] }>(`/content/${contentId}/outline`);
  return res.data;
}

export async function listContents(limit = 20, offset = 0): Promise<{ contents: Content[] }> {
  const res = await client.get<{ contents: Content[] }>('/contents', { params: { limit, offset } });
  return res.data;
}
