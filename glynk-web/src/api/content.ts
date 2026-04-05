import client from './client';
import type { ReadResponse, OutlineItem, Content } from '../types/content';

export async function readContent(
  contentId: string,
  params?: { from?: number; size?: number; view?: string; lang?: string },
): Promise<ReadResponse> {
  const res = await client.get<ReadResponse>(`/contents/${contentId}/read`, { params });
  return res.data;
}

export async function getOutline(contentId: string): Promise<OutlineItem[]> {
  const res = await client.get<OutlineItem[]>(`/contents/${contentId}/outline`);
  return res.data;
}

export async function listContents(limit: number, offset: number): Promise<Content[]> {
  const res = await client.get<Content[]>('/contents', { params: { limit, offset } });
  return res.data;
}
