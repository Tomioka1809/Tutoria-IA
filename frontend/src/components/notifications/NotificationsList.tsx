// src/components/notifications/NotificationsList.tsx
import React from 'react';
import { ScrollView, View, Text, RefreshControl } from 'react-native';
import { Notification } from '@/src/types';
import { NotificationItem } from './NotificationItem';
import { Feather } from '@expo/vector-icons';

interface NotificationsListProps {
  notifications: Notification[];
  isLoading: boolean;
  onRefresh: () => void;
  onMarkRead: (id: number, isRead: boolean) => void;
}

export function NotificationsList({
  notifications,
  isLoading,
  onRefresh,
  onMarkRead,
}: NotificationsListProps) {
  return (
    <ScrollView
      className="flex-1 px-6"
      showsVerticalScrollIndicator={false}
      refreshControl={
        <RefreshControl
          refreshing={isLoading}
          onRefresh={onRefresh}
          colors={['#9A3BEE']}
        />
      }
    >
      {notifications.length > 0 ? (
        notifications.map((notif) => (
          <NotificationItem
            key={notif.id}
            notification={notif}
            onPress={() => onMarkRead(notif.id, notif.is_read)}
          />
        ))
      ) : (
        // Vista vacía con estilo premium si no hay notificaciones
        <View className="items-center justify-center py-20 px-4 bg-white/50 border border-dashed border-[#EEEDFE] rounded-[32px] mt-4">
          <View className="w-16 h-16 rounded-[24px] bg-[#F3E8FF] items-center justify-center mb-4">
            <Feather name="bell" size={28} color="#9A3BEE" />
          </View>
          <Text className="text-base font-bold text-[#1E1E2F] text-center">
            No tienes notificaciones
          </Text>
          <Text className="text-xs text-[#8E8EA0] mt-1.5 text-center max-w-[200px]">
            Aquí aparecerán tus recordatorios y tutorías asignadas
          </Text>
        </View>
      )}
    </ScrollView>
  );
}
