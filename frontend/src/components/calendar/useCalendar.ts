// src/components/calendar/useCalendar.ts
import { useState, useEffect } from 'react';
import { useAuthStore } from '@/src/store/auth';
import { useSessionStore } from '@/src/store/session';
import client from '@/src/api/client';
import { User, ServiceType } from '@/src/types';

export function useCalendar() {
  const { user } = useAuthStore();
  const { sessions, fetchSessions, createSession } = useSessionStore();

  const [selectedDate, setSelectedDate] = useState<Date>(new Date(2026, 4, 19)); // Defaults to May 19, 2026
  const [currentMonth, setCurrentMonth] = useState<Date>(new Date(2026, 4, 1));

  // Scheduling Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [students, setStudents] = useState<User[]>([]);
  const [serviceTypes, setServiceTypes] = useState<ServiceType[]>([]);
  const [selectedStudentId, setSelectedStudentId] = useState<number | null>(null);
  const [selectedServiceTypeId, setSelectedServiceTypeId] = useState<number | null>(null);
  const [sessionHour, setSessionHour] = useState('10:00');
  const [sessionNotes, setSessionNotes] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isDataLoading, setIsDataLoading] = useState(false);

  useEffect(() => {
    fetchSessions();
  }, []);

  const fetchTutorData = async () => {
    setIsDataLoading(true);
    try {
      const studRes = await client.get('/tutors/students');
      const serviceRes = await client.get('/tutors/service-types');
      setStudents(studRes.data);
      setServiceTypes(serviceRes.data);
      if (studRes.data.length > 0) setSelectedStudentId(studRes.data[0].id);
      if (serviceRes.data.length > 0) setSelectedServiceTypeId(serviceRes.data[0].id);
    } catch (e) {
      console.error('Failed to load scheduling data', e);
    } finally {
      setIsDataLoading(false);
    }
  };

  const handleOpenScheduleModal = () => {
    setIsModalOpen(true);
    fetchTutorData();
  };

  const handleCreateSession = async () => {
    if (!selectedStudentId || !selectedServiceTypeId || !sessionHour) {
      alert('Por favor completa todos los campos obligatorios.');
      return;
    }

    setIsSubmitting(true);
    try {
      const dateStr = selectedDate.toISOString().split('T')[0];
      const scheduledAtStr = `${dateStr}T${sessionHour}:00`;

      await createSession({
        student_id: selectedStudentId,
        tutor_id: user!.id,
        service_type_id: selectedServiceTypeId,
        scheduled_at: scheduledAtStr,
        notes: sessionNotes || undefined,
      });

      setIsModalOpen(false);
      setSessionNotes('');
      alert('¡Tutoría programada con éxito!');
    } catch (error) {
      console.error(error);
      alert('Hubo un error al programar la tutoría.');
    } finally {
      setIsSubmitting(false);
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

  const hasSessions = (day: Date | null) => {
    if (!day) return false;
    const dayStr = day.toISOString().split('T')[0];
    return sessions.some((s) => s.scheduled_at.startsWith(dayStr));
  };

  const filteredSessions = sessions.filter((s) => {
    const selectedStr = selectedDate.toISOString().split('T')[0];
    return s.scheduled_at.startsWith(selectedStr);
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
    hasSessions,
    filteredSessions,
    // Modal & Scheduling
    isModalOpen,
    setIsModalOpen,
    students,
    serviceTypes,
    selectedStudentId,
    setSelectedStudentId,
    selectedServiceTypeId,
    setSelectedServiceTypeId,
    sessionHour,
    setSessionHour,
    sessionNotes,
    setSessionNotes,
    isSubmitting,
    isDataLoading,
    handleOpenScheduleModal,
    handleCreateSession,
  };
}
