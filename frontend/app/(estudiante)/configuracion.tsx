import React from 'react';
import { View, Text, ScrollView, Pressable, Image } from 'react-native';
import { useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Feather from '@expo/vector-icons/Feather';
import { useProfile } from '@/src/components/profile/useProfile';
import { useAuthStore } from '@/src/store/auth';
import { useTheme } from '@/src/theme/ThemeContext';

export default function ConfiguracionScreen() {
  const { colors } = useTheme();
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const { user } = useProfile();
  const profileImage = useAuthStore((s) => s.profileImage);
  const paddingTop = Math.max(insets.top, 16);

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
            <Pressable 
              onPress={() => router.replace('/(estudiante)/profile' as any)} 
              style={{ marginRight: 16 }}
            >
              <Feather name="arrow-left" size={24} color="white" />
            </Pressable>
            <Text style={{
              fontSize: 20,
              fontWeight: 'bold',
              color: 'white',
            }}>
              Configuración
            </Text>
          </View>
          <Feather name="settings" size={24} color="white" />
        </View>

        {/* Student Card */}
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
          marginBottom: -16, // overlap slightly with the bottom boundary
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
            }} />
          )}

          {/* Student details */}
          <View style={{ flex: 1 }}>
            <Text style={{
              fontSize: 18,
              fontWeight: 'bold',
              color: colors.text,
            }}>
              {user?.full_name || 'Sebastián Quispe'}
            </Text>
            <Text style={{
              fontSize: 13,
              color: colors.textSecondary,
              fontWeight: '500',
              marginTop: 4,
            }}>
              Código: {user?.student_code || '2123456'}
            </Text>
            <Text style={{
              fontSize: 12,
              color: colors.textSecondary,
              fontWeight: '500',
              marginTop: 2,
            }} numberOfLines={1}>
              {user?.school || 'Ingeniería Informática y de Sistemas'} · {user?.semester || 'VI Semestre'}
            </Text>
          </View>
        </View>
      </View>

      {/* Spacer to compensate for negative margin card overflow */}
      <View style={{ height: 24 }} />

      {/* Cuenta Section */}
      <View style={{ paddingHorizontal: 24, marginBottom: 24 }}>
        <Text style={{
          fontSize: 16,
          fontWeight: 'bold',
          color: colors.text,
          marginBottom: 12,
        }}>
          Cuenta
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
          {/* Option: Editar Perfil */}
          <Pressable
            style={{
              flexDirection: 'row',
              alignItems: 'center',
              justifyContent: 'space-between',
              paddingVertical: 14,
              paddingHorizontal: 16,
            }}
            onPress={() => router.push('/(estudiante)/editar-perfil' as any)}
          >
            <View style={{ flexDirection: 'row', alignItems: 'center', flex: 1 }}>
              <View style={{
                width: 40,
                height: 40,
                borderRadius: 20,
                backgroundColor: '#F3E8FF',
                alignItems: 'center',
                justifyContent: 'center',
                marginRight: 16,
              }}>
                <Feather name="user" size={20} color={colors.primary} />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={{ fontSize: 15, fontWeight: 'bold', color: colors.text }}>
                  Editar perfil
                </Text>
                <Text style={{ fontSize: 12, color: colors.textSecondary, marginTop: 2 }}>
                  Datos personales y académicos
                </Text>
              </View>
            </View>
            <Feather name="chevron-right" size={20} color="#94A3B8" />
          </Pressable>

          {/* Divider */}
          <View style={{ height: 1, backgroundColor: colors.border, marginLeft: 72 }} />

          {/* Option: Cambiar Contraseña */}
          <Pressable
            style={{
              flexDirection: 'row',
              alignItems: 'center',
              justifyContent: 'space-between',
              paddingVertical: 14,
              paddingHorizontal: 16,
            }}
            onPress={() => alert('Cambiar contraseña en desarrollo')}
          >
            <View style={{ flexDirection: 'row', alignItems: 'center', flex: 1 }}>
              <View style={{
                width: 40,
                height: 40,
                borderRadius: 20,
                backgroundColor: '#F3E8FF',
                alignItems: 'center',
                justifyContent: 'center',
                marginRight: 16,
              }}>
                <Feather name="lock" size={20} color={colors.primary} />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={{ fontSize: 15, fontWeight: 'bold', color: colors.text }}>
                  Cambiar contraseña
                </Text>
                <Text style={{ fontSize: 12, color: colors.textSecondary, marginTop: 2 }}>
                  Actualiza tu clave de acceso
                </Text>
              </View>
            </View>
            <Feather name="chevron-right" size={20} color="#94A3B8" />
          </Pressable>
        </View>
      </View>

      {/* Preferencias Section */}
      <View style={{ paddingHorizontal: 24, marginBottom: 24 }}>
        <Text style={{
          fontSize: 16,
          fontWeight: 'bold',
          color: colors.text,
          marginBottom: 12,
        }}>
          Preferencias
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
          {/* Option: Idioma */}
          <Pressable
            style={{
              flexDirection: 'row',
              alignItems: 'center',
              justifyContent: 'space-between',
              paddingVertical: 14,
              paddingHorizontal: 16,
            }}
            onPress={() => alert('Idioma en desarrollo')}
          >
            <View style={{ flexDirection: 'row', alignItems: 'center', flex: 1 }}>
              <View style={{
                width: 40,
                height: 40,
                borderRadius: 20,
                backgroundColor: '#F3E8FF',
                alignItems: 'center',
                justifyContent: 'center',
                marginRight: 16,
              }}>
                <Feather name="globe" size={20} color={colors.primary} />
              </View>
              <Text style={{ fontSize: 15, fontWeight: 'bold', color: colors.text }}>
                Idioma
              </Text>
            </View>
            <View style={{ flexDirection: 'row', alignItems: 'center' }}>
              <Text style={{ fontSize: 14, color: colors.textSecondary, marginRight: 8 }}>
                Español
              </Text>
              <Feather name="chevron-right" size={20} color="#94A3B8" />
            </View>
          </Pressable>

          {/* Divider */}
          <View style={{ height: 1, backgroundColor: colors.border, marginLeft: 72 }} />

          {/* Option: Tema */}
          <Pressable
            style={{
              flexDirection: 'row',
              alignItems: 'center',
              justifyContent: 'space-between',
              paddingVertical: 14,
              paddingHorizontal: 16,
            }}
            onPress={() => alert('Tema en desarrollo')}
          >
            <View style={{ flexDirection: 'row', alignItems: 'center', flex: 1 }}>
              <View style={{
                width: 40,
                height: 40,
                borderRadius: 20,
                backgroundColor: '#F3E8FF',
                alignItems: 'center',
                justifyContent: 'center',
                marginRight: 16,
              }}>
                <Feather name="sun" size={20} color={colors.primary} />
              </View>
              <Text style={{ fontSize: 15, fontWeight: 'bold', color: colors.text }}>
                Tema
              </Text>
            </View>
            <View style={{ flexDirection: 'row', alignItems: 'center' }}>
              <Text style={{ fontSize: 14, color: colors.textSecondary, marginRight: 8 }}>
                Claro
              </Text>
              <Feather name="chevron-right" size={20} color="#94A3B8" />
            </View>
          </Pressable>
        </View>
      </View>

      {/* Información Section */}
      <View style={{ paddingHorizontal: 24, marginBottom: 24 }}>
        <Text style={{
          fontSize: 16,
          fontWeight: 'bold',
          color: colors.text,
          marginBottom: 12,
        }}>
          Información
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
          {/* Option: Acerca de TutorIA */}
          <Pressable
            style={{
              flexDirection: 'row',
              alignItems: 'center',
              justifyContent: 'space-between',
              paddingVertical: 14,
              paddingHorizontal: 16,
            }}
            onPress={() => alert('TutorIA Versión 1.0.0')}
          >
            <View style={{ flexDirection: 'row', alignItems: 'center', flex: 1 }}>
              <View style={{
                width: 40,
                height: 40,
                borderRadius: 20,
                backgroundColor: '#F3E8FF',
                alignItems: 'center',
                justifyContent: 'center',
                marginRight: 16,
              }}>
                <Feather name="info" size={20} color={colors.primary} />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={{ fontSize: 15, fontWeight: 'bold', color: colors.text }}>
                  Acerca de TutorIA
                </Text>
                <Text style={{ fontSize: 12, color: colors.textSecondary, marginTop: 2 }}>
                  Versión 1.0.0
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
