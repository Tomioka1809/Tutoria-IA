// src/components/notifications/NotificationsList.tsx
import React from 'react';
import { ScrollView, View, Text, RefreshControl } from 'react-native';
import { Notification } from '@/src/types';
import { NotificationItem } from './NotificationItem';
import { Feather } from '@expo/vector-icons';
import { useTheme } from '@/src/theme/ThemeContext';
import { useTranslation } from 'react-i18next';

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
  const { colors } = useTheme();
  const { t } = useTranslation();
  return (
    <ScrollView
      className="flex-1 px-6"
      showsVerticalScrollIndicator={false}
      refreshControl={
        <RefreshControl
          refreshing={isLoading}
          onRefresh={onRefresh}
          colors={[colors.primary]}
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
        <View style={{ backgroundColor: colors.surface }} className="items-center justify-center py-20 px-4 /50 border border-dashed border-border rounded-[32px] mt-4">
          <View className="w-16 h-16 rounded-[24px] bg-[#F3E8FF] items-center justify-center mb-4">
            <Feather name="bell" size={28} color={colors.primary} />
          </View>
          <Text style={{ color: colors.text }} className="text-base font-bold  text-center">
            {t('notifications.emptyTitle')}
          </Text>
          <Text className="text-xs text-textSecondary mt-1.5 text-center max-w-[200px]">
            {t('notifications.emptyDescription')}
          </Text>
        </View>
      )}
    </ScrollView>
  );
}
