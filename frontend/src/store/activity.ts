import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { shouldRetainStoredActivity } from '../components/calendar/calendar-items';

export interface Activity {
  id: string;
  name: string;
  type: string;
  date: string; // Formato YYYY-MM-DD
  time: string; // Formato HH:MM (24h)
}

interface ActivityState {
  activities: Activity[];
  addActivity: (activity: Omit<Activity, 'id'>) => void;
  deleteActivity: (id: string) => void;
  clearPastActivities: () => void;
}

export const useActivityStore = create<ActivityState>()(
  persist(
    (set) => ({
      activities: [],
      addActivity: (activityData) => {
        const newActivity: Activity = {
          ...activityData,
          id: Math.random().toString(36).substring(2, 9),
        };
        set((state) => ({
          activities: [...state.activities, newActivity],
        }));
      },
      deleteActivity: (id) =>
        set((state) => ({
          activities: state.activities.filter((act) => act.id !== id),
        })),
      clearPastActivities: () =>
        set((state) => {
          const now = new Date();
          const activeActivities = state.activities.filter((act) =>
            shouldRetainStoredActivity(act, now)
          );
          return { activities: activeActivities };
        }),
    }),
    {
      name: 'tutoria-activities-storage',
      storage: createJSONStorage(() => AsyncStorage),
    }
  )
);
