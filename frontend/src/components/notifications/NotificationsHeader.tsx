import React from 'react';
import { View, Text, Pressable } from 'react-native';
import { useRouter } from 'expo-router';

export function NotificationsHeader() {
  const router = useRouter();

  return (
    <View className="px-6 mb-6 flex-row items-center justify-between">
      <View className="flex-row items-center">
        <Pressable onPress={() => router.back()} className="mr-3 p-1">
          <Text className="text-xl text-[#26215C]">←</Text>
        </Pressable>
        <Text className="text-[20px] font-bold text-[#111130]">Notificaciones</Text>
      </View>
      
      {/* Filter selection mock dropdown */}
      <Pressable className="bg-white border border-[#9A3BEE] rounded-xl px-4 py-1.5 flex-row items-center shadow-sm">
        <Text className="text-xs font-semibold text-[#9A3BEE] mr-1.5">Todas</Text>
        <Text className="text-xs text-[#9A3BEE]">∨</Text>
      </Pressable>
    </View>
  );
}
