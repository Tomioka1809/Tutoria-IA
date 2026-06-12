// app/(tabs)/calendar.tsx
import React, { useState } from 'react';
import { View, Text, Modal, Pressable } from 'react-native';
import { useCalendar } from '@/src/components/calendar/useCalendar';
import { CalendarHeader } from '@/src/components/calendar/CalendarHeader';
import { CalendarMonthView } from '@/src/components/calendar/CalendarMonthView';
import { CalendarActivitiesList } from '@/src/components/calendar/CalendarActivitiesList';
import { AddActivityModal } from '@/src/components/calendar/AddActivityModal';

interface UnifiedActivity {
  id: string;
  name: string;
  type: 'Tutoría Académica' | 'Sesión de Apoyo Psicológico' | 'Entrega de Tarea';
  date: string;
  time: string;
  isBackend: boolean;
  rawId: number;
}

export default function CalendarScreen() {
  const {
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
  } = useCalendar();

  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [activityToDelete, setActivityToDelete] = useState<UnifiedActivity | null>(null);

  const handleDeleteConfirm = async () => {
    if (!activityToDelete) return;

    if (activityToDelete.isBackend) {
      await cancelBackendSession(activityToDelete.rawId);
    } else {
      deleteActivity(activityToDelete.id);
    }

    setActivityToDelete(null);
  };

  const isAnyModalOpen = isAddModalOpen || activityToDelete !== null;

  return (
    <View className="flex-1 bg-[#F5F5FB] pt-16">
      {/* El fondo se vuelve semi-transparente cuando hay un modal abierto */}
      <View className="flex-1" style={{ opacity: isAnyModalOpen ? 0.35 : 1 }}>
        <CalendarHeader />

        <CalendarMonthView
          currentMonth={currentMonth}
          prevMonth={prevMonth}
          nextMonth={nextMonth}
          weekDays={weekDays}
          days={days}
          selectedDate={selectedDate}
          setSelectedDate={setSelectedDate}
          hasActivities={hasActivities}
        />

        <CalendarActivitiesList
          activities={filteredActivities}
          userRole={user?.role}
          onAddPress={() => setIsAddModalOpen(true)}
          onDeletePress={(activity) => setActivityToDelete(activity)}
        />
      </View>

      {/* Modal para añadir actividad */}
      <AddActivityModal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        selectedDate={selectedDate}
        userRole={user?.role}
        students={students}
        onAdd={addNewActivity}
      />

      {/* Ventana flotante/modal de confirmación de eliminación */}
      <Modal visible={activityToDelete !== null} animationType="fade" transparent={true}>
        <View className="flex-1 bg-black/45 justify-center items-center">
          <View className="bg-white rounded-3xl p-6 w-[85%] max-w-[340px] shadow-2xl border border-gray-100">
            <Text className="text-lg font-bold text-[#1E1E2F] text-center mb-2">
              Confirmar eliminación
            </Text>
            <Text className="text-sm text-[#8E8EA0] text-center mb-6">
              ¿Deseas borrar la actividad "{activityToDelete?.name}"?
            </Text>

            <View className="flex-row justify-between">
              <Pressable
                onPress={() => setActivityToDelete(null)}
                className="w-[47%] bg-gray-100 py-3 rounded-2xl items-center justify-center"
              >
                <Text className="text-gray-500 font-bold text-sm">Cancelar</Text>
              </Pressable>

              <Pressable
                onPress={handleDeleteConfirm}
                className="w-[47%] bg-red-500 py-3 rounded-2xl items-center justify-center shadow-md shadow-red-500/20"
              >
                <Text className="text-white font-bold text-sm">Borrar</Text>
              </Pressable>
            </View>
          </View>
        </View>
      </Modal>
    </View>
  );
}
