import { useState, useEffect, useCallback, useMemo } from 'react';
import { useAuthStore } from '@/src/store/auth';
import { useSessionStore } from '@/src/store/session';
import { useActivityStore } from '../../store/activity';
import client from '@/src/api/client';
import { User, Session } from '@/src/types';
import { useTranslation } from 'react-i18next';
import { buildCalendarItems, CalendarItem, LocalActivityInput, TutoringSessionInput } from './calendar-items';
import { reportApiError } from '@/src/services/error-feedback';

interface ServiceTypeOption {
  id: number;
  name: string;
}

export function useCalendar() {
  const { t } = useTranslation();
  const { user } = useAuthStore();
  const userRole = user?.role;

  const sessions = useSessionStore((state) => state.sessions);
  const fetchSessions = useSessionStore((state) => state.fetchSessions);
  const createSession = useSessionStore((state) => state.createSession);
  const updateSessionStatus = useSessionStore((state) => state.updateSessionStatus);

  const activities = useActivityStore((state) => state.activities);
  const addActivity = useActivityStore((state) => state.addActivity);
  const deleteActivityStore = useActivityStore((state) => state.deleteActivity);
  const clearPastActivities = useActivityStore((state) => state.clearPastActivities);

  const [selectedDate, setSelectedDate] = useState<Date>(() => new Date());
  const [currentMonth, setCurrentMonth] = useState<Date>(() => {
    const now = new Date();
    return new Date(now.getFullYear(), now.getMonth(), 1);
  });

  const [students, setStudents] = useState<User[]>([]);
  const [isDataLoading, setIsDataLoading] = useState(false);

  const fetchTutorData = useCallback(async () => {
    setIsDataLoading(true);
    try {
      const studRes = await client.get<User[]>('/tutors/students');
      setStudents(studRes.data);
    } catch (e) {
      reportApiError(e, 'errors.loadTutorData');
    } finally {
      setIsDataLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSessions();
    clearPastActivities();

    if (userRole === 'tutor' || userRole === 'admin') {
      fetchTutorData();
    }
  }, [userRole, fetchSessions, clearPastActivities, fetchTutorData]);

  const allItems = useMemo(() => {
    const actInputs: LocalActivityInput[] = activities;
    const sessionInputs: TutoringSessionInput[] = sessions.map((s: Session) => ({
      id: s.id,
      scheduled_at: s.scheduled_at,
      title: s.title,
      status: s.status,
      notes: s.notes,
      location: s.location,
      tutor: s.tutor ? { full_name: s.tutor.full_name } : undefined,
      student: s.student ? { full_name: s.student.full_name } : undefined,
      service_type: s.service_type ? { name: s.service_type.name } : undefined,
    }));
    return buildCalendarItems(actInputs, sessionInputs);
  }, [activities, sessions]);

  const addNewActivity = useCallback(async (activityData: {
    name: string;
    type: 'Tutoría Académica' | 'Tutoría Personal' | 'Tutoría Profesional' | 'Trabajos';
    date: string;
    time: string;
    studentId?: number | null;
    status?: string;
    notes?: string;
    location?: string;
  }) => {
    if (activityData.type.includes('Tutoría')) {
      try {
        let serviceTypeId: number | null = null;
        try {
          const serviceRes = await client.get<ServiceTypeOption[]>('/tutors/service-types');
          if (Array.isArray(serviceRes.data)) {
            const matchedService = serviceRes.data.find(
              (s) => s.name.toLowerCase() === activityData.type.toLowerCase()
            );
            if (matchedService) {
              serviceTypeId = matchedService.id;
            }
          }
        } catch (err) {
          reportApiError(err, 'errors.loadServiceTypes', { notify: false });
          throw err;
        }

        if (!serviceTypeId) {
          const noMatchErr = new Error('No matching service type found');
          reportApiError(noMatchErr, 'errors.loadServiceTypes', { notify: false });
          throw noMatchErr;
        }

        const scheduledAtStr = `${activityData.date}T${activityData.time}:00`;

        await createSession({
          student_id: activityData.studentId || undefined,
          tutor_id: user!.id,
          service_type_id: serviceTypeId,
          scheduled_at: scheduledAtStr,
          status: activityData.status || 'pendiente',
          title: activityData.name,
          notes: activityData.notes,
          location: activityData.location,
        });
        alert(t('calendar.scheduledSuccess'));
        fetchSessions();
      } catch {
        alert(t('calendar.scheduledError'));
      }
    } else {
      addActivity({
        name: activityData.name,
        type: activityData.type,
        date: activityData.date,
        time: activityData.time,
      });
    }
  }, [user, createSession, fetchSessions, addActivity, t]);

  const changeBackendSessionStatus = useCallback(async (sessionId: number, newStatus: string) => {
    try {
      await updateSessionStatus(sessionId, newStatus);
      alert(t('calendar.statusSuccess'));
      fetchSessions();
    } catch {
      alert(t('calendar.statusError'));
    }
  }, [updateSessionStatus, fetchSessions, t]);

  const deleteActivity = useCallback((activity: CalendarItem | { id: string; isBackend?: boolean } | string) => {
    if (typeof activity === 'object' && activity.isBackend) {
      return;
    }
    const raw = typeof activity === 'string'
      ? activity
      : ('localActivityId' in activity && activity.localActivityId
        ? activity.localActivityId
        : String(activity.id));
    const localId = raw.replace('activity:', '');
    deleteActivityStore(localId);
  }, [deleteActivityStore]);

  const getDaysInMonth = useCallback((date: Date) => {
    const year = date.getFullYear();
    const month = date.getMonth();
    const firstDayIndex = new Date(year, month, 1).getDay();
    const firstDay = firstDayIndex === 0 ? 6 : firstDayIndex - 1; // Mon-Sun
    const numDays = new Date(year, month + 1, 0).getDate();

    const daysList = [];
    for (let i = 0; i < firstDay; i++) {
      daysList.push(null);
    }
    for (let i = 1; i <= numDays; i++) {
      daysList.push(new Date(year, month, i));
    }
    return daysList;
  }, []);

  const days = useMemo(() => getDaysInMonth(currentMonth), [currentMonth, getDaysInMonth]);
  const weekDays = useMemo(() => t('calendar.weekDays', { returnObjects: true }) as string[], [t]);

  const prevMonth = useCallback(() => {
    setCurrentMonth((prev) => new Date(prev.getFullYear(), prev.getMonth() - 1, 1));
  }, []);

  const nextMonth = useCallback(() => {
    setCurrentMonth((prev) => new Date(prev.getFullYear(), prev.getMonth() + 1, 1));
  }, []);

  const hasActivities = useCallback((day: Date | null) => {
    if (!day) return false;
    const year = day.getFullYear();
    const month = String(day.getMonth() + 1).padStart(2, '0');
    const date = String(day.getDate()).padStart(2, '0');
    const dayStr = `${year}-${month}-${date}`;

    return allItems.some((item) => item.dateStr === dayStr && item.status !== 'cancelada');
  }, [allItems]);

  const filteredActivities = useMemo(() => {
    const selDateMidnight = new Date(selectedDate.getFullYear(), selectedDate.getMonth(), selectedDate.getDate()).getTime();
    return allItems.filter((item) => {
      const itemMidnight = new Date(item.startsAt.getFullYear(), item.startsAt.getMonth(), item.startsAt.getDate()).getTime();
      return itemMidnight >= selDateMidnight;
    });
  }, [allItems, selectedDate]);

  return {
    user,
    selectedDate,
    setSelectedDate,
    currentMonth,
    days,
    weekDays,
    prevMonth,
    nextMonth,
    hasActivities,
    filteredActivities,
    addNewActivity,
    deleteActivity,
    changeBackendSessionStatus,
    students,
    isDataLoading,
    fetchTutorData,
  };
}
