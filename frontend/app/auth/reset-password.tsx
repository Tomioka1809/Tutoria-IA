import React, { useState } from 'react';
import { View, TextInput, Text, Pressable, ActivityIndicator, KeyboardAvoidingView, Platform, ScrollView, Alert } from 'react-native';
import { useRouter, useLocalSearchParams } from 'expo-router';
import client from '../../src/api/client';
import { useTheme } from '@/src/theme/ThemeContext';
import { Feather } from '@expo/vector-icons';

export default function ResetPasswordScreen() {
  const { colors } = useTheme();
  const router = useRouter();
  const { email: paramEmail } = useLocalSearchParams<{ email: string }>();

  const [email, setEmail] = useState(paramEmail || '');
  const [token, setToken] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleResetPassword = async () => {
    if (!email || !token || !newPassword || !confirmPassword) {
      setError('Por favor, completa todos los campos.');
      return;
    }
    if (newPassword.length < 6) {
      setError('La contraseña debe tener al menos 6 caracteres.');
      return;
    }
    if (newPassword !== confirmPassword) {
      setError('Las contraseñas ingresadas no coinciden.');
      return;
    }

    setError('');
    setIsLoading(true);
    try {
      await client.post('/auth/reset-password', {
        email: email.trim().toLowerCase(),
        token: token.trim(),
        new_password: newPassword
      });

      Alert.alert(
        'Contraseña Restablecida',
        'Tu contraseña ha sido restablecida con éxito. Ya puedes iniciar sesión.',
        [
          {
            text: 'Iniciar Sesión',
            onPress: () => {
              router.replace('/auth/login');
            }
          }
        ]
      );
    } catch (e: any) {
      let errorMessage = 'No se pudo restablecer la contraseña.';
      if (!e.response) {
        errorMessage = 'No se pudo conectar con el servidor. Verifica tu conexión a internet.';
      } else if (e.response.data?.detail) {
        errorMessage = e.response.data.detail;
      }
      
      Alert.alert('Error', errorMessage);
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const labelStyle = { color: colors.text, fontSize: 12, fontWeight: '600' as const, marginBottom: 8, marginLeft: 4 };
  const inputStyle = { backgroundColor: colors.background, borderColor: colors.border, borderWidth: 1, borderRadius: 12, paddingHorizontal: 16, paddingVertical: 12, color: colors.text };

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      style={{ flex: 1, backgroundColor: colors.background }}
    >
      <ScrollView contentContainerStyle={{ flexGrow: 1, justifyContent: 'center' }} className="px-6 py-12">
        
        {/* Back Button */}
        <Pressable 
          onPress={() => router.back()}
          style={{ position: 'absolute', top: 50, left: 24, zIndex: 10, flexDirection: 'row', alignItems: 'center' }}
        >
          <Feather name="arrow-left" size={24} color={colors.text} />
          <Text style={{ color: colors.text, fontSize: 16, marginLeft: 8, fontWeight: '600' }}>Volver</Text>
        </Pressable>

        <View className="items-center mb-8">
          <Text className="text-5xl mb-2">🦖</Text>
          <Text style={{ color: colors.text, fontSize: 30, fontWeight: 'bold' }}>TutorIA</Text>
          <Text style={{ color: colors.primary, fontSize: 14, textAlign: 'center', marginTop: 4 }}>
            Restablecer Contraseña
          </Text>
        </View>

        <View style={{ backgroundColor: colors.surface, borderRadius: 24, padding: 24, shadowColor: '#000', shadowOffset: {width:0,height:2}, shadowOpacity:0.1, elevation:4 }}>
          <Text style={{ color: colors.text, fontSize: 20, fontWeight: 'bold', marginBottom: 24, textAlign: 'center' }}>
            Nueva Contraseña
          </Text>
          
          {error ? (
            <View style={{ backgroundColor: colors.danger + '20', borderColor: colors.danger + '40', borderWidth: 1, borderRadius: 12, padding: 12, marginBottom: 16 }}>
              <Text style={{ color: colors.danger, fontSize: 12, textAlign: 'center' }}>{error}</Text>
            </View>
          ) : null}

          <View className="mb-4">
            <Text style={labelStyle}>Correo Electrónico</Text>
            <TextInput
              value={email}
              onChangeText={setEmail}
              placeholder="ejemplo@correo.com"
              keyboardType="email-address"
              autoCapitalize="none"
              style={inputStyle}
              placeholderTextColor={colors.textSecondary}
              editable={!paramEmail} // Disable if passed from previous screen to avoid typos
            />
          </View>

          <View className="mb-4">
            <Text style={labelStyle}>Código de 6 Dígitos</Text>
            <TextInput
              value={token}
              onChangeText={setToken}
              placeholder="123456"
              keyboardType="numeric"
              maxLength={6}
              style={inputStyle}
              placeholderTextColor={colors.textSecondary}
            />
          </View>

          <View className="mb-4">
            <Text style={labelStyle}>Nueva Contraseña</Text>
            <TextInput
              value={newPassword}
              onChangeText={setNewPassword}
              placeholder="••••••••"
              secureTextEntry
              autoCapitalize="none"
              style={inputStyle}
              placeholderTextColor={colors.textSecondary}
            />
          </View>

          <View className="mb-6">
            <Text style={labelStyle}>Confirmar Contraseña</Text>
            <TextInput
              value={confirmPassword}
              onChangeText={setConfirmPassword}
              placeholder="••••••••"
              secureTextEntry
              autoCapitalize="none"
              style={inputStyle}
              placeholderTextColor={colors.textSecondary}
            />
          </View>

          <Pressable
            onPress={handleResetPassword}
            disabled={isLoading}
            style={{ backgroundColor: colors.primary, borderRadius: 12, paddingVertical: 12, alignItems: 'center', justifyContent: 'center', opacity: isLoading ? 0.8 : 1 }}
          >
            {isLoading ? (
              <ActivityIndicator color="white" />
            ) : (
              <Text style={{ color: 'white', fontWeight: 'bold', fontSize: 16 }}>
                Restablecer Contraseña
              </Text>
            )}
          </Pressable>
        </View>

        <View style={{ height: 40 }} />
      </ScrollView>
    </KeyboardAvoidingView>
  );
}
