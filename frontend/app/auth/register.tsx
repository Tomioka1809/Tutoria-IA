import React, { useState } from 'react';
import { View, TextInput, Text, Pressable, ActivityIndicator, KeyboardAvoidingView, Platform, ScrollView } from 'react-native';
import { useRouter, Link } from 'expo-router';
import client from '../../src/api/client';

export default function RegisterScreen() {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [studentCode, setStudentCode] = useState('');
  const [school, setSchool] = useState('');
  const [role, setRole] = useState<'estudiante' | 'tutor'>('estudiante');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();

  const handleRegister = async () => {
    if (!fullName || !email || !password) {
      setError('Por favor, ingresa tu nombre completo, correo y contraseña.');
      return;
    }
    if (password.length < 6) {
      setError('La contraseña debe tener al menos 6 caracteres.');
      return;
    }
    setError('');
    setIsLoading(true);
    try {
      await client.post('/auth/register', {
        full_name: fullName.trim(),
        email: email.trim().toLowerCase(),
        student_code: studentCode.trim() || undefined,
        school: school.trim() || undefined,
        role: role,
        password: password,
      });

      setSuccess(true);
      setTimeout(() => {
        router.replace('/auth/login');
      }, 2000);
    } catch (e: any) {
      console.error(e);
      setError(
        e.response?.data?.detail || 
        'Hubo un problema al crear la cuenta. Intenta de nuevo.'
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
      <ScrollView contentContainerStyle={{ flexGrow: 1, justifyContent: 'center' }} className="px-6 py-12">
        <View className="items-center mb-6">
          <Text className="text-4xl mb-1">🦖</Text>
          <Text className="text-2xl font-bold text-[#26215C]">Crear Cuenta</Text>
          <Text className="text-xs text-[#7F77DD] text-center mt-1">
            Únete a TutorIA y potencia tu aprendizaje
          </Text>
        </View>

        <View className="bg-white rounded-3xl p-6 shadow-md border border-[#7F77DD]/20">
          {success ? (
            <View className="bg-green-50 border border-green-200 rounded-xl p-4 mb-4 items-center">
              <Text className="text-green-600 font-bold mb-1 text-center">¡Registro exitoso!</Text>
              <Text className="text-green-600 text-xs text-center">Redirigiéndote al inicio de sesión...</Text>
            </View>
          ) : null}

          {error ? (
            <View className="bg-red-50 border border-red-200 rounded-xl p-3 mb-4">
              <Text className="text-red-600 text-xs text-center">{error}</Text>
            </View>
          ) : null}

          <View className="mb-3">
            <Text className="text-xs text-[#26215C] font-semibold mb-1 ml-1">Nombre Completo</Text>
            <TextInput
              value={fullName}
              onChangeText={setFullName}
              placeholder="Juan Pérez"
              className="bg-[#EEEDFE]/50 border border-[#7F77DD]/30 rounded-xl px-4 py-2.5 text-[#26215C]"
              placeholderTextColor="#26215C/40"
            />
          </View>

          <View className="mb-3">
            <Text className="text-xs text-[#26215C] font-semibold mb-1 ml-1">Correo Electrónico</Text>
            <TextInput
              value={email}
              onChangeText={setEmail}
              placeholder="juan.perez@universidad.edu"
              keyboardType="email-address"
              autoCapitalize="none"
              className="bg-[#EEEDFE]/50 border border-[#7F77DD]/30 rounded-xl px-4 py-2.5 text-[#26215C]"
              placeholderTextColor="#26215C/40"
            />
          </View>

          {/* Role selection tab */}
          <View className="mb-3">
            <Text className="text-xs text-[#26215C] font-semibold mb-2 ml-1">Rol</Text>
            <View className="flex-row bg-[#EEEDFE]/50 border border-[#7F77DD]/30 rounded-xl p-1">
              <Pressable
                onPress={() => setRole('estudiante')}
                className={`flex-1 py-2 rounded-lg items-center ${role === 'estudiante' ? 'bg-[#7F77DD]' : ''}`}
              >
                <Text className={`font-semibold text-xs ${role === 'estudiante' ? 'text-white' : 'text-[#26215C]/60'}`}>
                  Estudiante
                </Text>
              </Pressable>
              <Pressable
                onPress={() => setRole('tutor')}
                className={`flex-1 py-2 rounded-lg items-center ${role === 'tutor' ? 'bg-[#7F77DD]' : ''}`}
              >
                <Text className={`font-semibold text-xs ${role === 'tutor' ? 'text-white' : 'text-[#26215C]/60'}`}>
                  Tutor
                </Text>
              </Pressable>
            </View>
          </View>

          {role === 'estudiante' ? (
            <View className="mb-3">
              <Text className="text-xs text-[#26215C] font-semibold mb-1 ml-1">Código de Estudiante (Opcional)</Text>
              <TextInput
                value={studentCode}
                onChangeText={setStudentCode}
                placeholder="202612345"
                className="bg-[#EEEDFE]/50 border border-[#7F77DD]/30 rounded-xl px-4 py-2.5 text-[#26215C]"
                placeholderTextColor="#26215C/40"
              />
            </View>
          ) : null}

          <View className="mb-3">
            <Text className="text-xs text-[#26215C] font-semibold mb-1 ml-1">Facultad / Escuela (Opcional)</Text>
            <TextInput
              value={school}
              onChangeText={setSchool}
              placeholder="Ingeniería de Sistemas"
              className="bg-[#EEEDFE]/50 border border-[#7F77DD]/30 rounded-xl px-4 py-2.5 text-[#26215C]"
              placeholderTextColor="#26215C/40"
            />
          </View>

          <View className="mb-5">
            <Text className="text-xs text-[#26215C] font-semibold mb-1 ml-1">Contraseña</Text>
            <TextInput
              value={password}
              onChangeText={setPassword}
              placeholder="Mínimo 6 caracteres"
              secureTextEntry
              autoCapitalize="none"
              className="bg-[#EEEDFE]/50 border border-[#7F77DD]/30 rounded-xl px-4 py-2.5 text-[#26215C]"
              placeholderTextColor="#26215C/40"
            />
          </View>

          <Pressable
            onPress={handleRegister}
            disabled={isLoading || success}
            className={`bg-[#7F77DD] rounded-xl py-3 items-center justify-center shadow-sm ${isLoading ? 'opacity-80' : ''}`}
          >
            {isLoading ? (
              <ActivityIndicator color="white" />
            ) : (
              <Text className="text-white font-bold text-base">Registrarse</Text>
            )}
          </Pressable>
        </View>

        <View className="flex-row justify-center mt-6">
          <Text className="text-sm text-[#26215C]">¿Ya tienes una cuenta? </Text>
          <Link href="/auth/login" asChild>
            <Pressable>
              <Text className="text-sm font-bold text-[#7F77DD]">Inicia sesión</Text>
            </Pressable>
          </Link>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}
