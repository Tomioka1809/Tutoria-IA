import React, { useState } from 'react';
import { View, Text, ScrollView, Pressable, Image, Alert, Modal, TextInput, ActivityIndicator } from 'react-native';
import { useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Feather from '@expo/vector-icons/Feather';
import { useProfile } from '@/src/components/profile/useProfile';
import { useAuthStore } from '@/src/store/auth';
import { usePreferencesStore } from '@/src/store/preferences';
import { useTheme } from '@/src/theme/ThemeContext';

export default function ConfiguracionScreen() {
  const { colors } = useTheme();
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const { user } = useProfile();
  const { profileImage, changePassword } = useAuthStore();
  const { theme, language, setTheme, setLanguage } = usePreferencesStore();
  
  const paddingTop = Math.max(insets.top, 16);

  const [pwdModalVisible, setPwdModalVisible] = useState(false);
  const [currentPwd, setCurrentPwd] = useState('');
  const [newPwd, setNewPwd] = useState('');
  const [isChangingPwd, setIsChangingPwd] = useState(false);

  // Dynamic Theme Colors
  const isDark = theme === 'dark';
  const bgColor = isDark ? '#121212' : colors.background;
  const cardColor = isDark ? '#1E1E1E' : 'white';
  const textColor = isDark ? '#FFFFFF' : '#111130';
  const subTextColor = isDark ? '#A0A0A0' : colors.textSecondary;
  const borderColor = isDark ? '#2C2C2C' : colors.border;

  // Translations POC
  const t = {
    config: language === 'en' ? 'Settings' : 'Configuración',
    account: language === 'en' ? 'Account' : 'Cuenta',
    editProfile: language === 'en' ? 'Edit Profile' : 'Editar perfil',
    editProfileDesc: language === 'en' ? 'Personal & academic data' : 'Datos personales y académicos',
    changePwd: language === 'en' ? 'Change Password' : 'Cambiar contraseña',
    changePwdDesc: language === 'en' ? 'Update your access key' : 'Actualiza tu clave de acceso',
    prefs: language === 'en' ? 'Preferences' : 'Preferencias',
    lang: language === 'en' ? 'Language' : 'Idioma',
    theme: language === 'en' ? 'Theme' : 'Tema',
  };

  const handleLanguageChange = () => {
    Alert.alert('Idioma / Language', 'Selecciona tu idioma / Choose your language', [
      { text: 'Español', onPress: () => setLanguage('es') },
      { text: 'English', onPress: () => setLanguage('en') },
      { text: 'Cancelar', style: 'cancel' }
    ]);
  };

  const handleThemeChange = () => {
    Alert.alert('Tema', 'Selecciona el tema de la aplicación', [
      { text: 'Claro (Light)', onPress: () => setTheme('light') },
      { text: 'Oscuro (Dark)', onPress: () => setTheme('dark') },
      { text: 'Sistema (System)', onPress: () => setTheme('system') },
      { text: 'Cancelar', style: 'cancel' }
    ]);
  };

  const handleChangePassword = async () => {
    if (!currentPwd || !newPwd) {
      Alert.alert('Error', 'Debes ingresar ambas contraseñas.');
      return;
    }
    if (newPwd.length < 6) {
      Alert.alert('Error', 'La nueva contraseña debe tener al menos 6 caracteres.');
      return;
    }

    setIsChangingPwd(true);
    const success = await changePassword(currentPwd, newPwd);
    setIsChangingPwd(false);

    if (success) {
      Alert.alert('Éxito', 'Contraseña actualizada correctamente.');
      setPwdModalVisible(false);
      setCurrentPwd('');
      setNewPwd('');
    } else {
      Alert.alert('Error', 'La contraseña actual es incorrecta o hubo un problema.');
    }
  };

  return (
    <View style={{ flex: 1, backgroundColor: bgColor }}>
      <ScrollView
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
                {t.config}
              </Text>
            </View>
            <Feather name="settings" size={24} color="white" />
          </View>

          {/* Student Card */}
          <View style={{
            backgroundColor: cardColor,
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
                color: textColor,
              }}>
                {user?.full_name || 'Sebastián Quispe'}
              </Text>
              <Text style={{
                fontSize: 13,
                color: subTextColor,
                fontWeight: '500',
                marginTop: 4,
              }}>
                Código: {user?.student_code || '2123456'}
              </Text>
              <Text style={{
                fontSize: 12,
                color: subTextColor,
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
            color: textColor,
            marginBottom: 12,
          }}>
            {t.account}
          </Text>

          <View style={{
            backgroundColor: cardColor,
            borderRadius: 24,
            borderWidth: 1,
            borderColor: borderColor,
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
                  <Text style={{ fontSize: 15, fontWeight: 'bold', color: textColor }}>
                    {t.editProfile}
                  </Text>
                  <Text style={{ fontSize: 12, color: subTextColor, marginTop: 2 }}>
                    {t.editProfileDesc}
                  </Text>
                </View>
              </View>
              <Feather name="chevron-right" size={20} color="#94A3B8" />
            </Pressable>

            {/* Divider */}
            <View style={{ height: 1, backgroundColor: borderColor, marginLeft: 72 }} />

            {/* Option: Cambiar Contraseña */}
            <Pressable
              style={{
                flexDirection: 'row',
                alignItems: 'center',
                justifyContent: 'space-between',
                paddingVertical: 14,
                paddingHorizontal: 16,
              }}
              onPress={() => setPwdModalVisible(true)}
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
                  <Text style={{ fontSize: 15, fontWeight: 'bold', color: textColor }}>
                    {t.changePwd}
                  </Text>
                  <Text style={{ fontSize: 12, color: subTextColor, marginTop: 2 }}>
                    {t.changePwdDesc}
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
            color: textColor,
            marginBottom: 12,
          }}>
            {t.prefs}
          </Text>

          <View style={{
            backgroundColor: cardColor,
            borderRadius: 24,
            borderWidth: 1,
            borderColor: borderColor,
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
              onPress={handleLanguageChange}
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
                <Text style={{ fontSize: 15, fontWeight: 'bold', color: textColor }}>
                  {t.lang}
                </Text>
              </View>
              <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                <Text style={{ fontSize: 14, color: subTextColor, marginRight: 8 }}>
                  {language === 'es' ? 'Español' : 'English'}
                </Text>
                <Feather name="chevron-right" size={20} color="#94A3B8" />
              </View>
            </Pressable>

            {/* Divider */}
            <View style={{ height: 1, backgroundColor: borderColor, marginLeft: 72 }} />

            {/* Option: Tema */}
            <Pressable
              style={{
                flexDirection: 'row',
                alignItems: 'center',
                justifyContent: 'space-between',
                paddingVertical: 14,
                paddingHorizontal: 16,
              }}
              onPress={handleThemeChange}
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
                <Text style={{ fontSize: 15, fontWeight: 'bold', color: textColor }}>
                  {t.theme}
                </Text>
              </View>
              <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                <Text style={{ fontSize: 14, color: subTextColor, marginRight: 8, textTransform: 'capitalize' }}>
                  {theme}
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
            color: textColor,
            marginBottom: 12,
          }}>
            Información
          </Text>

          <View style={{
            backgroundColor: cardColor,
            borderRadius: 24,
            borderWidth: 1,
            borderColor: borderColor,
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
                  <Text style={{ fontSize: 15, fontWeight: 'bold', color: textColor }}>
                    Acerca de TutorIA
                  </Text>
                  <Text style={{ fontSize: 12, color: subTextColor, marginTop: 2 }}>
                    Versión 1.0.0
                  </Text>
                </View>
              </View>
              <Feather name="chevron-right" size={20} color="#94A3B8" />
            </Pressable>
          </View>
        </View>
      </ScrollView>

      {/* Password Change Modal */}
      <Modal
        visible={pwdModalVisible}
        transparent
        animationType="fade"
        onRequestClose={() => setPwdModalVisible(false)}
      >
        <View style={{ flex: 1, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'center', alignItems: 'center' }}>
          <View style={{ backgroundColor: cardColor, width: '80%', borderRadius: 24, padding: 24 }}>
            <Text style={{ fontSize: 18, fontWeight: 'bold', color: textColor, marginBottom: 16 }}>
              {t.changePwd}
            </Text>
            
            <Text style={{ fontSize: 14, color: textColor, marginBottom: 8 }}>Contraseña Actual</Text>
            <TextInput
              style={{ borderWidth: 1, borderColor: borderColor, borderRadius: 12, padding: 12, color: textColor, marginBottom: 16 }}
              secureTextEntry
              value={currentPwd}
              onChangeText={setCurrentPwd}
              placeholder="Ingresa tu contraseña actual"
              placeholderTextColor={subTextColor}
            />

            <Text style={{ fontSize: 14, color: textColor, marginBottom: 8 }}>Nueva Contraseña</Text>
            <TextInput
              style={{ borderWidth: 1, borderColor: borderColor, borderRadius: 12, padding: 12, color: textColor, marginBottom: 24 }}
              secureTextEntry
              value={newPwd}
              onChangeText={setNewPwd}
              placeholder="Mínimo 6 caracteres"
              placeholderTextColor={subTextColor}
            />

            <View style={{ flexDirection: 'row', justifyContent: 'flex-end' }}>
              <Pressable
                onPress={() => setPwdModalVisible(false)}
                style={{ paddingHorizontal: 16, paddingVertical: 10, marginRight: 8 }}
              >
                <Text style={{ color: subTextColor, fontWeight: '600' }}>Cancelar</Text>
              </Pressable>
              
              <Pressable
                onPress={handleChangePassword}
                disabled={isChangingPwd}
                style={{ backgroundColor: colors.primary, paddingHorizontal: 16, paddingVertical: 10, borderRadius: 12, opacity: isChangingPwd ? 0.7 : 1 }}
              >
                {isChangingPwd ? <ActivityIndicator size="small" color="#fff" /> : <Text style={{ color: 'white', fontWeight: 'bold' }}>Guardar</Text>}
              </Pressable>
            </View>
          </View>
        </View>
      </Modal>
    </View>
  );
}
