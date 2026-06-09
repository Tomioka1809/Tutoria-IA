// app/(tabs)/calendar.tsx
import React from 'react';
import { View } from 'react-native';
import { useCalendar } from '@/src/components/calendar/useCalendar';
import { CalendarHeader } from '@/src/components/calendar/CalendarHeader';
import { CalendarMonthView } from '@/src/components/calendar/CalendarMonthView';
import { CalendarActivitiesList } from '@/src/components/calendar/CalendarActivitiesList';
import { ScheduleSessionModal } from '@/src/components/calendar/ScheduleSessionModal';

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
    hasSessions,
    filteredSessions,
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
  } = useCalendar();

  return (
    <View className="flex-1 bg-[#F5F5FB] pt-16">
      <CalendarHeader />

      <CalendarMonthView
        currentMonth={currentMonth}
        prevMonth={prevMonth}
        nextMonth={nextMonth}
        weekDays={weekDays}
        days={days}
        selectedDate={selectedDate}
        setSelectedDate={setSelectedDate}
        hasSessions={hasSessions}
      />

      <CalendarActivitiesList
        userRole={user?.role}
        filteredSessions={filteredSessions}
        onAddPress={handleOpenScheduleModal}
      />

      <ScheduleSessionModal
        isModalOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        selectedDate={selectedDate}
        students={students}
        serviceTypes={serviceTypes}
        selectedStudentId={selectedStudentId}
        setSelectedStudentId={setSelectedStudentId}
        selectedServiceTypeId={selectedServiceTypeId}
        setSelectedServiceTypeId={setSelectedServiceTypeId}
        sessionHour={sessionHour}
        setSessionHour={setSessionHour}
        sessionNotes={sessionNotes}
        setSessionNotes={setSessionNotes}
        isSubmitting={isSubmitting}
        isDataLoading={isDataLoading}
        onSubmit={handleCreateSession}
      />
    </View>
  );
}
