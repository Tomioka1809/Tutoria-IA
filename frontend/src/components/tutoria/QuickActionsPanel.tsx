// src/components/tutoria/QuickActionsPanel.tsx
import React from 'react';
import { useTheme } from '@/src/theme/ThemeContext';
import { useTranslation } from 'react-i18next';
import { View, Pressable, Text, ScrollView } from 'react-native';

interface QuickActionsPanelProps {
  onActionPress: (actionText: string) => void;
  userRole?: string;
}

export function QuickActionsPanel({ onActionPress, userRole }: QuickActionsPanelProps) {
  const { colors } = useTheme();
  const { t } = useTranslation();
  const isTutor = userRole === 'tutor';

  return (
    <View style={{ backgroundColor: colors.background }} className="py-2.5 border-t border-border">
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={{ paddingHorizontal: 16 }}
      >
        {isTutor ? (
          <>
            <Pressable
              onPress={() => onActionPress(t('tutoring.myStudentsPrompt'))}
              style={{ backgroundColor: colors.surface }} className=" border border-border rounded-2xl px-4 py-2 mr-2 flex-row items-center shadow-sm"
            >
              <Text className="text-xs font-semibold" style={{ color: colors.text }}>👥 {t('tutoring.myStudents')}</Text>
            </Pressable>
            <Pressable
              onPress={() => onActionPress(t('tutoring.mySessionsPrompt'))}
              style={{ backgroundColor: colors.surface }} className=" border border-border rounded-2xl px-4 py-2 mr-2 flex-row items-center shadow-sm"
            >
              <Text className="text-xs font-semibold" style={{ color: colors.text }}>📅 {t('tutoring.mySessions')}</Text>
            </Pressable>
          </>
        ) : (
          <>
            <Pressable
              onPress={() => onActionPress(t('tutoring.curriculumPrompt'))}
              style={{ backgroundColor: colors.surface }} className=" border border-border rounded-2xl px-4 py-2 mr-2 flex-row items-center shadow-sm"
            >
              <Text className="text-xs font-semibold" style={{ color: colors.text }}>📄 {t('tutoring.curriculum')}</Text>
            </Pressable>
            <Pressable
              onPress={() => onActionPress(t('tutoring.sessionsPrompt'))}
              style={{ backgroundColor: colors.surface }} className=" border border-border rounded-2xl px-4 py-2 mr-2 flex-row items-center shadow-sm"
            >
              <Text className="text-xs font-semibold" style={{ color: colors.text }}>📅 {t('tutoring.sessions')}</Text>
            </Pressable>
          </>
        )}
        <Pressable
          onPress={() => onActionPress(t('tutoring.regulationsPrompt'))}
          style={{ backgroundColor: colors.surface }} className=" border border-border rounded-2xl px-4 py-2 flex-row items-center shadow-sm"
        >
          <Text className="text-xs font-semibold" style={{ color: colors.text }}>📄 {t('tutoring.regulations')}</Text>
        </Pressable>
      </ScrollView>
    </View>
  );
}
