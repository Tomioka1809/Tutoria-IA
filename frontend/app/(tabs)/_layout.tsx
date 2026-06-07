import { Tabs } from 'expo-router';
import React from 'react';
import { View, Pressable, Text, Platform } from 'react-native';

import { HapticTab } from '@/components/haptic-tab';
import { IconSymbol } from '@/components/ui/icon-symbol';
import { Colors } from '@/constants/theme';
import { useColorScheme } from '@/hooks/use-color-scheme';

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
          tabBarButton: ({ ref, ...restProps }) => (
            <Pressable
              {...restProps}
              style={{
                top: -18,
                justifyContent: 'center',
                alignItems: 'center',
                width: 70,
                height: 70,
              }}
            >
              <View
                style={{
                  width: 58,
                  height: 58,
                  borderRadius: 29,
                  backgroundColor: 'white',
                  borderWidth: 3,
                  borderColor: '#9A3BEE',
                  justifyContent: 'center',
                  alignItems: 'center',
                  ...Platform.select({
                    ios: {
                      shadowColor: '#9A3BEE',
                      shadowOffset: { width: 0, height: 4 },
                      shadowOpacity: 0.3,
                      shadowRadius: 5,
                    },
                    android: {
                      elevation: 6,
                    },
                  }),
                }}
              >
                <Text style={{ fontSize: 30 }}>🦖</Text>
              </View>
            </Pressable>
          ),
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
