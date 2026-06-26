// src/components/calendar/CalendarMonthView.tsx
import React from 'react';
import { useTheme } from '@/src/theme/ThemeContext';
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
  const { colors, isDark } = useTheme();
  const today = new Date();

  return (
    <View style={{ backgroundColor: colors.surface }} className=" rounded-3xl mx-6 p-4 shadow-sm border border-primary/5 mb-6">
      <View className="flex-row justify-center items-center mb-4">
        <Pressable onPress={prevMonth} className="px-4 py-2">
          <Text className="text-base text-textSecondary">◀</Text>
        </Pressable>
        <Text style={{ color: colors.text }} className="text-[17px] font-extrabold  mx-4 capitalize">
          {currentMonth.toLocaleDateString('es-ES', { month: 'long', year: 'numeric' })}
        </Text>
        <Pressable onPress={nextMonth} className="px-4 py-2">
          <Text className="text-base text-textSecondary">▶</Text>
        </Pressable>
      </View>

      {/* Days of Week Header */}
      <View className="flex-row justify-between mb-2 px-2">
        {weekDays.map((wd) => (
          <Text key={wd} className="w-[12%] text-center text-xs font-bold text-textSecondary">
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
          let textColor = colors.text; // Default to theme text color

          if (isToday) {
            containerClass += "bg-primary";
            textColor = '#FFFFFF'; // White text for today bubble
            textClass += "font-bold";
          } else if (isSelected) {
            containerClass += "bg-primary/15 border border-primary/35";
            textColor = isDark ? '#FFFFFF' : colors.primary; 
            textClass += "font-bold";
            if (hasAct) {
              containerClass += " border-2 border-primary";
            }
          } else if (hasAct) {
            containerClass += "border-2 border-primary bg-transparent";
            textClass += "font-bold";
          } else {
            containerClass += "bg-transparent";
          }

          return (
            <Pressable
              key={idx}
              onPress={() => setSelectedDate(day)}
              className={containerClass}
            >
              <Text className={textClass} style={{ color: textColor }}>
                {day.getDate()}
              </Text>
            </Pressable>
          );
        })}
      </View>
    </View>
  );
}

