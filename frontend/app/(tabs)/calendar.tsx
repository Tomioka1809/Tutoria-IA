// app/(tabs)/calendar.tsx
import React, { useState } from 'react';
import { View } from 'react-native';
import { useCalendar } from '@/src/components/calendar/useCalendar';
import { CalendarHeader } from '@/src/components/calendar/CalendarHeader';
import { CalendarMonthView } from '@/src/components/calendar/CalendarMonthView';
import { CalendarActivitiesList } from '@/src/components/calendar/CalendarActivitiesList';
import { AddActivityModal } from '@/src/components/calendar/AddActivityModal';

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
    addActivity,
    deleteActivity,
  } = useCalendar();

  const [isAddModalOpen, setIsAddModalOpen] = useState(false);

  return (
    <View className="flex-1 bg-[#F5F5FB] pt-16">
      {/* El fondo se vuelve semi-transparente cuando el modal está abierto para simular desenfoque */}
      <View className="flex-1" style={{ opacity: isAddModalOpen ? 0.35 : 1 }}>
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
          onAddPress={() => setIsAddModalOpen(true)}
          onDeletePress={deleteActivity}
        />
      </View>

      <AddActivityModal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        selectedDate={selectedDate}
        onAdd={addActivity}
      />
    </View>
  );
}

