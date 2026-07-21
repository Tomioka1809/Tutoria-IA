// src/components/calendar/useCalendar.ts
import { useState, useEffect } from 'react';
import { useAuthStore } from '@/src/store/auth';
import { useSessionStore } from '@/src/store/session';
import { useActivityStore } from '../../store/activity';
import client from '@/src/api/client';
import { User } from '@/src/types';
import { useTranslation } from 'react-i18next';

export function useCalendar() {
  const { t } = useTranslation();
  const { user } = useAuthStore();
  const { sessions, fetchSessions, createSession, updateSessionStatus } = useSessionStore();
  const { activities, addActivity, deleteActivity, clearPastActivities } = useActivityStore();

  const [selectedDate, setSelectedDate] = useState<Date>(new Date(2026, 4, 19)); // Defaults to May 19, 2026
  const [currentMonth, setCurrentMonth] = useState<Date>(new Date(2026, 4, 1));

  const [students, setStudents] = useState<User[]>([]);
  const [isDataLoading, setIsDataLoading] = useState(false);

  useEffect(() => {
    fetchSessions();
    clearPastActivities();
    
    if (user?.role === 'tutor' || user?.role === 'admin') {
      fetchTutorData();
    }
  }, [user]);

  const fetchTutorData = async () => {
    setIsDataLoading(true);
    try {
      const studRes = await client.get('/tutors/students');
      setStudents(studRes.data);
    } catch (e) {
      console.error('Failed to load scheduling data', e);
    } finally {
      setIsDataLoading(false);
    }
  };

  // Crea una actividad local o programa una sesión en el backend si es Tutoría Académica
  const addNewActivity = async (activityData: {
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
      // studentId can be null, which means "A todos"
      try {
        const scheduledAtStr = `${activityData.date}T${activityData.time}:00`;
        
        // Buscar el ID de tipo de servicio para Tutoría Académica
        let serviceTypeId = 1;
        try {
          const serviceRes = await client.get('/tutors/service-types');
          const matchedService = serviceRes.data.find(
            (s: any) => s.name.toLowerCase() === activityData.type.toLowerCase()
          );
          if (matchedService) {
            serviceTypeId = matchedService.id;
          } else if (serviceRes.data.length > 0) {
            serviceTypeId = serviceRes.data[0].id;
          }
        } catch (err) {
          console.warn('Could not fetch service types, using fallback ID 1', err);
        }

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
        fetchSessions(); // Recargar sesiones del backend
      } catch (error) {
        console.error(error);
        alert(t('calendar.scheduledError'));
      }
    } else {
      // Guardar localmente
      addActivity({
        name: activityData.name,
        type: activityData.type,
        date: activityData.date,
        time: activityData.time,
      });
    }
  };

  // Cambia el estado de una sesión de tutoría
  const changeBackendSessionStatus = async (sessionId: number, newStatus: string) => {
    try {
      await updateSessionStatus(sessionId, newStatus);
      alert(t('calendar.statusSuccess'));
      fetchSessions(); // Recargar sesiones
    } catch (error) {
      console.error(error);
      alert(t('calendar.statusError'));
    }
  };

  const getDaysInMonth = (date: Date) => {
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
  };

  const days = getDaysInMonth(currentMonth);
  const weekDays = t('calendar.weekDays', { returnObjects: true }) as string[];

  const prevMonth = () => {
    setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1, 1));
  };

  const nextMonth = () => {
    setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1, 1));
  };

  // Comprueba si un día tiene sesiones del backend (activas) o actividades locales
  const hasActivities = (day: Date | null) => {
    if (!day) return false;
    
    const year = day.getFullYear();
    const month = String(day.getMonth() + 1).padStart(2, '0');
    const date = String(day.getDate()).padStart(2, '0');
    const dayStr = `${year}-${month}-${date}`;

    const hasLocal = activities.some((act: any) => act.date === dayStr);
    const hasBackend = sessions.some(
      (s) => s.scheduled_at.startsWith(dayStr) && s.status !== 'cancelada'
    );

    return hasLocal || hasBackend;
  };

  // Devuelve la lista unificada y ordenada de actividades locales y sesiones del backend
  const getUnifiedActivities = () => {
    // Mapear sesiones de backend activas (no canceladas) al formato común de actividad
    const mappedSessions = sessions
      .filter((s) => s.status !== 'cancelada')
      .map((s) => {
        let type: 'Tutoría Académica' | 'Tutoría Personal' | 'Tutoría Profesional' | 'Trabajos' = 'Tutoría Académica';
        const name = s.service_type?.name || 'Tutoría Académica';

        if (name.includes('Personal')) {
          type = 'Tutoría Personal';
        } else if (name.includes('Profesional')) {
          type = 'Tutoría Profesional';
        } else if (name.includes('Tarea') || name.includes('Entrega') || name.includes('Trabajo')) {
          type = 'Trabajos';
        }

        return {
          id: `session_${s.id}`,
          name: s.title || s.notes || name,
          type,
          date: s.scheduled_at.split('T')[0],
          time: s.scheduled_at.split('T')[1].substring(0, 5),
          isBackend: true,
          rawId: s.id,
          status: s.status,
          notes: s.notes,
          location: s.location,
          tutorName: s.tutor?.full_name,
          studentName: s.student?.full_name,
        };
      });

    // Mapear actividades locales
    const mappedLocals = activities.map((act: any) => ({
      ...act,
      isBackend: false,
      rawId: 0,
    }));

    // Combinar
    const combined = [...mappedSessions, ...mappedLocals];

    // Ordenar cronológicamente (Fecha y Hora)
    combined.sort((a, b) => {
      const timeA = new Date(`${a.date}T${a.time}:00`).getTime();
      const timeB = new Date(`${b.date}T${b.time}:00`).getTime();
      return timeA - timeB;
    });

    return combined;
  };

  // Filtrar actividades unificadas a partir de la fecha seleccionada en adelante
  const filteredActivities = getUnifiedActivities().filter((act) => {
    const actDate = new Date(`${act.date}T00:00:00`);
    const selDate = new Date(selectedDate.getFullYear(), selectedDate.getMonth(), selectedDate.getDate());
    return actDate.getTime() >= selDate.getTime();
  });

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
