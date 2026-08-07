import React from 'react';
import { useTheme } from '@/src/theme/ThemeContext';
import { View, Text, Pressable } from 'react-native';
import Feather from '@expo/vector-icons/Feather';
import { Notification } from '@/src/types';
import { useTranslation } from 'react-i18next';

interface NotificationItemProps {
  notification: Notification;
  onPress: () => void;
}

export function NotificationItem({ notification, onPress }: NotificationItemProps) {
  const { colors, isDark } = useTheme();
  const { t } = useTranslation();
  let iconName: React.ComponentProps<typeof Feather>['name'] = 'bell';
  let iconBg = 'bg-[#F3E8FF]';
  let iconColor = colors.primary;
  let titleColor = isDark ? '#FFFFFF' : colors.text;

  const isLocalReminder = String(notification.id).startsWith('reminder_local_');

  const titleLower = notification.title.toLowerCase();
  if (titleLower.includes('cancelada') || titleLower.includes('cancelled')) {
    iconName = 'x-circle';
    iconBg = 'bg-[#FFEAEA]';
    iconColor = colors.danger;
    titleColor = colors.danger;
  } else if (notification.type === 'reminder' || titleLower.includes('recordatorio') || titleLower.includes('reminder')) {
    iconName = 'calendar';
    iconBg = 'bg-[#F3E8FF]';
  } else if (titleLower.includes('asignada') || titleLower.includes('assigned') || titleLower.includes('nueva tutoría')) {
    iconName = 'bell';
    iconBg = 'bg-[#F3E8FF]';
  }

  const formatRelativeTime = (dateStr: string) => {
    try {
      const created = new Date(dateStr);
      const now = new Date();
      const diffMs = now.getTime() - created.getTime();
      
      if (diffMs < 0) {
        return t('notifications.justNow');
      }
      
      const diffMins = Math.floor(diffMs / (60 * 1000));
      const diffHours = Math.floor(diffMs / (60 * 60 * 1000));
      const diffDays = Math.floor(diffMs / (24 * 60 * 60 * 1000));

      if (diffMins < 1) {
        return t('notifications.justNow');
      } else if (diffMins < 60) {
        return t('notifications.minutesAgo', { count: diffMins });
      } else if (diffHours < 24) {
        return t('notifications.hoursAgo', { count: diffHours });
      } else {
        return t('notifications.daysAgo', { count: diffDays });
      }
    } catch {
      return t('notifications.recently');
    }
  };

  const subtitleText = isLocalReminder ? notification.body : formatRelativeTime(notification.created_at);

  return (
    <Pressable
      onPress={onPress}
      style={{ backgroundColor: colors.surface }} className=" border border-border rounded-3xl p-4 mb-3 shadow-sm flex-row items-center"
    >
      <View className={`w-12 h-12 rounded-[20px] items-center justify-center mr-4 ${iconBg}`}>
        <Feather name={iconName} size={20} color={iconColor} />
      </View>

      <View className="flex-1">
        <Text className="text-sm font-bold" style={{ color: titleColor }}>{notification.title}</Text>
        <Text className="text-xs text-textSecondary mt-1 font-medium">
          {subtitleText}
        </Text>
      </View>

      {!notification.is_read ? (
        <View className="w-2.5 h-2.5 rounded-full bg-primary ml-2" />
      ) : null}
    </Pressable>
  );
}
