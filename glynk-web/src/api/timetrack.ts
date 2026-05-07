import client from './client';

export interface Tag {
  id: string;
  name: string;
  color: string;
  sort_order: number;
  created_at: string;
}

export interface Session {
  id: string;
  tag_id: string;
  start_time: string;
  end_time: string | null;
  note: string | null;
  created_at: string;
}

export interface StatItem extends Session {
  tag_name: string;
  tag_color: string;
}

export const timetrackApi = {
  getTags: () => client.get<Tag[]>('/timetrack/tags').then(res => res.data),
  createTag: (name: string, color: string) => client.post<Tag>('/timetrack/tags', { name, color }).then(res => res.data),
  updateTag: (id: string, data: Partial<Tag>) => client.put<Tag>(`/timetrack/tags/${id}`, data).then(res => res.data),
  deleteTag: (id: string) => client.delete(`/timetrack/tags/${id}`).then(res => res.data),
  reorderTags: (items: { id: string, sort_order: number }[]) => client.put('/timetrack/tags/reorder', { items }).then(res => res.data),
  
  getActiveSessions: () => client.get<Session[]>('/timetrack/sessions/active').then(res => res.data),
  startSession: (tagId: string, singleMode: boolean) => client.post<Session>(`/timetrack/sessions/${tagId}/start?single_mode=${singleMode}`).then(res => res.data),
  stopSession: (sessionId: string, end_time?: string) => client.post<Session>(`/timetrack/sessions/${sessionId}/stop`, { end_time }).then(res => res.data),
  updateSessionNote: (sessionId: string, note: string) => client.put<Session>(`/timetrack/sessions/${sessionId}/note`, { note }).then(res => res.data),
  deleteSession: (sessionId: string) => client.delete(`/timetrack/sessions/${sessionId}`).then(res => res.data),
  addPastSession: (tagId: string, durationMins: number, note: string) => client.post<Session>('/timetrack/sessions/past', { tag_id: tagId, duration_mins: durationMins, note }).then(res => res.data),
  
  getStats: (startDt?: string, endDt?: string) => {
    const params = new URLSearchParams();
    if (startDt) params.append('start_dt', startDt);
    if (endDt) params.append('end_dt', endDt);
    const qs = params.toString() ? `?${params.toString()}` : '';
    return client.get<StatItem[]>(`/timetrack/stats${qs}`).then(res => res.data);
  },
  getTodayStats: (since: string) => client.get<{tag_id: string, duration_ms: number}[]>(`/timetrack/stats/today?since=${encodeURIComponent(since)}`).then(res => res.data),
};
