// app/(estudiante)/calendar.tsx
import React, { useState } from 'react';
import { useTheme } from '@/src/theme/ThemeContext';
import { View, Text, Modal, Pressable } from 'react-native';
import { useCalendar } from '@/src/components/calendar/useCalendar';
import { CalendarHeader } from '@/src/components/calendar/CalendarHeader';
import { CalendarMonthView } from '@/src/components/calendar/CalendarMonthView';
import { CalendarActivitiesList } from '@/src/components/calendar/CalendarActivitiesList';
import { AddActivityModal } from '@/src/components/calendar/AddActivityModal';
import { ActivityDetailsModal } from '@/src/components/calendar/ActivityDetailsModal';
import { useTranslation } from 'react-i18next';

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
  const { t } = useTranslation();
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
    <View style={{ backgroundColor: colors.background }} className="flex-1  pt-16">
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
      />

      {/* Ventana flotante/modal de confirmación de eliminación */}
      <Modal visible={activityToDelete !== null} animationType="fade" transparent={true}>
        <View className="flex-1 bg-black/45 justify-center items-center">
          <View style={{ backgroundColor: colors.surface }} className=" rounded-3xl p-6 w-[85%] max-w-[340px] shadow-2xl border border-gray-100">
            <Text style={{ color: colors.text }} className="text-lg font-bold  text-center mb-2">
              {t('calendar.confirmDelete')}
            </Text>
            <Text className="text-sm text-textSecondary text-center mb-6">
              {t('calendar.confirmDeleteMessage', { name: activityToDelete?.name })}
            </Text>

            <View className="flex-row justify-between">
              <Pressable
                onPress={() => setActivityToDelete(null)}
                className="w-[47%] bg-gray-100 py-3 rounded-2xl items-center justify-center"
              >
                <Text className="text-gray-500 font-bold text-sm">{t('common.cancel')}</Text>
              </Pressable>

              <Pressable
                onPress={handleDeleteConfirm}
                className="w-[47%] bg-red-500 py-3 rounded-2xl items-center justify-center shadow-md shadow-red-500/20"
              >
                <Text className="text-white font-bold text-sm">{t('common.delete')}</Text>
              </Pressable>
            </View>
          </View>
        </View>
      </Modal>
    </View>
  );
}
