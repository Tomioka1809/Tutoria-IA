// src/components/dashboard/useDashboard.ts
import { useEffect, useCallback } from 'react';
import { useAuthStore } from '@/src/store/auth';
import { useStreakStore } from '@/src/store/streak';
import { useSessionStore } from '@/src/store/session';

export function useDashboard() {
  const user = useAuthStore((state) => state.user);
  const role = user?.role;
  const streak = useStreakStore((state) => state.streak);
  const fetchStreak = useStreakStore((state) => state.fetchStreak);
  const isStreakLoading = useStreakStore((state) => state.isLoading);
  const sessions = useSessionStore((state) => state.sessions);
  const fetchSessions = useSessionStore((state) => state.fetchSessions);
  const isSessionsLoading = useSessionStore((state) => state.isLoading);

  const onRefresh = useCallback(() => {
    if (role === 'estudiante') {
      fetchStreak();
    }
    fetchSessions();
  }, [role, fetchStreak, fetchSessions]);

  useEffect(() => {
    if (role === 'estudiante') {
      fetchStreak();
    }
    fetchSessions();
  }, [role, fetchStreak, fetchSessions]);

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
