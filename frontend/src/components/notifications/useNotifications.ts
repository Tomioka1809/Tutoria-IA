// src/components/notifications/useNotifications.ts
import { useEffect } from 'react';
import { useNotificationStore } from '@/src/store/notification';

export function useNotifications() {
  const { notifications, fetchNotifications, markAsRead, isLoading } = useNotificationStore();

  useEffect(() => {
    fetchNotifications();
  }, []);

  const handleMarkRead = (id: number, isRead: boolean) => {
    if (!isRead) {
      markAsRead(id);
    }
  };

  return {
    notifications,
    isLoading,
    fetchNotifications,
    handleMarkRead,
  };
}
