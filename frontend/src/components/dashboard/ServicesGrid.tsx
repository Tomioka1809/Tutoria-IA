// src/components/dashboard/ServicesGrid.tsx
import React from 'react';
import { useTheme } from '@/src/theme/ThemeContext';
import { View, Text, Pressable, Linking } from 'react-native';
import { useRouter } from 'expo-router';
import Feather from '@expo/vector-icons/Feather';
import MaterialCommunityIcons from '@expo/vector-icons/MaterialCommunityIcons';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTranslation } from 'react-i18next';

const services = [
  { nameKey: 'dashboard.academicTutoring', icon: 'book-open', iconType: 'Feather', bgColor: '#9C3FE4', url: 'https://www.unsaac.edu.pe/' },
  { nameKey: 'dashboard.personalTutoring', icon: 'heart', iconType: 'Feather', bgColor: '#3B82F6', url: 'https://www.unsaac.edu.pe/' },
  { nameKey: 'dashboard.professionalTutoring', icon: 'briefcase', iconType: 'Feather', bgColor: '#8B5CF6', url: 'https://www.unsaac.edu.pe/' },
  { nameKey: 'dashboard.psychologicalSupport', icon: 'brain', iconType: 'MaterialCommunityIcons', bgColor: '#EC4899', url: 'https://www.unsaac.edu.pe/' },
  { nameKey: 'dashboard.studentWelfare', icon: 'star', iconType: 'Feather', bgColor: '#06B6D4', url: 'https://www.unsaac.edu.pe/' },
  { nameKey: 'dashboard.internships', icon: 'rocket-outline', iconType: 'Ionicons', bgColor: '#F97316', url: 'https://www.unsaac.edu.pe/' },
  { nameKey: 'dashboard.studentMobility', icon: 'globe', iconType: 'Feather', bgColor: '#3B82F6', url: 'https://www.unsaac.edu.pe/' },
  { nameKey: 'dashboard.feedback', icon: 'message-square', iconType: 'Feather', bgColor: '#9333EA', url: null },
];

export function ServicesGrid() {
  const { colors } = useTheme();
  const { t } = useTranslation();
  const router = useRouter();

  const renderIcon = (type: string, name: string) => {
    const size = 22;
    const color = 'white';
    if (type === 'Feather') {
      return <Feather name={name as any} size={size} color={color} />;
    }
    if (type === 'MaterialCommunityIcons') {
      return <MaterialCommunityIcons name={name as any} size={size} color={color} />;
    }
    if (type === 'Ionicons') {
      return <Ionicons name={name as any} size={size} color={color} />;
    }
    return null;
  };

  const handlePress = (serv: any) => {
    if (serv.nameKey === 'dashboard.feedback') {
      router.push('/(estudiante)/retroalimentacion-quiz' as any);
    } else if (serv.url) {
      Linking.openURL(serv.url).catch((err) => {
        console.error("Failed to open URL:", err);
      });
    }
  };

  return (
    <View style={{ paddingHorizontal: 24, marginBottom: 24 }}>
      <View style={{
        marginBottom: 16,
      }}>
        <Text style={{ fontSize: 17, fontWeight: 'bold', color: colors.text }}>
          {t('dashboard.servicesTitle')}
        </Text>
      </View>

      <View style={{
        flexDirection: 'row',
        flexWrap: 'wrap',
        justifyContent: 'space-between',
      }}>
        {services.map((serv, index) => (
          <Pressable
            key={index}
            onPress={() => handlePress(serv)}
            style={{
              width: '23%',
              alignItems: 'center',
              marginBottom: 20,
            }}
          >
            <View
              style={{
                width: 56,
                height: 56,
                borderRadius: 16,
                backgroundColor: serv.bgColor,
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: 8,
                shadowColor: '#000',
                shadowOffset: { width: 0, height: 2 },
                shadowOpacity: 0.08,
                shadowRadius: 4,
                elevation: 2,
              }}
            >
              {renderIcon(serv.iconType, serv.icon)}
            </View>
            <Text 
              style={{
                fontSize: 10,
                fontWeight: '600',
                color: colors.textSecondary,
                textAlign: 'center',
                lineHeight: 13,
                width: '100%',
              }}
              numberOfLines={2}
            >
              {t(serv.nameKey)}
            </Text>
          </Pressable>
        ))}
      </View>
    </View>
  );
}
