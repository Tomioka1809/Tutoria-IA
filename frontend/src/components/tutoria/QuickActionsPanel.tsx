// src/components/tutoria/QuickActionsPanel.tsx
import React from 'react';
import { useTheme } from '@/src/theme/ThemeContext';
import { View, Pressable, Text } from 'react-native';

interface QuickActionsPanelProps {
  onActionPress: (actionText: string) => void;
  userRole?: string;
}

export function QuickActionsPanel({ onActionPress, userRole }: QuickActionsPanelProps) {
  const { colors } = useTheme();
  const isTutor = userRole === 'tutor';

  return (
    <View style={{ backgroundColor: colors.background }} className="px-6 py-3  flex-row flex-wrap">
      {isTutor ? (
        <>
          <Pressable
            onPress={() => onActionPress('¿Cuáles son mis estudiantes asignados?')}
            style={{ backgroundColor: colors.surface }} className=" border border-border rounded-2xl px-4 py-2.5 mr-2 mb-2 flex-row items-center shadow-sm"
          >
            <Text className="text-xs font-semibold" style={{ color: colors.text }}>👥 Mis estudiantes</Text>
          </Pressable>
          <Pressable
            onPress={() => onActionPress('¿Qué tutorías tengo hoy?')}
            style={{ backgroundColor: colors.surface }} className=" border border-border rounded-2xl px-4 py-2.5 mr-2 mb-2 flex-row items-center shadow-sm"
          >
            <Text className="text-xs font-semibold" style={{ color: colors.text }}>📅 Mis tutorías</Text>
          </Pressable>
        </>
      ) : (
        <>
          <Pressable
            onPress={() => onActionPress('¿Cuál es mi plan de estudios actual?')}
            style={{ backgroundColor: colors.surface }} className=" border border-border rounded-2xl px-4 py-2.5 mr-2 mb-2 flex-row items-center shadow-sm"
          >
            <Text className="text-xs font-semibold" style={{ color: colors.text }}>📄 Plan de estudios</Text>
          </Pressable>
          <Pressable
            onPress={() => onActionPress('¿Cuándo es mi próxima tutoría?')}
            style={{ backgroundColor: colors.surface }} className=" border border-border rounded-2xl px-4 py-2.5 mr-2 mb-2 flex-row items-center shadow-sm"
          >
            <Text className="text-xs font-semibold" style={{ color: colors.text }}>📅 Tutorías</Text>
          </Pressable>
        </>
      )}
      <Pressable
        onPress={() => onActionPress('¿Cuáles son los reglamentos de tutoría y de intercambio estudiantil?')}
        style={{ backgroundColor: colors.surface }} className=" border border-border rounded-2xl px-4 py-2.5 mb-2 flex-row items-center shadow-sm"
      >
        <Text className="text-xs font-semibold" style={{ color: colors.text }}>📄 Reglamentos</Text>
      </Pressable>
    </View>
  );
}
