// src/components/profile/ProfileMenu.tsx
import React from 'react';
import { View, Text, Pressable } from 'react-native';
import { useRouter } from 'expo-router';
import Feather from '@expo/vector-icons/Feather';

interface ProfileMenuProps {
  onLogout: () => void;
}

export function ProfileMenu({ onLogout }: ProfileMenuProps) {
  const router = useRouter();
  const menuItems = [
    {
      name: 'Configuración',
      icon: 'settings' as const,
      action: () => router.push('/(tabs)/configuracion' as any),
      isDestructive: false,
    },
    {
      name: 'Privacidad',
      icon: 'lock' as const,
      action: () => router.push('/(tabs)/privacidad' as any),
      isDestructive: false,
    },
    {
      name: 'Centro de ayuda',
      icon: 'help-circle' as const,
      action: () => alert('Centro de ayuda en desarrollo.'),
      isDestructive: false,
    },
    {
      name: 'Cerrar sesión',
      icon: 'log-out' as const,
      action: onLogout,
      isDestructive: true,
    },
  ];

  return (
    <View style={{ paddingHorizontal: 24 }}>
      {menuItems.map((item, index) => {
        const iconBgColor = item.isDestructive ? '#FEE2E2' : '#F1F5F9';
        const iconColor = item.isDestructive ? '#EF4444' : '#4B5563';
        const textColor = item.isDestructive ? '#EF4444' : '#1E1E2F';
        const arrowColor = item.isDestructive ? '#EF4444' : '#94A3B8';

        return (
          <Pressable
            key={index}
            onPress={item.action}
            style={{
              backgroundColor: 'white',
              borderRadius: 20,
              paddingVertical: 14,
              paddingHorizontal: 16,
              marginBottom: 12,
              borderWidth: 1,
              borderColor: '#EEEDFE',
              shadowColor: '#000',
              shadowOffset: { width: 0, height: 2 },
              shadowOpacity: 0.04,
              shadowRadius: 6,
              elevation: 2,
              flexDirection: 'row',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <View style={{ flexDirection: 'row', alignItems: 'center' }}>
              <View style={{
                width: 40,
                height: 40,
                borderRadius: 20,
                backgroundColor: iconBgColor,
                alignItems: 'center',
                justifyContent: 'center',
                marginRight: 16,
              }}>
                <Feather name={item.icon} size={20} color={iconColor} />
              </View>
              <Text style={{
                fontSize: 15,
                fontWeight: '600',
                color: textColor,
              }}>
                {item.name}
              </Text>
            </View>
            <Feather name="chevron-right" size={20} color={arrowColor} />
          </Pressable>
        );
      })}
    </View>
  );
}
