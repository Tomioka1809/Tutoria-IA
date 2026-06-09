// src/components/notifications/NotificationItem.tsx
import React from 'react';
import { View, Text, Pressable } from 'react-native';
import { Notification } from '@/src/types';

interface NotificationItemProps {
  notification: Notification;
  onPress: () => void;
}

export function NotificationItem({ notification, onPress }: NotificationItemProps) {
  // Determine colors and icon based on notification title/type
  let iconStr = '🔔';
  let iconBg = 'bg-[#F3E8FF]';

  if (notification.title.includes('Sesión') || notification.type === 'session') {
    iconStr = '📅';
    iconBg = 'bg-[#F3E8FF]';
  } else if (notification.title.includes('Práctica')) {
    iconStr = '💼';
    iconBg = 'bg-[#FFEDD5]';
  } else if (notification.title.includes('Bienestar')) {
    iconStr = '⭐';
    iconBg = 'bg-[#ECFEFF]';
  } else if (notification.title.includes('Mesa') || notification.title.includes('Beca')) {
    iconStr = '✈️';
    iconBg = 'bg-[#DBEAFE]';
  }

  return (
    <Pressable
      onPress={onPress}
      className="bg-white border border-[#EEEDFE] rounded-3xl p-4 mb-3 shadow-sm flex-row items-center"
    >
      <View className={`w-12 h-12 rounded-[20px] items-center justify-center mr-4 ${iconBg}`}>
        <Text className="text-xl">{iconStr}</Text>
      </View>

      <View className="flex-1">
        <Text className="text-sm font-bold text-[#1E1E2F]">{notification.title}</Text>
        <Text className="text-xs text-[#8E8EA0] mt-1 font-medium">Hace 2 horas</Text>
      </View>

      {!notification.is_read ? (
        <View className="w-2.5 h-2.5 rounded-full bg-[#9A3BEE] ml-2" />
      ) : null}
    </Pressable>
  );
}
