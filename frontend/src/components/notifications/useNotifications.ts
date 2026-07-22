import { useEffect, useCallback } from 'react';
import { useNotificationStore } from '@/src/store/notification';
import { useActivityStore } from '../../store/activity';
import { useTranslation } from 'react-i18next';
import { parseLocalActivityDate } from '../calendar/calendar-items';

export function useNotifications() {
  const { t } = useTranslation();
  const notifications = useNotificationStore((state) => state.notifications);
  const fetchNotifications = useNotificationStore((state) => state.fetchNotifications);
  const markAsRead = useNotificationStore((state) => state.markAsRead);
  const isLoading = useNotificationStore((state) => state.isLoading);

  const activities = useActivityStore((state) => state.activities);

  useEffect(() => {
    fetchNotifications();
  }, [fetchNotifications]);

  const formatTime12h = useCallback((time24: string) => {
    try {
      const [hoursStr, minutesStr] = time24.split(':');
      const hours = parseInt(hoursStr, 10);
      const minutes = parseInt(minutesStr, 10);
      const ampm = hours >= 12 ? 'PM' : 'AM';
      const displayHours = hours % 12 === 0 ? 12 : hours % 12;
      const displayMinutes = String(minutes).padStart(2, '0');
      const formattedHours = String(displayHours).padStart(2, '0');
      return `${formattedHours}:${displayMinutes} ${ampm}`;
    } catch {
      return time24;
    }
  }, []);

  const handleMarkRead = useCallback((id: any, isRead: boolean) => {
    if (typeof id === 'number' && !isRead) {
      markAsRead(id);
    }
  }, [markAsRead]);

  const getUnifiedNotifications = useCallback(() => {
    const filteredBackend = notifications
      .filter((n) => {
        const titleLower = n.title.toLowerCase();
        return (
          titleLower.includes('asignada') ||
          titleLower.includes('programada') ||
          titleLower.includes('cancelada')
        );
      })
      .map((n) => {
        let title = n.title;
        if (title.includes('Sesión Programada') || title.includes('tutoría asignada')) {
          title = t('notifications.assignedTitle');
        } else if (title.toLowerCase().includes('cancelada')) {
          title = t('notifications.cancelledTitle');
        }
        return {
          ...n,
          title,
        };
      });

    const now = new Date();
    const limit = new Date(now.getTime() + 24 * 60 * 60 * 1000);
    const reminders: any[] = [];

    activities.forEach((act) => {
      try {
        const actDate = parseLocalActivityDate(act);
        if (actDate && actDate.getTime() > now.getTime() && actDate.getTime() <= limit.getTime()) {
          const timeFormatted = formatTime12h(act.time);
          const isAcademic = act.type === 'Tutoría Académica';
          const title = isAcademic
            ? t('notifications.sessionReminder', { time: timeFormatted })
            : t('notifications.activityReminder', { name: act.name, time: timeFormatted });

          reminders.push({
            id: `reminder_local_${act.id}`,
            title,
            body: t('notifications.activityBody', { name: act.name, time: timeFormatted }),
            type: 'reminder',
            is_read: false,
            created_at: actDate.toISOString(),
          });
        }
      } catch {
        // Safe fallback
      }
    });

    const combined = [...filteredBackend, ...reminders];
    combined.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());

    return combined;
  }, [notifications, activities, t, formatTime12h]);

  return {
    notifications: getUnifiedNotifications(),
    isLoading,
    fetchNotifications,
    handleMarkRead,
  };
}
