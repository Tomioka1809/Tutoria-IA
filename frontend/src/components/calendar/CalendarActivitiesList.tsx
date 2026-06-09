// src/components/calendar/CalendarActivitiesList.tsx
import React from 'react';
import { View, Text, ScrollView, Pressable } from 'react-native';
import { Session } from '@/src/types';

interface CalendarActivitiesListProps {
  userRole?: string;
  filteredSessions: Session[];
  onAddPress: () => void;
}

export function CalendarActivitiesList({
  userRole,
  filteredSessions,
  onAddPress,
}: CalendarActivitiesListProps) {
  const canAdd = userRole === 'tutor' || userRole === 'admin';

  return (
    <View className="flex-1 px-6">
      <View className="flex-row justify-between items-center mb-4">
        <Text className="text-[#1E1E2F] font-bold text-base">Próximas actividades</Text>
        {canAdd ? (
          <Pressable onPress={onAddPress}>
            <Text className="text-sm font-bold text-[#9A3BEE]">+ Añadir</Text>
          </Pressable>
        ) : null}
      </View>

      <ScrollView className="flex-1" showsVerticalScrollIndicator={false}>
        {filteredSessions.length > 0 ? (
          filteredSessions.map((session) => {
            let iconStr = '📖';
            let iconBg = 'bg-[#F3E8FF]';

            if (session.service_type.name.includes('Personal')) {
              iconStr = '💙';
              iconBg = 'bg-[#EFF6FF]';
            } else if (session.service_type.name.includes('Psicológico')) {
              iconStr = '🧠';
              iconBg = 'bg-[#FDF2F8]';
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
                    })} - {new Date(new Date(session.scheduled_at).getTime() + 60 * 60 * 1000).toLocaleTimeString([], {
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
  );
}
