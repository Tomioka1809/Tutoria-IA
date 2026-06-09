// app/(tabs)/notifications.tsx
import React from 'react';
import { View } from 'react-native';
import { useNotifications } from '@/src/components/notifications/useNotifications';
import { NotificationsHeader } from '@/src/components/notifications/NotificationsHeader';
import { NotificationsList } from '@/src/components/notifications/NotificationsList';

export default function NotificationsScreen() {
  const { notifications, isLoading, fetchNotifications, handleMarkRead } = useNotifications();

  return (
    <View className="flex-1 bg-[#F5F5FB] pt-16">
      <NotificationsHeader />

      <NotificationsList
        notifications={notifications}
        isLoading={isLoading}
        onRefresh={fetchNotifications}
        onMarkRead={handleMarkRead}
      />
    </View>
  );
}
