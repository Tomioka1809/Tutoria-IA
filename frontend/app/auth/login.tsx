import React, { useState } from 'react';
import { View, TextInput, Text, Pressable, ActivityIndicator, KeyboardAvoidingView, Platform, ScrollView, Alert } from 'react-native';
import { useRouter, Link } from 'expo-router';
import { useAuthStore } from '../../src/store/auth';
import client from '../../src/api/client';
import { ThemedText } from '../../components/themed-text';
import { ThemedView } from '../../components/themed-view';
import { useTranslation } from 'react-i18next';
import { useTheme } from '@/src/theme/ThemeContext';

export default function LoginScreen() {
  const { t } = useTranslation();
  const { colors } = useTheme();
  
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();
  const setAuth = useAuthStore((state) => state.setAuth);

  const handleLogin = async () => {
    if (!email || !password) {
      setError(t('auth.login.emptyFields') || 'Por favor, ingresa tu correo y contraseña.');
      return;
    }
    setError('');
    setIsLoading(true);
    try {
      const formData = new FormData();
      formData.append('username', email.trim().toLowerCase());
      formData.append('password', password);

      const response = await client.post('/auth/login', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      const { access_token } = response.data;

      const userResponse = await client.get('/auth/me', {
        headers: {
          Authorization: `Bearer ${access_token}`,
        },
      });

      setAuth(access_token, userResponse.data);
      if (userResponse.data.role === 'admin') {
        router.replace('/(admin)');
      } else if (userResponse.data.role === 'tutor') {
        router.replace('/(tutor)');
      } else {
        router.replace('/(estudiante)');
      }
    } catch (e: any) {
      let errorMessage = 'Error de conexión. Revisa tus credenciales.';
      if (!e.response) {
        errorMessage = 'No se pudo conectar con el servidor. Verifica tu conexión a internet.';
      } else if (e.response.status === 401) {
        errorMessage = e.response.data?.detail || 'Correo o contraseña incorrectos.';
      } else if (e.response.data?.detail) {
        errorMessage = e.response.data.detail;
      }
      
      Alert.alert('Error de Inicio de Sesión', errorMessage);
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      style={{ flex: 1, backgroundColor: colors.background }}
    >
      <ScrollView contentContainerStyle={{ flexGrow: 1, justifyContent: 'center' }} className="px-6">
        <View className="items-center mb-8">
          <Text className="text-5xl mb-2">🦖</Text>
          <Text style={{ color: colors.text, fontSize: 30, fontWeight: 'bold' }}>TutorIA</Text>
          <Text style={{ color: colors.primary, fontSize: 14, textAlign: 'center', marginTop: 4 }}>
            {t('auth.login.subtitle') || 'Tu tutor inteligente en tu bolsillo'}
          </Text>
        </View>

        <View style={{ backgroundColor: colors.surface, borderRadius: 24, padding: 24, shadowColor: '#000', shadowOffset: {width:0,height:2}, shadowOpacity:0.1, elevation:4 }}>
          <Text style={{ color: colors.text, fontSize: 20, fontWeight: 'bold', marginBottom: 24, textAlign: 'center' }}>
            {t('auth.login.title') || 'Iniciar Sesión'}
          </Text>
          
          {error ? (
            <View style={{ backgroundColor: colors.danger + '20', borderColor: colors.danger + '40', borderWidth: 1, borderRadius: 12, padding: 12, marginBottom: 16 }}>
              <Text style={{ color: colors.danger, fontSize: 12, textAlign: 'center' }}>{error}</Text>
            </View>
          ) : null}

          <View className="mb-4">
            <Text style={{ color: colors.text, fontSize: 12, fontWeight: '600', marginBottom: 8, marginLeft: 4 }}>
              {t('auth.login.email') || 'Correo Electrónico'}
            </Text>
            <TextInput
              value={email}
              onChangeText={setEmail}
              placeholder={t('auth.login.emailPlaceholder') || 'ejemplo@correo.com'}
              keyboardType="email-address"
              autoCapitalize="none"
              style={{ backgroundColor: colors.background, borderColor: colors.border, borderWidth: 1, borderRadius: 12, paddingHorizontal: 16, paddingVertical: 12, color: colors.text }}
              placeholderTextColor={colors.textSecondary}
            />
          </View>

          <View className="mb-6">
            <Text style={{ color: colors.text, fontSize: 12, fontWeight: '600', marginBottom: 8, marginLeft: 4 }}>
              {t('auth.login.password') || 'Contraseña'}
            </Text>
            <TextInput
              value={password}
              onChangeText={setPassword}
              placeholder="••••••••"
              secureTextEntry
              autoCapitalize="none"
              style={{ backgroundColor: colors.background, borderColor: colors.border, borderWidth: 1, borderRadius: 12, paddingHorizontal: 16, paddingVertical: 12, color: colors.text }}
              placeholderTextColor={colors.textSecondary}
            />
          </View>

          <Link href="/auth/forgot-password" asChild>
            <Pressable style={{ alignSelf: 'flex-end', marginTop: -8, marginBottom: 20 }}>
              <Text style={{ fontSize: 13, color: colors.primary, fontWeight: '600' }}>
                ¿Olvidaste tu contraseña?
              </Text>
            </Pressable>
          </Link>

          <Pressable
            onPress={handleLogin}
            disabled={isLoading}
            style={{ backgroundColor: colors.primary, borderRadius: 12, paddingVertical: 12, alignItems: 'center', justifyContent: 'center', opacity: isLoading ? 0.8 : 1 }}
          >
            {isLoading ? (
              <ActivityIndicator color="white" />
            ) : (
              <Text style={{ color: 'white', fontWeight: 'bold', fontSize: 16 }}>
                {t('auth.login.button') || 'Ingresar'}
              </Text>
            )}
          </Pressable>
        </View>

        <View className="flex-row justify-center mt-6">
          <Text style={{ fontSize: 14, color: colors.text }}>
            {t('auth.login.noAccount') || '¿No tienes una cuenta? '}
          </Text>
          <Link href="/auth/register" asChild>
            <Pressable>
              <Text style={{ fontSize: 14, fontWeight: 'bold', color: colors.primary }}>
                {t('auth.login.registerLink') || 'Regístrate aquí'}
              </Text>
            </Pressable>
          </Link>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}
