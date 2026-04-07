import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AuthState {
  uid: string | null;
  token: string | null;
  setAuth: (data: { uid: string; token: string }) => void;
  logout: () => void;
  isAuthenticated: () => boolean;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      uid: null,
      token: null,

      setAuth: ({ uid, token }) => {
        localStorage.setItem('glynk_token', token);
        set({ uid, token });
      },

      logout: () => {
        localStorage.removeItem('glynk_token');
        set({ uid: null, token: null });
      },

      isAuthenticated: () => get().token !== null,
    }),
    {
      name: 'glynk-auth',
    },
  ),
);
