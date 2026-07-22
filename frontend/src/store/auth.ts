import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { User } from '../types';
import client from '../api/client';
import { configureApiAuth } from '../api/auth-session';

interface AuthState {
  token: string | null;
  user: User | null;
  profileImage: string | null;
  setAuth: (token: string, user: User) => void;
  updateUser: (partial: Partial<User>) => void;
  updateProfile: (partial: Partial<User>) => Promise<void>;
  changePassword: (currentPassword: string, newPassword: string) => Promise<boolean>;
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
      updateProfile: async (partial) => {
        try {
          const res = await client.put<User>('/auth/profile', partial);
          set({ user: res.data });
        } catch (error) {
          console.error('Failed to update profile:', error);
          throw error;
        }
      },
      changePassword: async (current_password, new_password) => {
        try {
          await client.put('/auth/change-password', { current_password, new_password });
          return true;
        } catch (error) {
          console.error('Failed to change password:', error);
          return false;
        }
      },
      setProfileImage: (uri) => set({ profileImage: uri }),
      logout: () => set({ token: null, user: null, profileImage: null }),
    }),
    {
      name: 'tutoria-auth-storage',
      storage: createJSONStorage(() => AsyncStorage),
    }
  )
);

configureApiAuth({
  getToken: () => useAuthStore.getState().token,
  onUnauthorized: () => {
    useAuthStore.getState().logout();
  },
});
