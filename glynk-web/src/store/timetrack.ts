import { create } from 'zustand';
import type { Tag, Session } from '../api/timetrack';
import { timetrackApi } from '../api/timetrack';

interface TimetrackState {
  tags: Tag[];
  activeSessions: Session[];
  todayStats: {tag_id: string, duration_ms: number}[];
  singleMode: boolean;
  loading: boolean;
  
  setSingleMode: (mode: boolean) => void;
  fetchTags: () => Promise<void>;
  createTag: (name: string, color: string) => Promise<void>;
  updateTag: (id: string, data: Partial<Tag>) => Promise<void>;
  deleteTag: (id: string) => Promise<void>;
  reorderTags: (newTags: Tag[]) => Promise<void>;
  
  fetchActiveSessions: () => Promise<void>;
  fetchTodayStats: () => Promise<void>;
  addPastSession: (tagId: string, durationMins: number, note: string) => Promise<void>;
  startSession: (tagId: string) => Promise<Session>;
  stopSession: (sessionId: string) => Promise<void>;
  updateSessionNote: (sessionId: string, note: string) => Promise<void>;
}

export const useTimetrackStore = create<TimetrackState>((set, get) => ({
  tags: [],
  activeSessions: [],
  todayStats: [],
  singleMode: true,
  loading: false,

  setSingleMode: (mode) => set({ singleMode: mode }),

  fetchTags: async () => {
    set({ loading: true });
    try {
      const tags = await timetrackApi.getTags();
      set({ tags });
    } finally {
      set({ loading: false });
    }
  },

  createTag: async (name, color) => {
    const newTag = await timetrackApi.createTag(name, color);
    set(state => ({ tags: [...state.tags, newTag] }));
  },

  updateTag: async (id, data) => {
    const updated = await timetrackApi.updateTag(id, data);
    set(state => ({
      tags: state.tags.map(t => t.id === id ? updated : t)
    }));
  },

  deleteTag: async (id) => {
    await timetrackApi.deleteTag(id);
    set(state => ({
      tags: state.tags.filter(t => t.id !== id),
      activeSessions: state.activeSessions.filter(s => s.tag_id !== id)
    }));
  },

  reorderTags: async (newTags) => {
    set({ tags: newTags });
    const items = newTags.map((t, index) => ({ id: t.id, sort_order: index }));
    await timetrackApi.reorderTags(items);
  },

  fetchActiveSessions: async () => {
    const sessions = await timetrackApi.getActiveSessions();
    set({ activeSessions: sessions });
  },

  fetchTodayStats: async () => {
    const stats = await timetrackApi.getTodayStats();
    set({ todayStats: stats });
  },

  addPastSession: async (tagId, durationMins, note) => {
    await timetrackApi.addPastSession(tagId, durationMins, note);
    get().fetchTodayStats();
  },

  startSession: async (tagId) => {
    const { singleMode } = get();
    // Optimistic UI could be added here, but relying on server ensures accurate timestamp
    const session = await timetrackApi.startSession(tagId, singleMode);
    
    if (singleMode) {
      // If single mode, all other sessions were stopped on server.
      set({ activeSessions: [session] });
    } else {
      set(state => ({ activeSessions: [...state.activeSessions, session] }));
    }
    return session;
  },

  stopSession: async (sessionId) => {
    // Determine end time to be as accurate to click as possible
    const endTime = new Date().toISOString();
    
    // Optimistic update
    set(state => ({
      activeSessions: state.activeSessions.filter(s => s.id !== sessionId)
    }));

    try {
      await timetrackApi.stopSession(sessionId, endTime);
    } catch (e) {
      // Revert or refresh on failure
      get().fetchActiveSessions();
    }
  },

  updateSessionNote: async (sessionId, note) => {
    const updated = await timetrackApi.updateSessionNote(sessionId, note);
    set(state => ({
      activeSessions: state.activeSessions.map(s => s.id === sessionId ? updated : s)
    }));
  }
}));
