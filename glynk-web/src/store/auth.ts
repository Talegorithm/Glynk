import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AuthState {
  uid: string | null;
  token: string | null;
  name: string | null;
  email: string | null;
  setAuth: (data: { uid: string; token: string; name?: string; email?: string }) => void;
  logout: () => void;
  isAuthenticated: () => boolean;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      uid: null,
      token: null,
      name: null,
      email: null,

      setAuth: ({ uid, token, name, email }) => {
        localStorage.setItem('glynk_token', token);
        set({ uid, token, name: name ?? null, email: email ?? null });
      },

      logout: () => {
        localStorage.removeItem('glynk_token');
        set({ uid: null, token: null, name: null, email: null });
      },

      isAuthenticated: () => get().token !== null,
    }),
    {
      name: 'glynk-auth',
    },
  ),
);
