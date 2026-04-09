import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AuthState {
  uid: string | null;
  token: string | null;
  preferredLang: string;
  setAuth: (data: { uid: string; token: string }) => void;
  setPreferredLang: (lang: string) => void;
  logout: () => void;
  isAuthenticated: () => boolean;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      uid: null,
      token: null,
      preferredLang: 'zh',

      setAuth: ({ uid, token }) => {
        localStorage.setItem('glynk_token', token);
        set({ uid, token });
      },

      setPreferredLang: (lang) => {
        set({ preferredLang: lang });
      },

      logout: () => {
        localStorage.removeItem('glynk_token');
        set({ uid: null, token: null, preferredLang: 'zh' });
      },

      isAuthenticated: () => get().token !== null,
    }),
    {
      name: 'glynk-auth',
    },
  ),
);
