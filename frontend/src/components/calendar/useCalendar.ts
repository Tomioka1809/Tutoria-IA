// src/components/calendar/useCalendar.ts
import { useState, useEffect } from 'react';
import { useAuthStore } from '@/src/store/auth';
import { useSessionStore } from '@/src/store/session';
import { useActivityStore } from '../../store/activity';
import client from '@/src/api/client';
import { User } from '@/src/types';

export function useCalendar() {
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
    type: 'Tutoría Académica' | 'Sesión de Apoyo Psicológico' | 'Trabajos';
    date: string;
    time: string;
    studentId?: number;
  }) => {
    if (activityData.type === 'Tutoría Académica') {
      if (!activityData.studentId) {
        alert('Por favor selecciona un estudiante.');
        return;
      }
      try {
        const scheduledAtStr = `${activityData.date}T${activityData.time}:00`;
        
        // Buscar el ID de tipo de servicio para Tutoría Académica
        let serviceTypeId = 1;
        try {
          const serviceRes = await client.get('/tutors/service-types');
          const academicService = serviceRes.data.find(
            (s: any) => s.name.includes('Académica') || s.name.includes('Tutoría')
          );
          if (academicService) {
            serviceTypeId = academicService.id;
          } else if (serviceRes.data.length > 0) {
            serviceTypeId = serviceRes.data[0].id;
          }
        } catch (err) {
          console.warn('Could not fetch service types, using fallback ID 1', err);
        }

        await createSession({
          student_id: activityData.studentId,
          tutor_id: user!.id,
          service_type_id: serviceTypeId,
          scheduled_at: scheduledAtStr,
          notes: activityData.name,
        });
        alert('¡Tutoría programada con éxito!');
        fetchSessions(); // Recargar sesiones del backend
      } catch (error) {
        console.error(error);
        alert('Hubo un error al programar la tutoría.');
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

  // Cancela una sesión de tutoría en el backend
  const cancelBackendSession = async (sessionId: number) => {
    try {
      await updateSessionStatus(sessionId, 'cancelada');
      alert('¡Tutoría cancelada con éxito!');
      fetchSessions(); // Recargar sesiones
    } catch (error) {
      console.error(error);
      alert('Hubo un error al cancelar la tutoría.');
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
  const weekDays = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'];

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
        let type: 'Tutoría Académica' | 'Sesión de Apoyo Psicológico' | 'Trabajos' = 'Tutoría Académica';
        const name = s.service_type?.name || 'Tutoría Académica';

        if (name.includes('Psicológico') || name.includes('Apoyo')) {
          type = 'Sesión de Apoyo Psicológico';
        } else if (name.includes('Tarea') || name.includes('Entrega') || name.includes('Trabajo')) {
          type = 'Trabajos';
        }

        return {
          id: `session_${s.id}`,
          name: s.notes || name,
          type,
          date: s.scheduled_at.split('T')[0],
          time: s.scheduled_at.split('T')[1].substring(0, 5),
          isBackend: true,
          rawId: s.id, // ID numérico para peticiones backend
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
    cancelBackendSession,
    students,
    isDataLoading,
    fetchTutorData,
  };
}
