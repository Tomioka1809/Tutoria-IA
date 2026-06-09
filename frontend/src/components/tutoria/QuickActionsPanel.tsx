// src/components/tutoria/QuickActionsPanel.tsx
import React from 'react';
import { View, Pressable, Text } from 'react-native';

interface QuickActionsPanelProps {
  onActionPress: (actionText: string) => void;
}

export function QuickActionsPanel({ onActionPress }: QuickActionsPanelProps) {
  return (
    <View className="px-6 py-3 bg-[#F5F5FB] flex-row flex-wrap">
      <Pressable
        onPress={() => onActionPress('¿Cuál es mi plan de estudios actual?')}
        className="bg-white border border-[#EEEDFE] rounded-2xl px-4 py-2.5 mr-2 mb-2 flex-row items-center shadow-sm"
      >
        <Text className="text-xs text-[#26215C] font-semibold">📄 Plan de estudios</Text>
      </Pressable>
      <Pressable
        onPress={() => onActionPress('¿Cuándo es mi próxima tutoría?')}
        className="bg-white border border-[#EEEDFE] rounded-2xl px-4 py-2.5 mr-2 mb-2 flex-row items-center shadow-sm"
      >
        <Text className="text-xs text-[#26215C] font-semibold">📅 Tutorías</Text>
      </Pressable>
      <Pressable
        onPress={() => onActionPress('¿Dónde encuentro los reglamentos universitarios?')}
        className="bg-white border border-[#EEEDFE] rounded-2xl px-4 py-2.5 mb-2 flex-row items-center shadow-sm"
      >
        <Text className="text-xs text-[#26215C] font-semibold">📄 Reglamentos</Text>
      </Pressable>
    </View>
  );
}
