import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface ReaderSettingsState {
  fontSize: number;
  fontFamily: 'serif' | 'sans-serif';
  setFontSize: (size: number) => void;
  setFontFamily: (family: 'serif' | 'sans-serif') => void;
}

export const useReaderSettingsStore = create<ReaderSettingsState>()(
  persist(
    (set) => ({
      fontSize: 18,
      fontFamily: 'serif',
      setFontSize: (fontSize) => set({ fontSize: Math.max(12, Math.min(36, fontSize)) }),
      setFontFamily: (fontFamily) => set({ fontFamily }),
    }),
    {
      name: 'glynk-reader-settings',
    }
  )
);
