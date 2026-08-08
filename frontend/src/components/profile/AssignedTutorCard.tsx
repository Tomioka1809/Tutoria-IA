import React from 'react';
import { View, Text, Pressable } from 'react-native';
import { useRouter } from 'expo-router';
import { Feather } from '@expo/vector-icons';
import { TutorAssignment } from '@/src/types';
import { useTheme } from '@/src/theme/ThemeContext';
import { useTranslation } from 'react-i18next';
import { resolveAssignedTutor } from './assigned-tutor-view-model';

interface AssignedTutorCardProps {
  assignedTutors: TutorAssignment[];
  isLoading?: boolean;
  hasLoadError?: boolean;
}

export function AssignedTutorCard({
  assignedTutors,
  isLoading = false,
  hasLoadError = false,
}: AssignedTutorCardProps) {
  const { colors, isDark } = useTheme();
  const { t } = useTranslation();
  const router = useRouter();

  const resolution = resolveAssignedTutor(assignedTutors);

  if (isLoading) {
    return (
      <View style={{ paddingHorizontal: 24, marginTop: -32, marginBottom: 24 }}>
        <View
          style={{
            backgroundColor: colors.surface,
            borderRadius: 24,
            padding: 16,
            borderWidth: 1,
            borderColor: colors.border,
            flexDirection: 'row',
            alignItems: 'center',
          }}
        >
          <View
            style={{
              width: 48,
              height: 48,
              borderRadius: 24,
              backgroundColor: isDark ? '#374151' : '#F3E8FF',
              marginRight: 12,
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Feather name="clock" size={22} color={colors.primary} />
          </View>
          <View style={{ flex: 1 }}>
            <Text style={{ fontSize: 15, fontWeight: 'bold', color: colors.text }}>
              {t('common.loading')}
            </Text>
          </View>
        </View>
      </View>
    );
  }

  if (hasLoadError) {
    return (
      <View style={{ paddingHorizontal: 24, marginTop: -32, marginBottom: 24 }}>
        <View
          style={{
            backgroundColor: colors.surface,
            borderRadius: 24,
            padding: 16,
            borderWidth: 1,
            borderColor: colors.border,
            flexDirection: 'row',
            alignItems: 'center',
          }}
        >
          <View
            style={{
              width: 48,
              height: 48,
              borderRadius: 24,
              backgroundColor: isDark ? '#374151' : '#FFEAEA',
              marginRight: 12,
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Feather name="alert-circle" size={22} color={colors.danger} />
          </View>
          <View style={{ flex: 1 }}>
            <Text style={{ fontSize: 15, fontWeight: 'bold', color: colors.text }}>
              {t('profile.tutorUnavailable')}
            </Text>
            <Text style={{ fontSize: 12, color: colors.textSecondary, marginTop: 2, fontWeight: '500' }}>
              {t('errors.loadAssignedTutor')}
            </Text>
          </View>
        </View>
      </View>
    );
  }

  if (resolution.status === 'none') {
    return (
      <View style={{ paddingHorizontal: 24, marginTop: -32, marginBottom: 24 }}>
        <View
          style={{
            backgroundColor: colors.surface,
            borderRadius: 24,
            padding: 16,
            borderWidth: 1,
            borderColor: colors.border,
            flexDirection: 'row',
            alignItems: 'center',
          }}
        >
          <View
            style={{
              width: 48,
              height: 48,
              borderRadius: 24,
              backgroundColor: isDark ? '#374151' : '#F3E8FF',
              marginRight: 12,
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Feather name="user-x" size={22} color={colors.primary} />
          </View>
          <View style={{ flex: 1 }}>
            <Text style={{ fontSize: 15, fontWeight: 'bold', color: colors.text }}>
              {t('profile.noAssignedTutor')}
            </Text>
            <Text style={{ fontSize: 12, color: colors.textSecondary, marginTop: 2, fontWeight: '500' }}>
              {t('profile.noAssignedTutorDescription')}
            </Text>
          </View>
        </View>
      </View>
    );
  }

  if (resolution.status === 'ambiguous') {
    return (
      <View style={{ paddingHorizontal: 24, marginTop: -32, marginBottom: 24 }}>
        <View
          style={{
            backgroundColor: colors.surface,
            borderRadius: 24,
            padding: 16,
            borderWidth: 1,
            borderColor: colors.border,
            flexDirection: 'row',
            alignItems: 'center',
          }}
        >
          <View
            style={{
              width: 48,
              height: 48,
              borderRadius: 24,
              backgroundColor: isDark ? '#374151' : '#FEF3C7',
              marginRight: 12,
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Feather name="users" size={22} color="#D97706" />
          </View>
          <View style={{ flex: 1 }}>
            <Text style={{ fontSize: 15, fontWeight: 'bold', color: colors.text }}>
              {t('profile.tutorAssignmentAmbiguous')}
            </Text>
            <Text style={{ fontSize: 12, color: colors.textSecondary, marginTop: 2, fontWeight: '500' }}>
              {t('profile.tutorAssignmentAmbiguousDescription')}
            </Text>
          </View>
        </View>
      </View>
    );
  }

  const realTutor = resolution.tutor!;

  return (
    <View style={{ paddingHorizontal: 24, marginTop: -32, marginBottom: 24 }}>
      <View
        style={{
          backgroundColor: colors.surface,
          borderRadius: 24,
          padding: 16,
          borderWidth: 1,
          borderColor: colors.border,
          flexDirection: 'row',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <View style={{ flexDirection: 'row', alignItems: 'center', flex: 1 }}>
          <View
            style={{
              width: 48,
              height: 48,
              borderRadius: 24,
              backgroundColor: '#D8B4FE',
              marginRight: 12,
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Feather name="user-check" size={22} color="#6B21A8" />
          </View>
          <View style={{ flex: 1 }}>
            <Text style={{ fontSize: 15, fontWeight: 'bold', color: colors.text }}>
              {realTutor.full_name}
            </Text>
            <Text style={{ fontSize: 12, color: colors.textSecondary, marginTop: 2, fontWeight: '500' }}>
              {t('profile.tutorTeacher')}
            </Text>
          </View>
        </View>

        <Pressable onPress={() => router.push('/(estudiante)/perfil-tutor' as any)}>
          <Text style={{ fontSize: 13, fontWeight: 'bold', color: colors.primary }}>
            {t('profile.viewProfile')}
          </Text>
        </Pressable>
      </View>
    </View>
  );
}
