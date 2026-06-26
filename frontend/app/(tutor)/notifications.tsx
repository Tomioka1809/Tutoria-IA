// app/(tutor)/notifications.tsx
import React from 'react';
import { useTheme } from '@/src/theme/ThemeContext';
import { View } from 'react-native';
import { useNotifications } from '@/src/components/notifications/useNotifications';
import { NotificationsHeader } from '@/src/components/notifications/NotificationsHeader';
import { NotificationsList } from '@/src/components/notifications/NotificationsList';

export default function NotificationsScreen() {
  const { colors } = useTheme();
  const { notifications, isLoading, fetchNotifications, handleMarkRead } = useNotifications();

  return (
    <View style={{ backgroundColor: colors.background }} className="flex-1  pt-16">
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
