// src/components/tutoria/QuickActionsPanel.tsx
import React from 'react';
import { useTheme } from '@/src/theme/ThemeContext';
import { useTranslation } from 'react-i18next';
import { View, Pressable, Text, ScrollView } from 'react-native';
import Feather from '@expo/vector-icons/Feather';

interface QuickActionsPanelProps {
  onActionPress: (actionText: string) => void;
  userRole?: string;
}

interface QuickActionProps {
  icon: React.ComponentProps<typeof Feather>['name'];
  label: string;
  onPress: () => void;
  isLast?: boolean;
}

function QuickAction({ icon, label, onPress, isLast }: QuickActionProps) {
  const { colors } = useTheme();

  return (
    <Pressable
      onPress={onPress}
      style={{ backgroundColor: colors.surface }}
      className={`border border-border rounded-2xl px-4 py-2 flex-row items-center shadow-sm active:opacity-70${
        isLast ? '' : ' mr-2'
      }`}
    >
      <Feather name={icon} size={14} color={colors.primary} style={{ marginRight: 6 }} />
      <Text className="text-xs font-semibold" style={{ color: colors.text }}>
        {label}
      </Text>
    </Pressable>
  );
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
            <QuickAction
              icon="users"
              label={t('tutoring.myStudents')}
              onPress={() => onActionPress(t('tutoring.myStudentsPrompt'))}
            />
            <QuickAction
              icon="calendar"
              label={t('tutoring.mySessions')}
              onPress={() => onActionPress(t('tutoring.mySessionsPrompt'))}
            />
          </>
        ) : (
          <>
            <QuickAction
              icon="grid"
              label={t('tutoring.curriculum')}
              onPress={() => onActionPress(t('tutoring.curriculumPrompt'))}
            />
            <QuickAction
              icon="calendar"
              label={t('tutoring.sessions')}
              onPress={() => onActionPress(t('tutoring.sessionsPrompt'))}
            />
          </>
        )}
        <QuickAction
          icon="file-text"
          label={t('tutoring.regulations')}
          onPress={() => onActionPress(t('tutoring.regulationsPrompt'))}
          isLast
        />
      </ScrollView>
    </View>
  );
}
