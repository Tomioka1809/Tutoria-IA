import React, { useState } from 'react';
import { View, TextInput, Text, Pressable, ActivityIndicator, KeyboardAvoidingView, Platform, ScrollView } from 'react-native';
import { useRouter, Link } from 'expo-router';
import { useAuthStore } from '../../src/store/auth';
import client from '../../src/api/client';
import { ThemedText } from '../../components/themed-text';
import { ThemedView } from '../../components/themed-view';

export default function LoginScreen() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();
  const setAuth = useAuthStore((state) => state.setAuth);

  const handleLogin = async () => {
    if (!email || !password) {
      setError('Por favor, ingresa tu correo y contraseña.');
      return;
    }
    setError('');
    setIsLoading(true);
    try {
      // 1. Get OAuth2 form data
      const formData = new FormData();
      formData.append('username', email.trim().toLowerCase());
      formData.append('password', password);

      const response = await client.post('/auth/login', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      const { access_token } = response.data;

      // 2. Fetch user details
      const userResponse = await client.get('/auth/me', {
        headers: {
          Authorization: `Bearer ${access_token}`,
        },
      });

      // 3. Set auth state
      setAuth(access_token, userResponse.data);
      router.replace('/(tabs)');
    } catch (e: any) {
      console.error(e);
      setError(
        e.response?.data?.detail || 
        'Error de conexión. Revisa tus credenciales o si el servidor está activo.'
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      className="flex-1 bg-[#EEEDFE]"
    >
      <ScrollView contentContainerStyle={{ flexGrow: 1, justifyContent: 'center' }} className="px-6">
        <View className="items-center mb-8">
          <Text className="text-5xl mb-2">🦖</Text>
          <Text className="text-3xl font-bold text-[#26215C] font-semibold">TutorIA</Text>
          <Text className="text-sm text-[#7F77DD] text-center mt-1">
            Tu tutor inteligente en tu bolsillo
          </Text>
        </View>

        <View className="bg-white rounded-3xl p-6 shadow-md border border-[#7F77DD]/20">
          <Text className="text-xl font-bold text-[#26215C] mb-6 text-center">Iniciar Sesión</Text>
          
          {error ? (
            <View className="bg-red-50 border border-red-200 rounded-xl p-3 mb-4">
              <Text className="text-red-600 text-xs text-center">{error}</Text>
            </View>
          ) : null}

          <View className="mb-4">
            <Text className="text-xs text-[#26215C] font-semibold mb-2 ml-1">Correo Electrónico</Text>
            <TextInput
              value={email}
              onChangeText={setEmail}
              placeholder="ejemplo@correo.com"
              keyboardType="email-address"
              autoCapitalize="none"
              className="bg-[#EEEDFE]/50 border border-[#7F77DD]/30 rounded-xl px-4 py-3 text-[#26215C]"
              placeholderTextColor="#26215C/40"
            />
          </View>

          <View className="mb-6">
            <Text className="text-xs text-[#26215C] font-semibold mb-2 ml-1">Contraseña</Text>
            <TextInput
              value={password}
              onChangeText={setPassword}
              placeholder="••••••••"
              secureTextEntry
              autoCapitalize="none"
              className="bg-[#EEEDFE]/50 border border-[#7F77DD]/30 rounded-xl px-4 py-3 text-[#26215C]"
              placeholderTextColor="#26215C/40"
            />
          </View>

          <Pressable
            onPress={handleLogin}
            disabled={isLoading}
            className={`bg-[#7F77DD] rounded-xl py-3 items-center justify-center shadow-sm ${isLoading ? 'opacity-80' : ''}`}
          >
            {isLoading ? (
              <ActivityIndicator color="white" />
            ) : (
              <Text className="text-white font-bold text-base">Ingresar</Text>
            )}
          </Pressable>
        </View>

        <View className="flex-row justify-center mt-6">
          <Text className="text-sm text-[#26215C]">¿No tienes una cuenta? </Text>
          <Link href="/auth/register" asChild>
            <Pressable>
              <Text className="text-sm font-bold text-[#7F77DD]">Regístrate aquí</Text>
            </Pressable>
          </Link>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}
