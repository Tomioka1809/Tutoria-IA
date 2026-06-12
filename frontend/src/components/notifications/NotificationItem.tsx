// src/components/notifications/NotificationItem.tsx
import React from 'react';
import { View, Text, Pressable } from 'react-native';
import { Notification } from '@/src/types';

interface NotificationItemProps {
  notification: Notification;
  onPress: () => void;
}

export function NotificationItem({ notification, onPress }: NotificationItemProps) {
  // Determinar color e icono según título o tipo
  let iconStr = '🔔';
  let iconBg = 'bg-[#F3E8FF]';
  let titleColor = 'text-[#1E1E2F]';

  if (notification.title.includes('Cancelada') || notification.title.includes('cancelada')) {
    iconStr = '❌';
    iconBg = 'bg-[#FFEAEA]';
    titleColor = 'text-[#EF4444]';
  } else if (notification.title.includes('Recordatorio')) {
    iconStr = '📅';
    iconBg = 'bg-[#F3E8FF]';
  } else if (notification.title.includes('asignada') || notification.title.includes('Nueva tutoría')) {
    iconStr = '🔔';
    iconBg = 'bg-[#F3E8FF]';
  }

  // Formatear fecha de creación a tiempo relativo
  const formatRelativeTime = (dateStr: string) => {
    try {
      const created = new Date(dateStr);
      const now = new Date();
      const diffMs = now.getTime() - created.getTime();
      
      if (diffMs < 0) {
        return 'Hace unos momentos';
      }
      
      const diffMins = Math.floor(diffMs / (60 * 1000));
      const diffHours = Math.floor(diffMs / (60 * 60 * 1000));
      const diffDays = Math.floor(diffMs / (24 * 60 * 60 * 1000));

      if (diffMins < 1) {
        return 'Hace unos momentos';
      } else if (diffMins < 60) {
        return `Hace ${diffMins} ${diffMins === 1 ? 'minuto' : 'minutos'}`;
      } else if (diffHours < 24) {
        return `Hace ${diffHours} ${diffHours === 1 ? 'hora' : 'horas'}`;
      } else {
        return `Hace ${diffDays} ${diffDays === 1 ? 'día' : 'días'}`;
      }
    } catch (e) {
      return 'Hace poco';
    }
  };

  return (
    <Pressable
      onPress={onPress}
      className="bg-white border border-[#EEEDFE] rounded-3xl p-4 mb-3 shadow-sm flex-row items-center"
    >
      <View className={`w-12 h-12 rounded-[20px] items-center justify-center mr-4 ${iconBg}`}>
        <Text className="text-xl">{iconStr}</Text>
      </View>

      <View className="flex-1">
        <Text className={`text-sm font-bold ${titleColor}`}>{notification.title}</Text>
        <Text className="text-xs text-[#8E8EA0] mt-1 font-medium">
          {formatRelativeTime(notification.created_at)}
        </Text>
      </View>

      {!notification.is_read ? (
        <View className="w-2.5 h-2.5 rounded-full bg-[#9A3BEE] ml-2" />
      ) : null}
    </Pressable>
  );
}

