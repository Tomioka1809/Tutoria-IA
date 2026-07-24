// app/(tutor)/perfil-tutor.tsx
import React from 'react';
import { View, Text, ScrollView, Pressable, Image, Platform } from 'react-native';
import { useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Feather from '@expo/vector-icons/Feather';
import { useAuthStore } from '@/src/store/auth';
import { useTheme } from '@/src/theme/ThemeContext';
import { useTranslation } from 'react-i18next';

const PURPLE = '#9A3BEE';
const PURPLE_LIGHT = '#F3E8FF';

export default function PerfilTutorScreen() {
  const { colors } = useTheme();
  const { t } = useTranslation();
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const paddingTop = Math.max(insets.top, 16);
  const minimumBottomPadding = Platform.OS === 'ios' ? 24 : 12;
  const bottomPadding = Math.max(insets.bottom, minimumBottomPadding);
  const tabBarBaseHeight = 62;
  const totalTabBarHeight = tabBarBaseHeight + bottomPadding;
  const scrollBottomPadding = totalTabBarHeight + 24;

  const { user, profileImage } = useAuthStore();

  const handleBack = () => {
    if (router.canGoBack()) {
      router.back();
      return;
    }
    router.replace('/(tutor)/profile' as any);
  };

  const infoRows = [
    {
      iconName: 'mail' as const,
      label: t('tutorProfile.institutionalEmail'),
      value: user?.email || t('common.notSpecified'),
    },
    {
      iconName: 'award' as const,
      label: t('profile.codeLabel'),
      value: user?.tutor_code || t('common.notSpecified'),
    },
    {
      iconName: 'phone' as const,
      label: t('tutorProfile.phone'),
      value: user?.phone_number || t('common.notSpecified'),
    },
    {
      iconName: 'star' as const,
      label: t('tutorProfile.expertise'),
      value: user?.expertise_areas || t('common.notSpecified'),
    },
    {
      iconName: 'map-pin' as const,
      label: t('tutorProfile.office'),
      value: user?.office_location || t('common.notSpecified'),
    },
  ];

  return (
    <ScrollView
      style={{ flex: 1, backgroundColor: colors.background }}
      contentContainerStyle={{ paddingBottom: scrollBottomPadding }}
      showsVerticalScrollIndicator={false}
    >
      {/* ─── Encabezado morado ─────────────────────────────── */}
      <View
        style={{
          backgroundColor: PURPLE,
          paddingTop: paddingTop + 16,
          paddingBottom: 56,
          paddingHorizontal: 24,
          borderBottomLeftRadius: 0,
          borderBottomRightRadius: 0,
        }}
      >
        <View style={{ flexDirection: 'row', alignItems: 'center' }}>
          <Pressable
            onPress={handleBack}
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

      {/* ─── Tarjeta principal del tutor ───────────────────── */}
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
          {profileImage ? (
            <Image
              source={{ uri: profileImage }}
              style={{
                width: 72,
                height: 72,
                borderRadius: 36,
                backgroundColor: '#D8B4FE',
                marginRight: 16,
              }}
              resizeMode="cover"
            />
          ) : (
            <View
              style={{
                width: 72,
                height: 72,
                borderRadius: 36,
                backgroundColor: '#D8B4FE',
                marginRight: 16,
              }}
            />
          )}
          
          <View style={{ flex: 1 }}>
            <Text style={{ fontSize: 18, fontWeight: 'bold', color: colors.text }}>
              {user?.full_name || t('tutorProfile.nameNotSpecified')}
            </Text>
            <Text style={{ fontSize: 13, color: '#8E8EA0', marginTop: 4, fontWeight: '500' }}>
              {t('tutorProfile.teacherTutor')}
            </Text>
          </View>
        </View>
      </View>

      {/* ─── Tarjeta de información ────────────────────────── */}
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
              {/* Fila de información */}
              <View
                style={{
                  flexDirection: 'row',
                  alignItems: 'flex-start',
                  paddingHorizontal: 16,
                  paddingVertical: 16,
                }}
              >
                {/* Ícono en recuadro morado claro */}
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
                {/* Textos */}
                <View style={{ flex: 1 }}>
                  <Text style={{ fontSize: 14, fontWeight: '700', color: colors.text, marginBottom: 3 }}>
                    {row.label}
                  </Text>
                  <Text style={{ fontSize: 13, color: '#8E8EA0', lineHeight: 18 }}>
                    {row.value}
                  </Text>
                </View>
              </View>
              {/* Divisor entre filas */}
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
    </ScrollView>
  );
}
