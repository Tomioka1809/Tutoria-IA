// src/components/calendar/CalendarMonthView.tsx
import React from 'react';
import { View, Text, Pressable } from 'react-native';

interface CalendarMonthViewProps {
  currentMonth: Date;
  prevMonth: () => void;
  nextMonth: () => void;
  weekDays: string[];
  days: (Date | null)[];
  selectedDate: Date;
  setSelectedDate: (date: Date) => void;
  hasActivities: (day: Date | null) => boolean;
}

export function CalendarMonthView({
  currentMonth,
  prevMonth,
  nextMonth,
  weekDays,
  days,
  selectedDate,
  setSelectedDate,
  hasActivities,
}: CalendarMonthViewProps) {
  const today = new Date();

  return (
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
          if (!day) {
            return <View key={idx} className="w-[14.28%] aspect-square" />;
          }

          const isToday =
            day.getDate() === today.getDate() &&
            day.getMonth() === today.getMonth() &&
            day.getFullYear() === today.getFullYear();

          const isSelected =
            day.getDate() === selectedDate.getDate() &&
            day.getMonth() === selectedDate.getMonth() &&
            day.getFullYear() === selectedDate.getFullYear();

          const hasAct = hasActivities(day);

          // Estilos basados en requerimientos:
          // 1. Hoy: círculo morado relleno
          // 2. Seleccionado (y no hoy): círculo morado claro / de selección
          // 3. Actividad programada (y no hoy): contorno/circunferencia morada
          let containerClass = "w-[14.28%] aspect-square justify-center items-center rounded-full my-0.5 ";
          let textClass = "text-sm font-semibold ";

          if (isToday) {
            containerClass += "bg-[#9A3BEE]";
            textClass += "text-white font-bold";
          } else if (isSelected) {
            containerClass += "bg-[#9A3BEE]/15 border border-[#9A3BEE]/35";
            textClass += "text-[#9A3BEE] font-bold";
            if (hasAct) {
              containerClass += " border-2 border-[#9A3BEE]";
            }
          } else if (hasAct) {
            containerClass += "border-2 border-[#9A3BEE] bg-transparent";
            textClass += "text-[#111130] font-bold";
          } else {
            containerClass += "bg-transparent";
            textClass += "text-[#111130]";
          }

          return (
            <Pressable
              key={idx}
              onPress={() => setSelectedDate(day)}
              className={containerClass}
            >
              <Text className={textClass}>
                {day.getDate()}
              </Text>
            </Pressable>
          );
        })}
      </View>
    </View>
  );
}
