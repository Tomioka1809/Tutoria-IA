// src/components/tutoria/TutoriaHeader.tsx
import React from 'react';
import { useTheme } from '@/src/theme/ThemeContext';
import { useTranslation } from 'react-i18next';
import { View, Text, Pressable } from 'react-native';
import Feather from '@expo/vector-icons/Feather';
import { TutorIAAvatar } from '@/src/components/tutoria/TutorIAAvatar';

interface TutoriaHeaderProps {
  onRefresh: () => void;
  onBackPress?: () => void;
}

export function TutoriaHeader({ onRefresh }: TutoriaHeaderProps) {
  const { colors } = useTheme();
  const { t } = useTranslation();
  return (
    <View style={{ backgroundColor: colors.surface }} className=" border-b border-border px-6 pt-16 pb-4 flex-row items-center justify-between">
      <View className="flex-row items-center flex-1">
        <View className="w-10 h-10 rounded-full bg-primary/10 items-center justify-center border border-primary/25 mr-3">
          <TutorIAAvatar size={36} />
        </View>

        <View className="flex-1">
          <Text style={{ color: colors.text }} className="text-sm font-extrabold ">TutorIA AI</Text>
          <View className="flex-row items-center mt-0.5">
            <View className="w-2 h-2 rounded-full bg-[#10B981] mr-1.5" />
            <Text className="text-[10px] text-textSecondary font-semibold">{t('tutoring.online')}</Text>
          </View>
        </View>
      </View>

      <Pressable
        onPress={onRefresh}
        hitSlop={8}
        accessibilityRole="button"
        accessibilityLabel={t('tutoring.restartConversation')}
        className="p-2 active:opacity-60"
      >
        <Feather name="refresh-cw" size={18} color={colors.text} />
      </Pressable>
    </View>
  );
}
