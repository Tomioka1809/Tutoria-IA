import React from 'react';
import { useTheme } from '@/src/theme/ThemeContext';
import { View, Text } from 'react-native';
import { useTranslation } from 'react-i18next';

export function NotificationsHeader() {
  const { colors } = useTheme();
  const { t } = useTranslation();

  return (
    <View className="px-6 mb-6 flex-row items-center justify-between">
      <View className="flex-row items-center">
        <Text style={{ color: colors.text }} className="text-[20px] font-bold ">
          {t('notifications.title')}
        </Text>
      </View>
    </View>
  );
}
