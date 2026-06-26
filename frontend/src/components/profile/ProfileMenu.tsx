// src/components/profile/ProfileMenu.tsx
import React from 'react';
import { View, Text, Pressable } from 'react-native';
import { useRouter } from 'expo-router';
import Feather from '@expo/vector-icons/Feather';
import { useAuthStore } from '@/src/store/auth';
import { useTheme } from '@/src/theme/ThemeContext';

interface ProfileMenuProps {
  onLogout: () => void;
}

export function ProfileMenu({ onLogout }: ProfileMenuProps) {
  const { colors } = useTheme();
  const router = useRouter();
  const user = useAuthStore((state) => state.user);
  const routePrefix = user?.role === 'tutor' ? '/(tutor)' : user?.role === 'admin' ? '/(admin)' : '/(estudiante)';

  const menuItems = [
    {
      name: 'Configuración',
      icon: 'settings' as const,
      action: () => router.push(`${routePrefix}/configuracion` as any),
      isDestructive: false,
    },
    {
      name: 'Privacidad',
      icon: 'lock' as const,
      action: () => router.push(`${routePrefix}/privacidad` as any),
      isDestructive: false,
    },
    {
      name: 'Centro de ayuda',
      icon: 'help-circle' as const,
      action: () => router.push(`${routePrefix}/centro-ayuda` as any),
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
        const iconColor = item.isDestructive ? colors.danger : '#4B5563';
        const textColor = item.isDestructive ? colors.danger : colors.text;
        const arrowColor = item.isDestructive ? colors.danger : '#94A3B8';

        return (
          <Pressable
            key={index}
            onPress={item.action}
            style={{
              backgroundColor: colors.surface,
              borderRadius: 20,
              paddingVertical: 14,
              paddingHorizontal: 16,
              marginBottom: 12,
              borderWidth: 1,
              borderColor: colors.border,
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
