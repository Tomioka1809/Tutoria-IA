// src/components/dashboard/StreakCard.tsx
import React from 'react';
import { View, Text } from 'react-native';

interface StreakCardProps {
  currentStreak?: number;
}

export function StreakCard({ currentStreak = 13 }: StreakCardProps) {
  return (
    <View className="px-6">
      <Text className="text-[17px] font-bold text-[#1E1E2F] mb-4">Racha de tutorías</Text>
      
      <View className="bg-white rounded-3xl p-6 border border-[#EEEDFE] shadow-sm items-center">
        <Text className="text-5xl mb-4">🔥</Text>
        <Text className="text-[#F97316] font-extrabold text-2xl tracking-tight text-center">
          ¡{currentStreak} días de racha!
        </Text>
        <Text className="text-[#8E8EA0] text-xs font-semibold text-center mt-2 px-4 leading-4">
          Completa tu siguiente tutoría para aumentar tu racha
        </Text>
      </View>
    </View>
  );
}
