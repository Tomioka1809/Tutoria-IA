import React from 'react';
import { useTheme } from '@/src/theme/ThemeContext';
import { View, Text, Pressable } from 'react-native';
import { useRouter } from 'expo-router';
import { useTranslation } from 'react-i18next';

export function NotificationsHeader() {
  const { colors } = useTheme();
  const { t } = useTranslation();
  const router = useRouter();

  return (
    <View className="px-6 mb-6 flex-row items-center justify-between">
      <View className="flex-row items-center">
        <Pressable onPress={() => router.back()} className="mr-3 p-1">
          <Text className="text-xl text-text">←</Text>
        </Pressable>
        <Text style={{ color: colors.text }} className="text-[20px] font-bold ">
          {t('notifications.title')}
        </Text>
      </View>
    </View>
  );
}
