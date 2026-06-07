import { create } from 'zustand';
import client from '../api/client';
import { Notification } from '../types';

interface NotificationState {
  notifications: Notification[];
  isLoading: boolean;
  fetchNotifications: () => Promise<void>;
  markAsRead: (notificationId: number) => Promise<void>;
  getUnreadCount: () => number;
}

export const useNotificationStore = create<NotificationState>((set, get) => ({
  notifications: [],
  isLoading: false,
  fetchNotifications: async () => {
    set({ isLoading: true });
    try {
      const response = await client.get<Notification[]>('/notifications/');
      set({ notifications: response.data });
    } catch (error) {
      console.error('Failed to fetch notifications:', error);
    } finally {
      set({ isLoading: false });
    }
  },
  markAsRead: async (notificationId) => {
    try {
      const response = await client.put<Notification>(
        `/notifications/${notificationId}/read`
      );
      set((state) => ({
        notifications: state.notifications.map((n) =>
          n.id === notificationId ? response.data : n
        ),
      }));
    } catch (error) {
      console.error('Failed to mark notification as read:', error);
    }
  },
  getUnreadCount: () => {
    return get().notifications.filter((n) => !n.is_read).length;
  },
}));
