import { create } from 'zustand';
import client from '../api/client';
import { Streak } from '../types';
import { reportApiError } from '../services/error-feedback';

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
      reportApiError(error, 'errors.loadStreak');
    } finally {
      set({ isLoading: false });
    }
  },
}));
