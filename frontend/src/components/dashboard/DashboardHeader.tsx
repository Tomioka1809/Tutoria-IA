// src/components/dashboard/DashboardHeader.tsx
import React from 'react';
import { View, Text } from 'react-native';

interface DashboardHeaderProps {
  firstName: string;
}

export function DashboardHeader({ firstName }: DashboardHeaderProps) {
  return (
    <View className="px-6 pt-16 pb-6 bg-[#F5F5FB]">
      <Text className="text-[32px] font-extrabold text-[#111130] tracking-tight">
        ¡Hola, {firstName}! 👋
      </Text>
      <Text className="text-sm text-[#8E8EA0] mt-1 font-medium">
        ¿Qué quieres aprender hoy?
      </Text>
    </View>
  );
}
