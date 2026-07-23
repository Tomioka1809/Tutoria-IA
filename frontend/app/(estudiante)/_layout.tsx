// app/(estudiante)/_layout.tsx
import { Tabs, usePathname } from 'expo-router';
import React from 'react';
import { Platform, Text } from 'react-native';

import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { HapticTab } from '@/components/haptic-tab';
import { IconSymbol } from '@/components/ui/icon-symbol';
import { TutoriaTabBarButton } from '@/src/components/tutoria/TutoriaTabBarButton';
import { useTranslation } from 'react-i18next';
import { useTheme } from '@/src/theme/ThemeContext';

export default function TabLayout() {
  const pathname = usePathname();
  const { t } = useTranslation();
  const { colors } = useTheme();
  const insets = useSafeAreaInsets();

  const minimumBottomPadding = Platform.OS === 'ios' ? 24 : 12;
  const bottomPadding = Math.max(insets.bottom, minimumBottomPadding);
  const tabBarBaseHeight = 62;

  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: colors.primary,
        tabBarInactiveTintColor: colors.textSecondary,
        headerShown: false,
        tabBarButton: HapticTab,
        tabBarHideOnKeyboard: true,
        tabBarLabelStyle: {
          fontSize: 10,
          fontWeight: '600',
          marginTop: 2,
        },
        tabBarStyle: {
          borderTopWidth: 1,
          borderTopColor: colors.border,
          height: tabBarBaseHeight + bottomPadding,
          paddingBottom: bottomPadding,
          paddingTop: 8,
          backgroundColor: colors.surface,
          position: 'absolute',
          bottom: 0,
          left: 0,
          right: 0,
        }
      }}>
      <Tabs.Screen
        name="index"
        options={{
          title: t('tabs.home') || 'Inicio',
          tabBarIcon: ({ color }) => <IconSymbol size={26} name="house.fill" color={color} />,
        }}
      />
      <Tabs.Screen
        name="calendar"
        options={{
          title: t('tabs.calendar') || 'Calendario',
          tabBarIcon: ({ color }) => <IconSymbol size={26} name="calendar" color={color} />,
        }}
      />
      <Tabs.Screen
        name="tutoria"
        options={{
          title: 'TutorIA',
          tabBarIcon: ({ color }) => <IconSymbol size={26} name="message.fill" color={color} />,
          tabBarButton: (props) => <TutoriaTabBarButton {...props} />,
        }}
      />
      <Tabs.Screen
        name="notifications"
        options={{
          title: t('tabs.notifications') || 'Notificaciones',
          tabBarIcon: ({ color }) => <IconSymbol size={26} name="bell.fill" color={color} />,
        }}
      />
      <Tabs.Screen
        name="profile"
        options={{
          title: t('tabs.profile') || 'Perfil',
          tabBarIcon: ({ color, focused }) => {
            const isActive = focused || pathname === '/configuracion' || pathname === '/privacidad' || pathname === '/centro-ayuda' || pathname === '/perfil-tutor' || pathname === '/editar-perfil';
            return <IconSymbol size={26} name="person.fill" color={isActive ? colors.primary : colors.textSecondary} />;
          },
          tabBarLabel: ({ focused }) => {
            const isActive = focused || pathname === '/configuracion' || pathname === '/privacidad' || pathname === '/centro-ayuda' || pathname === '/perfil-tutor' || pathname === '/editar-perfil';
            return (
              <Text style={{
                fontSize: 10,
                fontWeight: '600',
                marginTop: 2,
                color: isActive ? colors.primary : colors.textSecondary,
              }}>
                {t('tabs.profile') || 'Perfil'}
              </Text>
            );
          }
        }}
      />
      
      {/* Hidden Screens */}
      <Tabs.Screen name="configuracion" options={{ href: null }} />
      <Tabs.Screen name="privacidad" options={{ href: null }} />
      <Tabs.Screen name="centro-ayuda" options={{ href: null }} />
      <Tabs.Screen name="perfil-tutor" options={{ href: null }} />
      <Tabs.Screen name="editar-perfil" options={{ href: null }} />
      <Tabs.Screen name="explore" options={{ href: null }} />
      <Tabs.Screen 
        name="retroalimentacion-quiz" 
        options={{ 
          href: null,
          tabBarStyle: { display: 'none' }
        }} 
      />
    </Tabs>
  );
}
