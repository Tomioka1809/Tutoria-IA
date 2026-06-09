// app/(tabs)/_layout.tsx
import { Tabs } from 'expo-router';
import React from 'react';
import { Platform } from 'react-native';

import { HapticTab } from '@/components/haptic-tab';
import { IconSymbol } from '@/components/ui/icon-symbol';
import { Colors } from '@/constants/theme';
import { useColorScheme } from '@/hooks/use-color-scheme';
import { TutoriaTabBarButton } from '@/src/components/tutoria/TutoriaTabBarButton';

export default function TabLayout() {
  const colorScheme = useColorScheme();

  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: '#9A3BEE',
        tabBarInactiveTintColor: '#8E8EA0',
        headerShown: false,
        tabBarButton: HapticTab,
        tabBarStyle: {
          borderTopWidth: 1,
          borderTopColor: '#EEEDFE',
          height: Platform.OS === 'ios' ? 88 : 70,
          paddingBottom: Platform.OS === 'ios' ? 24 : 12,
          paddingTop: 8,
          backgroundColor: 'white',
          position: 'absolute',
          bottom: 0,
          left: 0,
          right: 0,
        }
      }}>
      <Tabs.Screen
        name="index"
        options={{
          title: 'Inicio',
          tabBarIcon: ({ color }) => <IconSymbol size={26} name="house.fill" color={color} />,
        }}
      />
      <Tabs.Screen
        name="calendar"
        options={{
          title: 'Calendario',
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
          title: 'Notificaciones',
          tabBarIcon: ({ color }) => <IconSymbol size={26} name="bell.fill" color={color} />,
        }}
      />
      <Tabs.Screen
        name="profile"
        options={{
          title: 'Perfil',
          tabBarIcon: ({ color }) => <IconSymbol size={26} name="person.fill" color={color} />,
        }}
      />
      
      {/* Hide the old default templates */}
      <Tabs.Screen
        name="explore"
        options={{
          href: null,
        }}
      />
    </Tabs>
  );
}
