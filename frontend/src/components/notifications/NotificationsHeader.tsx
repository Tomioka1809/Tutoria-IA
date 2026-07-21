import React from 'react';
import { useTheme } from '@/src/theme/ThemeContext';
import { View, Text, Pressable } from 'react-native';
import { useRouter } from 'expo-router';
import { useTranslation } from 'react-i18next';

export function NotificationsHeader() {
  const { colors, isDark } = useTheme();
  const { t } = useTranslation();
  const router = useRouter();

  return (
    <View className="px-6 mb-6 flex-row items-center justify-between">
      <View className="flex-row items-center">
        <Pressable onPress={() => router.back()} className="mr-3 p-1">
          <Text className="text-xl text-text">←</Text>
        </Pressable>
        <Text style={{ color: colors.text }} className="text-[20px] font-bold ">{t('notifications.title')}</Text>
      </View>
      
      {/* Filter selection mock dropdown */}
      <Pressable style={{ backgroundColor: colors.surface }} className=" border border-primary rounded-xl px-4 py-1.5 flex-row items-center shadow-sm">
        <Text className="text-xs font-semibold mr-1.5" style={{ color: isDark ? '#FFFFFF' : colors.primary }}>{t('notifications.all')}</Text>
        <Text className="text-xs" style={{ color: isDark ? '#FFFFFF' : colors.primary }}>∨</Text>
      </Pressable>
    </View>
  );
}
