import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import AsyncStorage from '@react-native-async-storage/async-storage';

export interface Activity {
  id: string;
  name: string;
  type: 'Tutoría Académica' | 'Sesión de Apoyo Psicológico' | 'Trabajos';
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
          const activeActivities = state.activities.filter((act) => {
            // Unir fecha (YYYY-MM-DD) y hora (HH:MM) para crear un objeto Date
            const [year, month, day] = act.date.split('-').map(Number);
            const [hours, minutes] = act.time.split(':').map(Number);
            
            // Creamos la fecha local de la actividad
            const actDate = new Date(year, month - 1, day, hours, minutes, 0, 0);
            
            // Si la fecha de la actividad es mayor o igual a la hora actual, se mantiene.
            // Si ya pasó, retorna false (se descarta)
            return actDate.getTime() >= now.getTime();
          });
          return { activities: activeActivities };
        }),
    }),
    {
      name: 'tutoria-activities-storage',
      storage: createJSONStorage(() => AsyncStorage),
    }
  )
);
