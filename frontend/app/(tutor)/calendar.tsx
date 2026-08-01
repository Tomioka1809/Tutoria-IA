// app/(tutor)/calendar.tsx
import React, { useState } from 'react';
import { useTheme } from '@/src/theme/ThemeContext';
import { View, Text, Modal, Pressable, Platform } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useCalendar } from '@/src/components/calendar/useCalendar';
import { CalendarHeader } from '@/src/components/calendar/CalendarHeader';
import { CalendarMonthView } from '@/src/components/calendar/CalendarMonthView';
import { CalendarActivitiesList } from '@/src/components/calendar/CalendarActivitiesList';
import { AddActivityModal } from '@/src/components/calendar/AddActivityModal';
import { ActivityDetailsModal } from '@/src/components/calendar/ActivityDetailsModal';
import { CalendarLoadState } from '@/src/components/calendar/CalendarLoadState';
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

  const insets = useSafeAreaInsets();
  const screenTopPadding = Math.max(insets.top + 16, 64);
  const minimumBottomPadding = Platform.OS === 'ios' ? 24 : 12;
  const bottomPadding = Math.max(insets.bottom, minimumBottomPadding);
  const tabBarBaseHeight = 62;
  const totalTabBarHeight = tabBarBaseHeight + bottomPadding;
  const scrollBottomPadding = totalTabBarHeight + 24;

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
    isDataLoading,
    loadError,
    retryLoad,
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
    <View style={{ flex: 1, backgroundColor: colors.background, paddingTop: screenTopPadding }}>
      {/* El fondo se vuelve semi-transparente cuando hay un modal abierto */}
      <View style={{ flex: 1, opacity: isAnyModalOpen ? 0.35 : 1 }}>
        <CalendarHeader />

        <CalendarLoadState isLoading={isDataLoading} error={loadError} onRetry={retryLoad}>
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
            bottomPadding={scrollBottomPadding}
            onAddPress={() => {
              if (user?.role === 'tutor' || user?.role === 'admin') {
                fetchTutorData();
              }
              setIsAddModalOpen(true);
            }}
            onViewPress={(activity) => setActivityToView(activity)}
            onDeletePress={(activity) => setActivityToDelete(activity)}
          />
        </CalendarLoadState>
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
              {t('calendar.confirmDelete')}
            </Text>
            <Text style={{ fontSize: 14, color: colors.textSecondary, textAlign: 'center', marginBottom: 24 }}>
              {t('calendar.confirmDeleteMessage', { name: activityToDelete?.name })}
            </Text>

            <View className="flex-row justify-between">
              <Pressable
                onPress={() => setActivityToDelete(null)}
                style={{ width: '47%', backgroundColor: colors.border, paddingVertical: 12, borderRadius: 16, alignItems: 'center', justifyContent: 'center' }}
              >
                <Text style={{ color: colors.textSecondary, fontWeight: 'bold', fontSize: 14 }}>{t('common.cancel')}</Text>
              </Pressable>

              <Pressable
                onPress={handleDeleteConfirm}
                style={{ width: '47%', backgroundColor: colors.danger, paddingVertical: 12, borderRadius: 16, alignItems: 'center', justifyContent: 'center' }}
              >
                <Text style={{ color: '#FFFFFF', fontWeight: 'bold', fontSize: 14 }}>{t('common.delete')}</Text>
              </Pressable>
            </View>
          </View>
        </View>
      </Modal>
    </View>
  );
}
