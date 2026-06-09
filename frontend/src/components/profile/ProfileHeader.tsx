// src/components/profile/ProfileHeader.tsx
import React from 'react';
import { View, Text, Pressable } from 'react-native';
import { User } from '@/src/types';

interface ProfileHeaderProps {
  user: User | null;
}

export function ProfileHeader({ user }: ProfileHeaderProps) {
  return (
    <View className="bg-[#9A3BEE] pt-16 pb-24 px-6 rounded-b-[40px] relative">
      <View className="flex-row justify-between items-center mb-6">
        <Text className="text-white text-[20px] font-bold">Perfil</Text>
        <Pressable onPress={() => alert('Configuración general')}>
          <Text className="text-white text-xl">⚙️</Text>
        </Pressable>
      </View>
      
      {/* Profile Overlay Card */}
      <View className="absolute left-6 right-6 bottom-[-60px] bg-white rounded-3xl p-5 border border-[#EEEDFE] shadow-md flex-row items-center">
        <View className="w-16 h-16 rounded-full bg-[#E2E8F0] items-center justify-center mr-4">
          <Text className="text-3xl">👤</Text>
        </View>
        <View className="flex-1">
          <Text className="text-lg font-bold text-[#111130]">{user?.full_name || 'Sebastián Quispe'}</Text>
          <Text className="text-xs text-[#8E8EA0] font-medium mt-1">
            Código: {user?.student_code || '2123456'}
          </Text>
          <Text className="text-xs text-[#8E8EA0] font-medium mt-0.5" numberOfLines={1}>
            {user?.school || 'Ingeniería Informática y de Sistemas'}
          </Text>
          <Text className="text-[11px] text-[#8E8EA0] font-medium mt-0.5">
            VI Semestre
          </Text>
        </View>
      </View>
    </View>
  );
}
