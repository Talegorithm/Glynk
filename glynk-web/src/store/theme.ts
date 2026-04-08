import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { isNightTime } from '../hooks/useTimeGradient';

export type Theme = 'light' | 'dark' | 'sky';

interface ThemeState {
  theme: Theme;
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
}

const THEME_ORDER: Theme[] = ['sky', 'light', 'dark'];

export const useThemeStore = create<ThemeState>()(
  persist(
    (set) => ({
      theme: 'sky',
      setTheme: (theme) => {
        set({ theme });
        applyTheme(theme);
      },
      toggleTheme: () => {
        set((state) => {
          const currentIndex = THEME_ORDER.indexOf(state.theme);
          const newTheme = THEME_ORDER[(currentIndex + 1) % THEME_ORDER.length];
          applyTheme(newTheme);
          return { theme: newTheme };
        });
      },
    }),
    {
      name: 'glynk-theme',
      onRehydrateStorage: () => (state) => {
        if (state) {
          applyTheme(state.theme);
        }
      },
    }
  )
);

// Helper to apply the theme to the document
export function applyTheme(theme: Theme) {
  if (typeof window === 'undefined') return;

  const root = window.document.documentElement;
  
  root.classList.remove('light', 'dark', 'sky');
  root.classList.add('sky'); // Universal glassmorphism foundation
  root.style.backgroundColor = 'transparent';

  if (theme === 'dark' || (theme === 'sky' && isNightTime())) {
    root.classList.add('dark');
  } else {
    root.classList.add('light');
  }
}

// Check sky mode time periodically
if (typeof window !== 'undefined') {
  setInterval(() => {
    const currentTheme = useThemeStore.getState().theme;
    if (currentTheme === 'sky') {
      applyTheme('sky'); // Will process isNightTime logic
    }
  }, 60000);
}


