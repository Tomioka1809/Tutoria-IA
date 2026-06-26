// app/(tutor)/calendar.tsx
import React, { useState } from 'react';
import { useTheme } from '@/src/theme/ThemeContext';
import { View, Text, Modal, Pressable } from 'react-native';
import { useCalendar } from '@/src/components/calendar/useCalendar';
import { CalendarHeader } from '@/src/components/calendar/CalendarHeader';
import { CalendarMonthView } from '@/src/components/calendar/CalendarMonthView';
import { CalendarActivitiesList } from '@/src/components/calendar/CalendarActivitiesList';
import { AddActivityModal } from '@/src/components/calendar/AddActivityModal';
import { ActivityDetailsModal } from '@/src/components/calendar/ActivityDetailsModal';

interface UnifiedActivity {
  id: string;
  name: string;
  type: string;
  date: string;
  time: string;
  isBackend: boolean;
  rawId: number;
  status?: string;
  notes?: string;
  location?: string;
  tutorName?: string;
  studentName?: string;
}

export default function CalendarScreen() {
  const { colors } = useTheme();
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
    changeBackendSessionStatus,
    students,
    fetchTutorData,
  } = useCalendar();

  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [activityToDelete, setActivityToDelete] = useState<UnifiedActivity | null>(null);
  const [activityToView, setActivityToView] = useState<UnifiedActivity | null>(null);

  const handleDeleteConfirm = async () => {
    if (!activityToDelete) return;

    if (activityToDelete.isBackend) {
      await changeBackendSessionStatus(activityToDelete.rawId, 'cancelada');
    } else {
      deleteActivity(activityToDelete.id);
    }

    setActivityToDelete(null);
  };

  const isAnyModalOpen = isAddModalOpen || activityToDelete !== null || activityToView !== null;

  return (
    <View style={{ flex: 1, backgroundColor: colors.background, paddingTop: 64 }}>
      {/* El fondo se vuelve semi-transparente cuando hay un modal abierto */}
      <View style={{ flex: 1, opacity: isAnyModalOpen ? 0.35 : 1 }}>
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
          onAddPress={() => {
            if (user?.role === 'tutor' || user?.role === 'admin') {
              fetchTutorData();
            }
            setIsAddModalOpen(true);
          }}
          onViewPress={(activity) => setActivityToView(activity)}
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

      {/* Modal de Detalles de Actividad */}
      <ActivityDetailsModal
        activity={activityToView}
        onClose={() => setActivityToView(null)}
        userRole={user?.role}
        onStatusChange={(sessionId, newStatus) => {
          changeBackendSessionStatus(sessionId, newStatus);
          setActivityToView({ ...activityToView!, status: newStatus });
        }}
      />

      {/* Ventana flotante/modal de confirmación de eliminación */}
      <Modal visible={activityToDelete !== null} animationType="fade" transparent={true}>
        <View className="flex-1 bg-black/45 justify-center items-center">
          <View style={{ backgroundColor: colors.surface, borderRadius: 24, padding: 24, width: '85%', maxWidth: 340, shadowColor: '#000', shadowOffset: {width: 0, height: 10}, shadowOpacity: 0.1, shadowRadius: 20, elevation: 5, borderWidth: 1, borderColor: colors.border }}>
            <Text style={{ fontSize: 18, fontWeight: 'bold', color: colors.text, textAlign: 'center', marginBottom: 8 }}>
              Confirmar eliminación
            </Text>
            <Text style={{ fontSize: 14, color: colors.textSecondary, textAlign: 'center', marginBottom: 24 }}>
              ¿Deseas borrar la actividad "{activityToDelete?.name}"?
            </Text>

            <View className="flex-row justify-between">
              <Pressable
                onPress={() => setActivityToDelete(null)}
                style={{ width: '47%', backgroundColor: colors.border, paddingVertical: 12, borderRadius: 16, alignItems: 'center', justifyContent: 'center' }}
              >
                <Text style={{ color: colors.textSecondary, fontWeight: 'bold', fontSize: 14 }}>Cancelar</Text>
              </Pressable>

              <Pressable
                onPress={handleDeleteConfirm}
                style={{ width: '47%', backgroundColor: colors.danger, paddingVertical: 12, borderRadius: 16, alignItems: 'center', justifyContent: 'center' }}
              >
                <Text style={{ color: '#FFFFFF', fontWeight: 'bold', fontSize: 14 }}>Borrar</Text>
              </Pressable>
            </View>
          </View>
        </View>
      </Modal>
    </View>
  );
}
