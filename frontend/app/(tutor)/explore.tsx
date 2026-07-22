import React from 'react';
import { View, Text, ScrollView, Pressable } from 'react-native';
import { useRouter } from 'expo-router';
import { Feather } from '@expo/vector-icons';
import { useTheme } from '@/src/theme/ThemeContext';
import { useTranslation } from 'react-i18next';

export default function TutorExploreScreen() {
  const { colors, isDark } = useTheme();
  const { t } = useTranslation();
  const router = useRouter();

  const services = [
    {
      id: 'chat',
      title: t('explore.openChat'),
      description: t('explore.tutorDescription'),
      icon: 'message-square' as const,
      route: '/(tutor)/tutoria',
      color: '#9A3BEE',
      bgColor: '#F3E8FF',
    },
    {
      id: 'calendar',
      title: t('explore.openCalendar'),
      description: t('calendar.emptyScheduledHint'),
      icon: 'calendar' as const,
      route: '/(tutor)/calendar',
      color: '#3B82F6',
      bgColor: '#DBEAFE',
    },
    {
      id: 'profile',
      title: t('explore.openProfile'),
      description: t('explore.profileDescription'),
      icon: 'user' as const,
      route: '/(tutor)/profile',
      color: '#10B981',
      bgColor: '#D1FAE5',
    },
  ];

  return (
    <ScrollView
      style={{ flex: 1, backgroundColor: colors.background }}
      contentContainerStyle={{ paddingHorizontal: 24, paddingTop: 64, paddingBottom: 120 }}
      showsVerticalScrollIndicator={false}
    >
      <View style={{ marginBottom: 24 }}>
        <Text style={{ fontSize: 24, fontWeight: 'bold', color: colors.text }}>
          {t('explore.title')}
        </Text>
        <Text style={{ fontSize: 14, color: colors.textSecondary, marginTop: 6, lineHeight: 20 }}>
          {t('explore.tutorDescription')}
        </Text>
      </View>

      {services.map((item) => (
        <Pressable
          key={item.id}
          onPress={() => router.push(item.route as any)}
          style={{
            backgroundColor: colors.surface,
            borderRadius: 24,
            padding: 20,
            marginBottom: 16,
            borderWidth: 1,
            borderColor: colors.border,
            shadowColor: '#000',
            shadowOffset: { width: 0, height: 2 },
            shadowOpacity: 0.04,
            shadowRadius: 8,
            elevation: 2,
            flexDirection: 'row',
            alignItems: 'center',
          }}
        >
          <View
            style={{
              width: 52,
              height: 52,
              borderRadius: 20,
              backgroundColor: isDark ? '#374151' : item.bgColor,
              alignItems: 'center',
              justifyContent: 'center',
              marginRight: 16,
            }}
          >
            <Feather name={item.icon} size={24} color={item.color} />
          </View>
          <View style={{ flex: 1 }}>
            <Text style={{ fontSize: 16, fontWeight: 'bold', color: colors.text, marginBottom: 4 }}>
              {item.title}
            </Text>
            <Text style={{ fontSize: 12, color: colors.textSecondary, lineHeight: 16 }} numberOfLines={2}>
              {item.description}
            </Text>
          </View>
          <Feather name="chevron-right" size={20} color={colors.textSecondary} style={{ marginLeft: 8 }} />
        </Pressable>
      ))}
    </ScrollView>
  );
}
