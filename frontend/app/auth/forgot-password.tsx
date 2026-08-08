import React, { useState } from 'react';
import { View, TextInput, Text, Pressable, ActivityIndicator, KeyboardAvoidingView, Platform, ScrollView, Alert } from 'react-native';
import { useRouter } from 'expo-router';
import client from '../../src/api/client';
import { useTheme } from '@/src/theme/ThemeContext';
import { Feather } from '@expo/vector-icons';
import { TutorIAAvatar } from '@/src/components/tutoria/TutorIAAvatar';

export default function ForgotPasswordScreen() {
  const { colors } = useTheme();
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();

  const handleRequestCode = async () => {
    if (!email) {
      setError('Por favor, ingresa tu correo electrónico.');
      return;
    }
    setError('');
    setIsLoading(true);
    try {
      await client.post('/auth/forgot-password', {
        email: email.trim().toLowerCase()
      });

      Alert.alert(
        'Código Enviado',
        'Si el correo corresponde a una cuenta registrada, se generó un código de recuperación de 6 dígitos. En este entorno de desarrollo, revise la consola del backend para verlo.',
        [
          {
            text: 'Entendido',
            onPress: () => {
              router.push({
                pathname: '/auth/reset-password',
                params: { email: email.trim().toLowerCase() }
              });
            }
          }
        ]
      );
    } catch (e: any) {
      // Sin rama para 404: el backend responde igual exista o no la cuenta, y
      // delatarlo aca reabriria la enumeracion de correos registrados.
      let errorMessage = 'Hubo un error al procesar tu solicitud.';
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

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      style={{ flex: 1, backgroundColor: colors.background }}
    >
      <ScrollView contentContainerStyle={{ flexGrow: 1, justifyContent: 'center' }} className="px-6">
        
        {/* Back Button */}
        <Pressable 
          onPress={() => router.back()}
          style={{ position: 'absolute', top: 50, left: 24, zIndex: 10, flexDirection: 'row', alignItems: 'center' }}
        >
          <Feather name="arrow-left" size={24} color={colors.text} />
          <Text style={{ color: colors.text, fontSize: 16, marginLeft: 8, fontWeight: '600' }}>Volver</Text>
        </Pressable>

        <View className="items-center mb-8">
          <View style={{ marginBottom: 12 }}>
            <TutorIAAvatar size={72} />
          </View>
          <Text style={{ color: colors.text, fontSize: 30, fontWeight: 'bold' }}>TutorIA</Text>
          <Text style={{ color: colors.primary, fontSize: 14, textAlign: 'center', marginTop: 4 }}>
            Recuperación de Contraseña
          </Text>
        </View>

        <View style={{ backgroundColor: colors.surface, borderRadius: 24, padding: 24, shadowColor: '#000', shadowOffset: {width:0,height:2}, shadowOpacity:0.1, elevation:4 }}>
          <Text style={{ color: colors.text, fontSize: 20, fontWeight: 'bold', marginBottom: 8, textAlign: 'center' }}>
            ¿Olvidaste tu contraseña?
          </Text>
          <Text style={{ color: colors.textSecondary, fontSize: 14, textAlign: 'center', marginBottom: 24, lineHeight: 20 }}>
            Ingresa tu correo registrado y te enviaremos un código de seguridad de 6 dígitos para restablecerla.
          </Text>
          
          {error ? (
            <View style={{ backgroundColor: colors.danger + '20', borderColor: colors.danger + '40', borderWidth: 1, borderRadius: 12, padding: 12, marginBottom: 16 }}>
              <Text style={{ color: colors.danger, fontSize: 12, textAlign: 'center' }}>{error}</Text>
            </View>
          ) : null}

          <View className="mb-6">
            <Text style={{ color: colors.text, fontSize: 12, fontWeight: '600', marginBottom: 8, marginLeft: 4 }}>
              Correo Electrónico
            </Text>
            <TextInput
              value={email}
              onChangeText={setEmail}
              placeholder="ejemplo@correo.com"
              keyboardType="email-address"
              autoCapitalize="none"
              style={{ backgroundColor: colors.background, borderColor: colors.border, borderWidth: 1, borderRadius: 12, paddingHorizontal: 16, paddingVertical: 12, color: colors.text }}
              placeholderTextColor={colors.textSecondary}
            />
          </View>

          <Pressable
            onPress={handleRequestCode}
            disabled={isLoading}
            style={{ backgroundColor: colors.primary, borderRadius: 12, paddingVertical: 12, alignItems: 'center', justifyContent: 'center', opacity: isLoading ? 0.8 : 1 }}
          >
            {isLoading ? (
              <ActivityIndicator color="white" />
            ) : (
              <Text style={{ color: 'white', fontWeight: 'bold', fontSize: 16 }}>
                Enviar Código
              </Text>
            )}
          </Pressable>
        </View>

        <View style={{ height: 40 }} />
      </ScrollView>
    </KeyboardAvoidingView>
  );
}
