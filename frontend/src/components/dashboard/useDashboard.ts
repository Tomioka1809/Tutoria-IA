// src/components/dashboard/useDashboard.ts
import { useEffect } from 'react';
import { useAuthStore } from '@/src/store/auth';
import { useStreakStore } from '@/src/store/streak';
import { useSessionStore } from '@/src/store/session';

export function useDashboard() {
  const { user } = useAuthStore();
  const { streak, fetchStreak, isLoading: isStreakLoading } = useStreakStore();
  const { sessions, fetchSessions, isLoading: isSessionsLoading } = useSessionStore();

  const onRefresh = () => {
    if (user?.role === 'estudiante') {
      fetchStreak();
    }
    fetchSessions();
  };

  useEffect(() => {
    if (user?.role === 'estudiante') {
      fetchStreak();
    }
    fetchSessions();
  }, []);

  const firstName = user?.full_name ? user.full_name.split(' ')[0] : '';

  return {
    user,
    streak,
    sessions,
    isLoading: isStreakLoading || isSessionsLoading,
    onRefresh,
    firstName,
  };
}
