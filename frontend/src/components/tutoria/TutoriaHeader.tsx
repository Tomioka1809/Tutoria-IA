// src/components/tutoria/TutoriaHeader.tsx
import React from 'react';
import { View, Text, Pressable } from 'react-native';

interface TutoriaHeaderProps {
  onRefresh: () => void;
}

export function TutoriaHeader({ onRefresh }: TutoriaHeaderProps) {
  return (
    <View className="bg-white border-b border-[#EEEDFE] px-6 pt-16 pb-4 flex-row items-center justify-between">
      <View className="flex-row items-center flex-1">
        <Pressable onPress={() => {}} className="mr-3 p-1">
          <Text className="text-xl text-[#26215C]">←</Text>
        </Pressable>

        <View className="w-10 h-10 rounded-full bg-[#9A3BEE]/10 items-center justify-center border border-[#9A3BEE]/25 mr-3">
          <Text className="text-xl">🦖</Text>
        </View>

        <View className="flex-1">
          <Text className="text-sm font-extrabold text-[#111130]">TutorIA AI</Text>
          <View className="flex-row items-center mt-0.5">
            <View className="w-2 h-2 rounded-full bg-[#10B981] mr-1.5" />
            <Text className="text-[10px] text-[#8E8EA0] font-semibold">En línea</Text>
          </View>
        </View>
      </View>

      <Pressable onPress={onRefresh} className="p-2">
        <Text className="text-lg text-[#26215C]">↻</Text>
      </Pressable>
    </View>
  );
}
