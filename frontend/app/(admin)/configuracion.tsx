import React from 'react';
import { View, Text, ScrollView, Pressable, Image } from 'react-native';
import { useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Feather from '@expo/vector-icons/Feather';
import { useAuthStore } from '@/src/store/auth';
import { useTheme } from '@/src/theme/ThemeContext';

export default function AdminConfiguracionScreen() {
  const { colors } = useTheme();
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const profileImage = useAuthStore((s) => s.profileImage);
  const paddingTop = Math.max(insets.top, 16);

  const handleLogout = () => {
    logout();
    router.replace('/auth/login');
  };

  return (
    <ScrollView
      style={{ flex: 1, backgroundColor: colors.background }}
      contentContainerStyle={{ paddingBottom: 130 }}
      showsVerticalScrollIndicator={false}
    >
      {/* Header Container */}
      <View style={{
        backgroundColor: colors.primary,
        paddingTop: paddingTop + 16,
        paddingBottom: 48,
        paddingHorizontal: 24,
        borderBottomLeftRadius: 32,
        borderBottomRightRadius: 32,
      }}>
        {/* Top Header Row */}
        <View style={{
          flexDirection: 'row',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 20,
        }}>
          <View style={{ flexDirection: 'row', alignItems: 'center' }}>
            <Text style={{
              fontSize: 20,
              fontWeight: 'bold',
              color: 'white',
            }}>
              Ajustes de Administrador
            </Text>
          </View>
          <Feather name="settings" size={24} color="white" />
        </View>

        {/* Admin Card */}
        <View style={{
          backgroundColor: colors.surface,
          borderRadius: 24,
          padding: 20,
          flexDirection: 'row',
          alignItems: 'center',
          shadowColor: '#000',
          shadowOffset: { width: 0, height: 4 },
          shadowOpacity: 0.08,
          shadowRadius: 12,
          elevation: 4,
          marginBottom: -16,
        }}>
          {/* Avatar */}
          {profileImage ? (
            <Image
              source={{ uri: profileImage }}
              style={{
                width: 64,
                height: 64,
                borderRadius: 32,
                backgroundColor: '#CBD5E1',
                marginRight: 16,
              }}
              resizeMode="cover"
            />
          ) : (
            <View style={{
              width: 64,
              height: 64,
              borderRadius: 32,
              backgroundColor: '#CBD5E1',
              marginRight: 16,
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <Feather name="shield" size={30} color="white" />
            </View>
          )}

          {/* Admin details */}
          <View style={{ flex: 1 }}>
            <Text style={{
              fontSize: 18,
              fontWeight: 'bold',
              color: colors.text,
            }}>
              {user?.full_name || 'Admin'}
            </Text>
            <Text style={{
              fontSize: 13,
              color: colors.textSecondary,
              fontWeight: '500',
              marginTop: 4,
            }}>
              {user?.email || 'admin@admin.com'}
            </Text>
            <Text style={{
              fontSize: 12,
              color: colors.primary,
              fontWeight: 'bold',
              marginTop: 2,
            }}>
              Administrador del Sistema
            </Text>
          </View>
        </View>
      </View>

      <View style={{ height: 24 }} />

      {/* Cuenta Section */}
      <View style={{ paddingHorizontal: 24, marginBottom: 24 }}>
        <Text style={{
          fontSize: 16,
          fontWeight: 'bold',
          color: colors.text,
          marginBottom: 12,
        }}>
          Acceso
        </Text>

        <View style={{
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
        }}>
          {/* Option: Cerrar Sesión */}
          <Pressable
            style={{
              flexDirection: 'row',
              alignItems: 'center',
              justifyContent: 'space-between',
              paddingVertical: 14,
              paddingHorizontal: 16,
            }}
            onPress={handleLogout}
          >
            <View style={{ flexDirection: 'row', alignItems: 'center', flex: 1 }}>
              <View style={{
                width: 40,
                height: 40,
                borderRadius: 20,
                backgroundColor: '#FEE2E2',
                alignItems: 'center',
                justifyContent: 'center',
                marginRight: 16,
              }}>
                <Feather name="log-out" size={20} color="#DC2626" />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={{ fontSize: 15, fontWeight: 'bold', color: '#DC2626' }}>
                  Cerrar Sesión
                </Text>
                <Text style={{ fontSize: 12, color: colors.textSecondary, marginTop: 2 }}>
                  Salir de la cuenta de administrador
                </Text>
              </View>
            </View>
            <Feather name="chevron-right" size={20} color="#94A3B8" />
          </Pressable>
        </View>
      </View>
    </ScrollView>
  );
}
