import React, { useState, useEffect } from 'react';
import { View, Text, ScrollView, Pressable, TextInput, Modal, ActivityIndicator } from 'react-native';
import { useAuthStore } from '../../src/store/auth';
import { useSessionStore } from '../../src/store/session';
import client from '../../src/api/client';
import { User, ServiceType } from '../../src/types';

export default function CalendarScreen() {
  const { user } = useAuthStore();
  const { sessions, fetchSessions, createSession } = useSessionStore();

  const [selectedDate, setSelectedDate] = useState<Date>(new Date(2026, 4, 19)); // Defaults to May 19, 2026 as per mockup
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

  // Generate days in current month helper
  const getDaysInMonth = (date: Date) => {
    const year = date.getFullYear();
    const month = date.getMonth();
    // Monday is first day of week as per mockup
    const firstDayIndex = new Date(year, month, 1).getDay();
    const firstDay = firstDayIndex === 0 ? 6 : firstDayIndex - 1; // Adjust for Mon-Sun
    const numDays = new Date(year, month + 1, 0).getDate();
    
    const days = [];
    for (let i = 0; i < firstDay; i++) {
      days.push(null);
    }
    for (let i = 1; i <= numDays; i++) {
      days.push(new Date(year, month, i));
    }
    return days;
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

  return (
    <View className="flex-1 bg-[#F5F5FB] pt-16">
      {/* Centered Calendar Header */}
      <View className="px-6 items-center mb-6">
        <Text className="text-[20px] font-bold text-[#111130]">Calendario</Text>
      </View>

      {/* Monthly view selector matching mockup */}
      <View className="bg-white rounded-3xl mx-6 p-4 shadow-sm border border-[#7F77DD]/5 mb-6">
        <View className="flex-row justify-center items-center mb-4">
          <Pressable onPress={prevMonth} className="px-4 py-2">
            <Text className="text-base text-[#8E8EA0]">◀</Text>
          </Pressable>
          <Text className="text-[17px] font-extrabold text-[#111130] mx-4 capitalize">
            {currentMonth.toLocaleDateString('es-ES', { month: 'long', year: 'numeric' })}
          </Text>
          <Pressable onPress={nextMonth} className="px-4 py-2">
            <Text className="text-base text-[#8E8EA0]">▶</Text>
          </Pressable>
        </View>

        {/* Days of Week Header */}
        <View className="flex-row justify-between mb-2 px-2">
          {weekDays.map((wd) => (
            <Text key={wd} className="w-[12%] text-center text-xs font-bold text-[#8E8EA0]">
              {wd}
            </Text>
          ))}
        </View>

        {/* Grid Days */}
        <View className="flex-row flex-wrap px-2">
          {days.map((day, idx) => {
            const isSelected =
              day && day.toDateString() === selectedDate.toDateString();
            const hasSess = hasSessions(day);

            return (
              <Pressable
                key={idx}
                disabled={!day}
                onPress={() => day && setSelectedDate(day)}
                className={`w-[14.28%] aspect-square justify-center items-center rounded-full my-0.5 ${
                  isSelected ? 'bg-[#9A3BEE]' : ''
                }`}
              >
                {day ? (
                  <View className="items-center">
                    <Text
                      className={`text-sm font-semibold ${
                        isSelected ? 'text-white' : 'text-[#111130]'
                      }`}
                    >
                      {day.getDate()}
                    </Text>
                    {hasSess && !isSelected ? (
                      <View className="w-1 h-1 rounded-full mt-0.5 bg-[#9A3BEE]" />
                    ) : null}
                  </View>
                ) : null}
              </Pressable>
            );
          })}
        </View>
      </View>

      {/* Agenda activities section matching mockup */}
      <View className="flex-1 px-6">
        <View className="flex-row justify-between items-center mb-4">
          <Text className="text-[#1E1E2F] font-bold text-base">Próximas actividades</Text>
          {user?.role === 'tutor' || user?.role === 'admin' ? (
            <Pressable onPress={handleOpenScheduleModal}>
              <Text className="text-sm font-bold text-[#9A3BEE]">+ Añadir</Text>
            </Pressable>
          ) : null}
        </View>

        <ScrollView className="flex-1" showsVerticalScrollIndicator={false}>
          {filteredSessions.length > 0 ? (
            filteredSessions.map((session) => {
              // Custom colors matching mockup
              let iconStr = '📖';
              let iconBg = 'bg-[#F3E8FF]';
              let iconColor = 'text-[#9C3FE4]';

              if (session.service_type.name.includes('Personal')) {
                iconStr = '💙';
                iconBg = 'bg-[#EFF6FF]';
                iconColor = 'text-[#3B82F6]';
              } else if (session.service_type.name.includes('Psicológico')) {
                iconStr = '🧠';
                iconBg = 'bg-[#FDF2F8]';
                iconColor = 'text-[#EC4899]';
              }

              return (
                <View
                  key={session.id}
                  className="bg-white border border-[#EEEDFE] rounded-3xl p-4 mb-3 shadow-sm flex-row items-center"
                >
                  <View className={`w-12 h-12 rounded-[20px] items-center justify-center mr-4 ${iconBg}`}>
                    <Text className="text-xl">{iconStr}</Text>
                  </View>

                  <View className="flex-1">
                    <Text className="text-sm font-bold text-[#1E1E2F]">{session.service_type.name}</Text>
                    <Text className="text-xs text-[#8E8EA0] mt-1 font-medium">
                      {new Date(session.scheduled_at).toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit',
                      })} - {new Date(new Date(session.scheduled_at).getTime() + 60*60*1000).toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </Text>
                  </View>
                </View>
              );
            })
          ) : (
            // Default mockup placeholder items if database is empty for this date
            <View>
              <View className="bg-white border border-[#EEEDFE] rounded-3xl p-4 mb-3 shadow-sm flex-row items-center">
                <View className="w-12 h-12 rounded-[20px] bg-[#F3E8FF] items-center justify-center mr-4">
                  <Text className="text-xl">📖</Text>
                </View>
                <View className="flex-1">
                  <Text className="text-sm font-bold text-[#1E1E2F]">Tutoría Académica</Text>
                  <Text className="text-xs text-[#8E8EA0] mt-1 font-medium">10:00 AM - 11:00 AM</Text>
                </View>
              </View>

              <View className="bg-white border border-[#EEEDFE] rounded-3xl p-4 mb-3 shadow-sm flex-row items-center">
                <View className="w-12 h-12 rounded-[20px] bg-[#E0F2FE] items-center justify-center mr-4">
                  <Text className="text-xl">📅</Text>
                </View>
                <View className="flex-1">
                  <Text className="text-sm font-bold text-[#1E1E2F]">Reunión con Tutor</Text>
                  <Text className="text-xs text-[#8E8EA0] mt-1 font-medium">03:00 PM - 04:00 PM</Text>
                </View>
              </View>

              <View className="bg-white border border-[#EEEDFE] rounded-3xl p-4 mb-3 shadow-sm flex-row items-center">
                <View className="w-12 h-12 rounded-[20px] bg-[#FCE7F3] items-center justify-center mr-4">
                  <Text className="text-xl">🧠</Text>
                </View>
                <View className="flex-1">
                  <Text className="text-sm font-bold text-[#1E1E2F]">Sesión de Apoyo Psicológico</Text>
                  <Text className="text-xs text-[#8E8EA0] mt-1 font-medium">04:30 PM - 05:30 PM</Text>
                </View>
              </View>
            </View>
          )}
        </ScrollView>
      </View>

      {/* Schedule Tutoring Modal */}
      <Modal visible={isModalOpen} animationType="slide" transparent={true}>
        <View className="flex-1 bg-black/50 justify-end">
          <View className="bg-white rounded-t-[40px] px-6 pt-8 pb-12">
            <View className="flex-row justify-between items-center mb-6">
              <Text className="text-xl font-bold text-[#26215C]">Programar Tutoría</Text>
              <Pressable onPress={() => setIsModalOpen(false)}>
                <Text className="text-[#9A3BEE] font-bold text-sm">Cerrar</Text>
              </Pressable>
            </View>

            {isDataLoading ? (
              <ActivityIndicator size="large" color="#9A3BEE" className="py-12" />
            ) : (
              <View>
                <View className="mb-4 bg-[#EEEDFE] p-3.5 rounded-xl border border-[#7F77DD]/20">
                  <Text className="text-xs text-[#26215C]/60 font-semibold">Fecha Seleccionada</Text>
                  <Text className="text-base text-[#26215C] font-bold mt-1">
                    {selectedDate.toLocaleDateString('es-ES', { weekday: 'long', day: 'numeric', month: 'long' })}
                  </Text>
                </View>

                {/* Student Select */}
                <View className="mb-4">
                  <Text className="text-xs text-[#26215C] font-semibold mb-2 ml-1">Estudiante</Text>
                  <View className="bg-[#EEEDFE]/50 border border-[#7F77DD]/30 rounded-xl p-1 flex-row flex-wrap">
                    {students.map((student) => (
                      <Pressable
                        key={student.id}
                        onPress={() => setSelectedStudentId(student.id)}
                        className={`px-3 py-2 rounded-lg m-1 border ${
                          selectedStudentId === student.id
                            ? 'bg-[#9A3BEE] border-[#9A3BEE]'
                            : 'bg-white border-[#7F77DD]/20'
                        }`}
                      >
                        <Text
                          className={`text-xs font-semibold ${
                            selectedStudentId === student.id ? 'text-white' : 'text-[#26215C]/80'
                          }`}
                        >
                          {student.full_name}
                        </Text>
                      </Pressable>
                    ))}
                  </View>
                </View>

                {/* Service Type Select */}
                <View className="mb-4">
                  <Text className="text-xs text-[#26215C] font-semibold mb-2 ml-1">Tipo de Servicio</Text>
                  <View className="bg-[#EEEDFE]/50 border border-[#7F77DD]/30 rounded-xl p-1 flex-row flex-wrap">
                    {serviceTypes.map((type) => (
                      <Pressable
                        key={type.id}
                        onPress={() => setSelectedServiceTypeId(type.id)}
                        className={`px-3 py-2 rounded-lg m-1 border ${
                          selectedServiceTypeId === type.id
                            ? 'bg-[#9A3BEE] border-[#9A3BEE]'
                            : 'bg-white border-[#7F77DD]/20'
                        }`}
                      >
                        <Text
                          className={`text-xs font-semibold ${
                            selectedServiceTypeId === type.id ? 'text-white' : 'text-[#26215C]/80'
                          }`}
                        >
                          {type.name}
                        </Text>
                      </Pressable>
                    ))}
                  </View>
                </View>

                {/* Hour selection input */}
                <View className="mb-4">
                  <Text className="text-xs text-[#26215C] font-semibold mb-2 ml-1">Hora (Formato 24h)</Text>
                  <TextInput
                    value={sessionHour}
                    onChangeText={setSessionHour}
                    placeholder="10:00"
                    className="bg-[#EEEDFE]/50 border border-[#7F77DD]/30 rounded-xl px-4 py-3 text-[#26215C] font-bold"
                  />
                </View>

                {/* Notes Input */}
                <View className="mb-6">
                  <Text className="text-xs text-[#26215C] font-semibold mb-2 ml-1">Notas / Detalles</Text>
                  <TextInput
                    value={sessionNotes}
                    onChangeText={setSessionNotes}
                    placeholder="Repasar dudas..."
                    className="bg-[#EEEDFE]/50 border border-[#7F77DD]/30 rounded-xl px-4 py-3 text-[#26215C]"
                    multiline
                    numberOfLines={2}
                  />
                </View>

                <Pressable
                  onPress={handleCreateSession}
                  disabled={isSubmitting}
                  className="bg-[#9A3BEE] rounded-xl py-3 items-center justify-center shadow-md"
                >
                  {isSubmitting ? (
                    <ActivityIndicator color="white" />
                  ) : (
                    <Text className="text-white font-bold text-base">Crear Tutoría</Text>
                  )}
                </Pressable>
              </View>
            )}
          </View>
        </View>
      </Modal>
    </View>
  );
}
