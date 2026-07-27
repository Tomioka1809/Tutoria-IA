import React, { useState } from 'react';
import { View, Text, ScrollView, Pressable, Image, Modal } from 'react-native';
import { useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Feather from '@expo/vector-icons/Feather';
import { useAuthStore } from '@/src/store/auth';
import { usePreferencesStore } from '@/src/store/preferences';
import { useTheme } from '@/src/theme/ThemeContext';
import { useTranslation } from 'react-i18next';

export default function AdminConfiguracionScreen() {
  const { colors } = useTheme();
  const { t: tr } = useTranslation();
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const profileImage = useAuthStore((s) => s.profileImage);
  const { theme, language, setTheme, setLanguage } = usePreferencesStore();
  const paddingTop = Math.max(insets.top, 16);
  const [languageModalVisible, setLanguageModalVisible] = useState(false);
  const [themeModalVisible, setThemeModalVisible] = useState(false);
  const [selectedLanguage, setSelectedLanguage] = useState<'es' | 'en'>(language);
  const [selectedTheme, setSelectedTheme] = useState<'light' | 'dark'>(theme === 'dark' ? 'dark' : 'light');
  const isDark = theme === 'dark';
  const secondaryColor = isDark ? '#FFFFFF' : colors.textSecondary;

  const t = {
    prefs: tr('settings.preferences'),
    lang: tr('settings.language'),
    theme: tr('settings.theme'),
    changeTheme: tr('settings.changeTheme'),
    changeThemeDesc: tr('settings.changeThemeDescription'),
    light: tr('settings.light'),
    dark: tr('settings.dark'),
  };

  const handleLanguageChange = () => {
    setSelectedLanguage(language);
    setLanguageModalVisible(true);
  };

  const handleThemeChange = () => {
    setSelectedTheme(theme === 'dark' ? 'dark' : 'light');
    setThemeModalVisible(true);
  };

  const handleLogout = () => {
    logout();
    router.replace('/auth/login');
  };

  return (
    <ScrollView
      style={{ flex: 1, backgroundColor: isDark ? '#000000' : colors.background }}
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
              {tr('admin.adminSettings')}
            </Text>
          </View>
        </View>

        {/* Admin Card */}
        <View style={{
          backgroundColor: colors.surface,
          borderRadius: 24,
          borderWidth: isDark ? 1 : 0,
          borderColor: isDark ? '#FFFFFF' : 'transparent',
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
              color: secondaryColor,
              fontWeight: '500',
              marginTop: 4,
            }}>
              {user?.email || 'admin@admin.com'}
            </Text>
            <Text style={{
              fontSize: 12,
              color: isDark ? '#FFFFFF' : colors.primary,
              fontWeight: 'bold',
              marginTop: 2,
            }}>
              {tr('admin.systemAdministrator')}
            </Text>
          </View>
        </View>
      </View>

      <View style={{ height: 24 }} />

      {/* Preferencias Section */}
      <View style={{ paddingHorizontal: 24, marginBottom: 24 }}>
        <Text style={{
          fontSize: 16,
          fontWeight: 'bold',
          color: colors.text,
          marginBottom: 12,
        }}>
          {t.prefs}
        </Text>

        <View style={{
          backgroundColor: colors.surface,
          borderRadius: 24,
          borderWidth: 1,
          borderColor: isDark ? '#FFFFFF' : colors.border,
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
              <Text style={{ fontSize: 15, fontWeight: 'bold', color: colors.text }}>
                {t.lang}
              </Text>
            </View>
            <View style={{ flexDirection: 'row', alignItems: 'center' }}>
              <Text style={{ fontSize: 14, color: secondaryColor, marginRight: 8 }}>
                {language === 'es' ? 'Español' : 'English'}
              </Text>
              <Feather name="chevron-right" size={20} color="#94A3B8" />
            </View>
          </Pressable>

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
              <Text style={{ fontSize: 15, fontWeight: 'bold', color: colors.text }}>
                {t.theme}
              </Text>
            </View>
            <View style={{ flexDirection: 'row', alignItems: 'center' }}>
              <Text style={{ fontSize: 14, color: secondaryColor, marginRight: 8 }}>
                {theme === 'dark' ? t.dark : t.light}
              </Text>
              <Feather name="chevron-right" size={20} color="#94A3B8" />
            </View>
          </Pressable>
        </View>
      </View>

      {/* Cuenta Section */}
      <View style={{ paddingHorizontal: 24, marginBottom: 24 }}>
        <Text style={{
          fontSize: 16,
          fontWeight: 'bold',
          color: colors.text,
          marginBottom: 12,
        }}>
          {tr('admin.access')}
        </Text>

        <View style={{
          backgroundColor: colors.surface,
          borderRadius: 24,
          borderWidth: 1,
          borderColor: isDark ? '#FFFFFF' : colors.border,
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
                <Text style={{ fontSize: 15, fontWeight: 'bold', color: isDark ? '#FFFFFF' : '#DC2626' }}>
                  {tr('admin.logout')}
                </Text>
                <Text style={{ fontSize: 12, color: secondaryColor, marginTop: 2 }}>
                  {tr('admin.logoutDescription')}
                </Text>
              </View>
            </View>
            <Feather name="chevron-right" size={20} color="#94A3B8" />
          </Pressable>
        </View>
      </View>

      {/* Language Modal */}
      <Modal
        visible={languageModalVisible}
        transparent
        animationType="fade"
        onRequestClose={() => setLanguageModalVisible(false)}
      >
        <View style={{ flex: 1, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'center', alignItems: 'center' }}>
          <View style={{ backgroundColor: colors.surface, width: '80%', borderRadius: 24, borderWidth: isDark ? 1 : 0, borderColor: isDark ? '#FFFFFF' : 'transparent', padding: 24, shadowColor: '#000', shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.12, shadowRadius: 10, elevation: 6 }}>
            <Text style={{ fontSize: 18, fontWeight: 'bold', color: colors.text }}>
              {tr('settings.changeLanguage')}
            </Text>
            <Text style={{ fontSize: 14, color: secondaryColor, marginTop: 6, marginBottom: 16 }}>
              {tr('settings.changeLanguageDescription')}
            </Text>

            {([
              { value: 'es' as const, label: 'Español' },
              { value: 'en' as const, label: 'English' },
            ]).map((option) => {
              const isSelected = selectedLanguage === option.value;
              return (
                <Pressable
                  key={option.value}
                  onPress={() => setSelectedLanguage(option.value)}
                  style={{
                    minHeight: 52,
                    borderWidth: isSelected ? 1.5 : 1,
                    borderColor: isSelected ? colors.primary : (isDark ? '#FFFFFF' : colors.border),
                    borderRadius: 12,
                    paddingHorizontal: 12,
                    marginBottom: 10,
                    flexDirection: 'row',
                    alignItems: 'center',
                    backgroundColor: isSelected ? (isDark ? '#2A183D' : '#FBF7FF') : colors.surface,
                  }}
                >
                  <View style={{ width: 34, height: 34, borderRadius: 17, backgroundColor: isSelected ? '#F3E8FF' : (isDark ? '#2C2C2C' : '#F5F5F7'), alignItems: 'center', justifyContent: 'center' }}>
                    <Feather name="globe" size={19} color={isSelected ? colors.primary : secondaryColor} />
                  </View>
                  <Text style={{ flex: 1, fontSize: 15, fontWeight: '600', color: colors.text, marginLeft: 12 }}>
                    {option.label}
                  </Text>
                  {isSelected ? (
                    <View style={{ width: 24, height: 24, borderRadius: 12, backgroundColor: colors.primary, alignItems: 'center', justifyContent: 'center' }}>
                      <Feather name="check" size={16} color="#FFFFFF" />
                    </View>
                  ) : (
                    <View style={{ width: 24, height: 24, borderRadius: 12, borderWidth: 2, borderColor: secondaryColor }} />
                  )}
                </Pressable>
              );
            })}

            <View style={{ flexDirection: 'row', justifyContent: 'flex-end', marginTop: 6 }}>
              <Pressable onPress={() => setLanguageModalVisible(false)} style={{ paddingHorizontal: 16, paddingVertical: 10, marginRight: 8 }}>
                <Text style={{ color: secondaryColor, fontWeight: '600' }}>{tr('common.cancel')}</Text>
              </Pressable>
              <Pressable
                onPress={() => {
                  setLanguage(selectedLanguage);
                  setLanguageModalVisible(false);
                }}
                style={{ backgroundColor: colors.primary, paddingHorizontal: 16, paddingVertical: 10, borderRadius: 12 }}
              >
                <Text style={{ color: '#FFFFFF', fontWeight: 'bold' }}>{tr('common.save')}</Text>
              </Pressable>
            </View>
          </View>
        </View>
      </Modal>

      {/* Theme Modal */}
      <Modal
        visible={themeModalVisible}
        transparent
        animationType="fade"
        onRequestClose={() => setThemeModalVisible(false)}
      >
        <View style={{ flex: 1, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'center', alignItems: 'center' }}>
          <View style={{ backgroundColor: colors.surface, width: '80%', borderRadius: 24, borderWidth: isDark ? 1 : 0, borderColor: isDark ? '#FFFFFF' : 'transparent', padding: 24, shadowColor: '#000', shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.12, shadowRadius: 10, elevation: 6 }}>
            <Text style={{ fontSize: 18, fontWeight: 'bold', color: colors.text }}>
              {t.changeTheme}
            </Text>
            <Text style={{ fontSize: 14, color: secondaryColor, marginTop: 6, marginBottom: 16 }}>
              {t.changeThemeDesc}
            </Text>

            {([
              { value: 'light' as const, label: t.light, icon: 'sun' as const },
              { value: 'dark' as const, label: t.dark, icon: 'moon' as const },
            ]).map((option) => {
              const isSelected = selectedTheme === option.value;
              return (
                <Pressable
                  key={option.value}
                  onPress={() => setSelectedTheme(option.value)}
                  style={{
                    minHeight: 52,
                    borderWidth: isSelected ? 1.5 : 1,
                    borderColor: isSelected ? colors.primary : (isDark ? '#FFFFFF' : colors.border),
                    borderRadius: 12,
                    paddingHorizontal: 12,
                    marginBottom: 10,
                    flexDirection: 'row',
                    alignItems: 'center',
                    backgroundColor: isSelected ? (isDark ? '#2A183D' : '#FBF7FF') : colors.surface,
                  }}
                >
                  <View style={{ width: 34, height: 34, borderRadius: 17, backgroundColor: isSelected ? '#F3E8FF' : (isDark ? '#2C2C2C' : '#F5F5F7'), alignItems: 'center', justifyContent: 'center' }}>
                    <Feather name={option.icon} size={19} color={isSelected ? colors.primary : colors.text} />
                  </View>
                  <Text style={{ flex: 1, fontSize: 15, fontWeight: '600', color: colors.text, marginLeft: 12 }}>
                    {option.label}
                  </Text>
                  {isSelected ? (
                    <View style={{ width: 24, height: 24, borderRadius: 12, backgroundColor: colors.primary, alignItems: 'center', justifyContent: 'center' }}>
                      <Feather name="check" size={16} color="#FFFFFF" />
                    </View>
                  ) : (
                    <View style={{ width: 24, height: 24, borderRadius: 12, borderWidth: 2, borderColor: secondaryColor }} />
                  )}
                </Pressable>
              );
            })}

            <View style={{ flexDirection: 'row', justifyContent: 'flex-end', marginTop: 6 }}>
              <Pressable onPress={() => setThemeModalVisible(false)} style={{ paddingHorizontal: 16, paddingVertical: 10, marginRight: 8 }}>
                <Text style={{ color: secondaryColor, fontWeight: '600' }}>{tr('common.cancel')}</Text>
              </Pressable>
              <Pressable
                onPress={() => {
                  setTheme(selectedTheme);
                  setThemeModalVisible(false);
                }}
                style={{ backgroundColor: colors.primary, paddingHorizontal: 16, paddingVertical: 10, borderRadius: 12 }}
              >
                <Text style={{ color: '#FFFFFF', fontWeight: 'bold' }}>{tr('common.save')}</Text>
              </Pressable>
            </View>
          </View>
        </View>
      </Modal>
    </ScrollView>
  );
}
