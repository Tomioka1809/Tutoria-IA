import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { User } from '../types';

interface AuthState {
  token: string | null;
  user: User | null;
  profileImage: string | null;
  setAuth: (token: string, user: User) => void;
  updateUser: (partial: Partial<User>) => void;
  setProfileImage: (uri: string | null) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      profileImage: null,
      setAuth: (token, user) => set({ token, user }),
      updateUser: (partial) =>
        set((state) => ({
          user: state.user ? { ...state.user, ...partial } : state.user,
        })),
      setProfileImage: (uri) => set({ profileImage: uri }),
      logout: () => set({ token: null, user: null, profileImage: null }),
    }),
    {
      name: 'tutoria-auth-storage',
      storage: createJSONStorage(() => AsyncStorage),
    }
  )
);
