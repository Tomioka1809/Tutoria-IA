import React from 'react';
import { View, Text, ScrollView, Pressable } from 'react-native';
import { useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Feather from '@expo/vector-icons/Feather';
import { useTheme } from '@/src/theme/ThemeContext';
import { useTranslation } from 'react-i18next';
import { useProfile } from '@/src/components/profile/useProfile';
import { resolveAssignedTutor } from '@/src/components/profile/assigned-tutor-view-model';

const PURPLE = '#9A3BEE';
const PURPLE_LIGHT = '#F3E8FF';

export default function PerfilTutorScreen() {
  const { colors, isDark } = useTheme();
  const { t } = useTranslation();
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const paddingTop = Math.max(insets.top, 16);
  
  const { assignedTutors, isLoading, assignedTutorLoadError } = useProfile();
  const resolution = resolveAssignedTutor(assignedTutors);

  const infoRows = [];
  if (resolution.status === 'available' && resolution.tutor) {
    if (resolution.tutor.email) {
      infoRows.push({
        iconName: 'mail' as const,
        label: t('tutorProfile.institutionalEmail'),
        value: resolution.tutor.email,
      });
    }
    if (resolution.tutor.expertise_areas) {
      infoRows.push({
        iconName: 'award' as const,
        label: t('tutorProfile.expertise'),
        value: resolution.tutor.expertise_areas,
      });
    }
  }

  let stateTitle = '';
  let stateDesc = '';
  let stateIcon: keyof typeof Feather.glyphMap = 'user-x';

  if (isLoading) {
    stateTitle = t('common.loading');
    stateDesc = '';
    stateIcon = 'clock';
  } else if (assignedTutorLoadError) {
    stateTitle = t('profile.tutorUnavailable');
    stateDesc = t('errors.loadAssignedTutor');
    stateIcon = 'alert-circle';
  } else if (resolution.status === 'none') {
    stateTitle = t('profile.noAssignedTutor');
    stateDesc = t('profile.noAssignedTutorDescription');
    stateIcon = 'user-x';
  } else if (resolution.status === 'ambiguous') {
    stateTitle = t('profile.tutorAssignmentAmbiguous');
    stateDesc = t('profile.tutorAssignmentAmbiguousDescription');
    stateIcon = 'users';
  }

  return (
    <ScrollView
      style={{ flex: 1, backgroundColor: colors.background }}
      contentContainerStyle={{ paddingBottom: 130 }}
      showsVerticalScrollIndicator={false}
    >
      <View
        style={{
          backgroundColor: PURPLE,
          paddingTop: paddingTop + 16,
          paddingBottom: 56,
          paddingHorizontal: 24,
        }}
      >
        <View style={{ flexDirection: 'row', alignItems: 'center' }}>
          <Pressable
            onPress={() => router.back()}
            style={{ marginRight: 16 }}
            hitSlop={{ top: 12, bottom: 12, left: 12, right: 12 }}
          >
            <Feather name="arrow-left" size={24} color="white" />
          </Pressable>
          <Text style={{ fontSize: 20, fontWeight: 'bold', color: 'white' }}>
            {t('tutorProfile.title')}
          </Text>
        </View>
      </View>

      {resolution.status !== 'available' || isLoading || assignedTutorLoadError ? (
        <View style={{ paddingHorizontal: 20, marginTop: -36 }}>
          <View
            style={{
              backgroundColor: colors.surface,
              borderRadius: 24,
              padding: 24,
              alignItems: 'center',
              justifyContent: 'center',
              shadowColor: '#000',
              shadowOffset: { width: 0, height: 4 },
              shadowOpacity: 0.08,
              shadowRadius: 12,
              elevation: 5,
              borderWidth: 1,
              borderColor: colors.border,
            }}
          >
            <View
              style={{
                width: 64,
                height: 64,
                borderRadius: 32,
                backgroundColor: isDark ? '#374151' : PURPLE_LIGHT,
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: 16,
              }}
            >
              <Feather name={stateIcon} size={32} color={PURPLE} />
            </View>
            <Text style={{ fontSize: 18, fontWeight: 'bold', color: colors.text, textAlign: 'center', marginBottom: 8 }}>
              {stateTitle}
            </Text>
            {stateDesc ? (
              <Text style={{ fontSize: 13, color: colors.textSecondary, textAlign: 'center', lineHeight: 18, maxWidth: 260 }}>
                {stateDesc}
              </Text>
            ) : null}
          </View>
        </View>
      ) : (
        <>
          <View style={{ paddingHorizontal: 20, marginTop: -36, marginBottom: 20 }}>
            <View
              style={{
                backgroundColor: colors.surface,
                borderRadius: 24,
                padding: 20,
                flexDirection: 'row',
                alignItems: 'center',
                shadowColor: '#000',
                shadowOffset: { width: 0, height: 4 },
                shadowOpacity: 0.08,
                shadowRadius: 12,
                elevation: 5,
              }}
            >
              <View
                style={{
                  width: 72,
                  height: 72,
                  borderRadius: 36,
                  backgroundColor: '#D8B4FE',
                  marginRight: 16,
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <Feather name="user" size={36} color="#6B21A8" />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={{ fontSize: 18, fontWeight: 'bold', color: colors.text }}>
                  {resolution.tutor!.full_name}
                </Text>
                <Text style={{ fontSize: 13, color: '#8E8EA0', marginTop: 4, fontWeight: '500' }}>
                  {t('profile.tutorTeacher')}
                </Text>
              </View>
            </View>
          </View>

          {infoRows.length > 0 && (
            <View style={{ paddingHorizontal: 20, marginBottom: 16 }}>
              <View
                style={{
                  backgroundColor: colors.surface,
                  borderRadius: 24,
                  borderWidth: 1,
                  borderColor: colors.border,
                  shadowColor: '#000',
                  shadowOffset: { width: 0, height: 2 },
                  shadowOpacity: 0.04,
                  shadowRadius: 6,
                  elevation: 2,
                  overflow: 'hidden',
                }}
              >
                {infoRows.map((row, index) => (
                  <View key={index}>
                    <View
                      style={{
                        flexDirection: 'row',
                        alignItems: 'flex-start',
                        paddingHorizontal: 16,
                        paddingVertical: 16,
                      }}
                    >
                      <View
                        style={{
                          width: 42,
                          height: 42,
                          borderRadius: 14,
                          backgroundColor: PURPLE_LIGHT,
                          alignItems: 'center',
                          justifyContent: 'center',
                          marginRight: 14,
                          flexShrink: 0,
                        }}
                      >
                        <Feather name={row.iconName} size={20} color={PURPLE} />
                      </View>
                      <View style={{ flex: 1 }}>
                        <Text style={{ fontSize: 14, fontWeight: '700', color: colors.text, marginBottom: 3 }}>
                          {row.label}
                        </Text>
                        <Text style={{ fontSize: 13, color: '#8E8EA0', lineHeight: 18 }}>
                          {row.value}
                        </Text>
                      </View>
                    </View>
                    {index < infoRows.length - 1 && (
                      <View
                        style={{
                          height: 1,
                          backgroundColor: colors.border,
                          marginLeft: 72,
                          marginRight: 16,
                        }}
                      />
                    )}
                  </View>
                ))}
              </View>
            </View>
          )}
        </>
      )}
    </ScrollView>
  );
}
