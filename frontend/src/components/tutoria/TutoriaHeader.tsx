// src/components/tutoria/TutoriaHeader.tsx
import React from 'react';
import { useTheme } from '@/src/theme/ThemeContext';
import { View, Text, Pressable } from 'react-native';

interface TutoriaHeaderProps {
  onRefresh: () => void;
  onBackPress?: () => void;
}

export function TutoriaHeader({ onRefresh, onBackPress }: TutoriaHeaderProps) {
  const { colors } = useTheme();
  return (
    <View style={{ backgroundColor: colors.surface }} className=" border-b border-border px-6 pt-16 pb-4 flex-row items-center justify-between">
      <View className="flex-row items-center flex-1">
        <Pressable onPress={onBackPress} className="mr-3 p-1">
          <Text className="text-xl" style={{ color: colors.text }}>←</Text>
        </Pressable>

        <View className="w-10 h-10 rounded-full bg-primary/10 items-center justify-center border border-primary/25 mr-3">
          <Text className="text-xl">🦖</Text>
        </View>

        <View className="flex-1">
          <Text style={{ color: colors.text }} className="text-sm font-extrabold ">TutorIA AI</Text>
          <View className="flex-row items-center mt-0.5">
            <View className="w-2 h-2 rounded-full bg-[#10B981] mr-1.5" />
            <Text className="text-[10px] text-textSecondary font-semibold">En línea</Text>
          </View>
        </View>
      </View>

      <Pressable onPress={onRefresh} className="p-2">
        <Text className="text-lg" style={{ color: colors.text }}>↻</Text>
      </Pressable>
    </View>
  );
}
