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
  hasSessions: (day: Date | null) => boolean;
}

export function CalendarMonthView({
  currentMonth,
  prevMonth,
  nextMonth,
  weekDays,
  days,
  selectedDate,
  setSelectedDate,
  hasSessions,
}: CalendarMonthViewProps) {
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
  );
}
