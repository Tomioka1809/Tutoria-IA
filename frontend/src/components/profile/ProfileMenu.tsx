// src/components/profile/ProfileMenu.tsx
import React from 'react';
import { View, Text, Pressable } from 'react-native';

interface ProfileMenuProps {
  onLogout: () => void;
}

export function ProfileMenu({ onLogout }: ProfileMenuProps) {
  const menuItems = [
    { name: 'Configuración', icon: '⚙️', action: () => alert('Ajustes en desarrollo.') },
    { name: 'Privacidad', icon: '🔒', action: () => alert('Privacidad en desarrollo.') },
    { name: 'Centro de ayuda', icon: '❓', action: () => alert('Centro de ayuda en desarrollo.') },
    { name: 'Cerrar sesión', icon: '➔', action: onLogout, color: 'text-red-500' },
  ];

  return (
    <View className="px-6">
      {menuItems.map((item, index) => (
        <Pressable
          key={index}
          onPress={item.action}
          className="bg-white border border-[#EEEDFE] rounded-2xl px-5 py-4.5 mb-3 shadow-sm flex-row justify-between items-center"
        >
          <View className="flex-row items-center">
            <View className="w-8 h-8 rounded-full bg-[#F5F5FB] items-center justify-center mr-3">
              <Text className="text-base">{item.icon}</Text>
            </View>
            <Text className={`text-sm font-bold ${item.color || 'text-[#1E1E2F]'}`}>{item.name}</Text>
          </View>
          <Text className="text-base text-[#8E8EA0] font-semibold">➔</Text>
        </Pressable>
      ))}
    </View>
  );
}
