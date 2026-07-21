// src/components/profile/AssignedTutorCard.tsx
import React from 'react';
import { View, Text, Pressable } from 'react-native';
import { useRouter } from 'expo-router';
import { TutorAssignment } from '@/src/types';
import { useAuthStore } from '@/src/store/auth';
import { useTheme } from '@/src/theme/ThemeContext';
import { useTranslation } from 'react-i18next';

interface AssignedTutorCardProps {
  assignedTutors: TutorAssignment[];
}

export function AssignedTutorCard({ assignedTutors }: AssignedTutorCardProps) {
  const { colors } = useTheme();
  const { t } = useTranslation();
  const router = useRouter();
  const user = useAuthStore((state) => state.user);
  const routePrefix = user?.role === 'tutor' ? '/(tutor)' : user?.role === 'admin' ? '/(admin)' : '/(estudiante)';
  
  const tutorName = assignedTutors.length > 0 && assignedTutors[0]?.tutor 
    ? assignedTutors[0].tutor.full_name 
    : 'Ing. Ana Torres';

  const tutorEmail = assignedTutors.length > 0 && assignedTutors[0]?.tutor 
    ? assignedTutors[0].tutor.email 
    : 'ana.torres@universidad.edu';

  return (
    <View style={{
      paddingHorizontal: 24,
      marginTop: -32,
      marginBottom: 24,
    }}>
      <View style={{
        backgroundColor: colors.surface,
        borderRadius: 24,
        padding: 16,
        borderWidth: 1,
        borderColor: colors.border,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.05,
        shadowRadius: 8,
        elevation: 3,
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
      }}>
        <View style={{ flexDirection: 'row', alignItems: 'center', flex: 1 }}>
          {/* Light purple circle avatar */}
          <View style={{
            width: 48,
            height: 48,
            borderRadius: 24,
            backgroundColor: '#D8B4FE',
            marginRight: 12,
          }} />
          <View style={{ flex: 1 }}>
            <Text style={{ fontSize: 15, fontWeight: 'bold', color: colors.text }}>
              {tutorName}
            </Text>
            <Text style={{ fontSize: 12, color: colors.textSecondary, marginTop: 2, fontWeight: '500' }}>
              {t('profile.tutorTeacher')}
            </Text>
          </View>
        </View>

        <Pressable onPress={() => router.push(`${routePrefix}/perfil-tutor` as any)}>
          <Text style={{ fontSize: 13, fontWeight: 'bold', color: colors.primary }}>
            {t('profile.viewProfile')}
          </Text>
        </Pressable>
      </View>
    </View>
  );
}
