// src/components/notifications/useNotifications.ts
import { useEffect } from 'react';
import { useNotificationStore } from '@/src/store/notification';
import { useActivityStore } from '../../store/activity';
import { useSessionStore } from '../../store/session';
import { useTranslation } from 'react-i18next';

export function useNotifications() {
  const { t } = useTranslation();
  const { notifications, fetchNotifications, markAsRead, isLoading } = useNotificationStore();
  const { activities } = useActivityStore();
  const { sessions, fetchSessions } = useSessionStore();

  useEffect(() => {
    fetchNotifications();
    fetchSessions();
  }, []);

  const formatTime12h = (time24: string) => {
    try {
      const [hoursStr, minutesStr] = time24.split(':');
      const hours = parseInt(hoursStr, 10);
      const minutes = parseInt(minutesStr, 10);
      const ampm = hours >= 12 ? 'PM' : 'AM';
      const displayHours = hours % 12 === 0 ? 12 : hours % 12;
      const displayMinutes = String(minutes).padStart(2, '0');
      const formattedHours = String(displayHours).padStart(2, '0');
      return `${formattedHours}:${displayMinutes} ${ampm}`;
    } catch (e) {
      return time24;
    }
  };

  const handleMarkRead = (id: any, isRead: boolean) => {
    if (typeof id === 'number' && !isRead) {
      markAsRead(id);
    }
  };

  const getUnifiedNotifications = () => {
    // 1. Filtrar las notificaciones del backend para mostrar solo:
    //    - "Nueva tutoría asignada" (normalizando desde "Nueva Sesión Programada")
    //    - "Tutoría Cancelada"
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

    // 2. Generar recordatorios dinámicos con 24h de anticipación
    const now = new Date();
    const limit = new Date(now.getTime() + 24 * 60 * 60 * 1000); // 24 horas en adelante
    const reminders: any[] = [];

    // Mapear actividades locales en las próximas 24 horas
    activities.forEach((act: any) => {
      try {
        const [year, month, day] = act.date.split('-').map(Number);
        const [hours, minutes] = act.time.split(':').map(Number);
        const actDate = new Date(year, month - 1, day, hours, minutes, 0, 0);

        if (actDate.getTime() > now.getTime() && actDate.getTime() <= limit.getTime()) {
          const timeFormatted = formatTime12h(act.time);
          const isAcademic = act.type === 'Tutoría Académica';
          const title = isAcademic
            ? t('notifications.sessionReminder', { time: timeFormatted })
            : t('notifications.activityReminder', { name: act.name, time: timeFormatted });

          reminders.push({
            id: `reminder_local_${act.id}`,
            title: title,
            body: t('notifications.activityBody', { name: act.name, time: timeFormatted }),
            type: 'reminder',
            is_read: false,
            created_at: new Date(now.getTime() - 15 * 60 * 1000).toISOString(), // Simular hace 15 mins
          });
        }
      } catch (e) {
        console.warn('Error parsing activity date for reminder', e);
      }
    });

    // Mapear tutorías activas (backend) en las próximas 24 horas
    sessions
      .filter((s) => s.status !== 'cancelada')
      .forEach((s) => {
        try {
          const sDate = new Date(s.scheduled_at);

          if (sDate.getTime() > now.getTime() && sDate.getTime() <= limit.getTime()) {
            const timePart = s.scheduled_at.split('T')[1].substring(0, 5);
            const timeFormatted = formatTime12h(timePart);
            const name = s.notes || s.service_type?.name || 'Tutoría Académica';
            const isAcademic = !s.service_type?.name || 
                               s.service_type.name.includes('Académica') || 
                               s.service_type.name.includes('Tutoría');
            const title = isAcademic
              ? t('notifications.sessionReminder', { time: timeFormatted })
              : t('notifications.activityReminder', { name, time: timeFormatted });

            reminders.push({
              id: `reminder_session_${s.id}`,
              title: title,
              body: t('notifications.tutoringBody', { name, time: timeFormatted }),
              type: 'reminder',
              is_read: false,
              created_at: new Date(now.getTime() - 30 * 60 * 1000).toISOString(), // Simular hace 30 mins
            });
          }
        } catch (e) {
          console.warn('Error parsing session date for reminder', e);
        }
      });

    // Combinar y ordenar descendentemente
    const combined = [...filteredBackend, ...reminders];
    combined.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());

    return combined;
  };

  return {
    notifications: getUnifiedNotifications(),
    isLoading,
    fetchNotifications,
    handleMarkRead,
  };
}
