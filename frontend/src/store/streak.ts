import { create } from 'zustand';
import client from '../api/client';
import { Streak } from '../types';

interface StreakState {
  streak: Streak | null;
  isLoading: boolean;
  fetchStreak: () => Promise<void>;
}

export const useStreakStore = create<StreakState>((set) => ({
  streak: null,
  isLoading: false,
  fetchStreak: async () => {
    set({ isLoading: true });
    try {
      const response = await client.get<Streak>('/streaks/');
      set({ streak: response.data });
    } catch (error) {
      console.error('Failed to fetch streak:', error);
    } finally {
      set({ isLoading: false });
    }
  },
}));
