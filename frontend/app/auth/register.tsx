import React, { useState } from 'react';
import { View, TextInput, Text, Pressable, ActivityIndicator, KeyboardAvoidingView, Platform, ScrollView, Alert } from 'react-native';
import { useRouter, Link } from 'expo-router';
import client from '../../src/api/client';
import { useTranslation } from 'react-i18next';
import { useTheme } from '@/src/theme/ThemeContext';
import { TutorIAAvatar } from '@/src/components/tutoria/TutorIAAvatar';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

export default function RegisterScreen() {
  const { t } = useTranslation();
  const { colors } = useTheme();
  const insets = useSafeAreaInsets();

  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<'estudiante' | 'tutor'>('estudiante');

  // Profile Fields
  const [phoneNumber, setPhoneNumber] = useState('');
  
  // Student
  const [studentCode, setStudentCode] = useState('');
  const [currentSemester, setCurrentSemester] = useState('');
  const [academicStatus, setAcademicStatus] = useState('');

  // Tutor
  const [tutorCode, setTutorCode] = useState('');
  const [expertiseAreas, setExpertiseAreas] = useState('');
  const [officeLocation, setOfficeLocation] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();

  const handleRegister = async () => {
    if (!fullName || !email || !password) {
      setError(t('auth.register.emptyFields') || 'Por favor, ingresa tu nombre completo, correo y contraseña.');
      return;
    }
    if (password.length < 6) {
      setError(t('auth.register.passwordLength') || 'La contraseña debe tener al menos 6 caracteres.');
      return;
    }
    setError('');
    setIsLoading(true);
    try {
      await client.post('/auth/register', {
        full_name: fullName.trim(),
        email: email.trim().toLowerCase(),
        password: password,
        role: role,
        phone_number: phoneNumber.trim() || undefined,
        
        // Student
        student_code: role === 'estudiante' ? (studentCode.trim() || undefined) : undefined,
        current_semester: role === 'estudiante' && currentSemester ? parseInt(currentSemester, 10) : undefined,
        academic_status: role === 'estudiante' ? (academicStatus.trim() || undefined) : undefined,
        
        // Tutor
        tutor_code: role === 'tutor' ? (tutorCode.trim() || undefined) : undefined,
        expertise_areas: role === 'tutor' ? (expertiseAreas.trim() || undefined) : undefined,
        office_location: role === 'tutor' ? (officeLocation.trim() || undefined) : undefined,
      });

      setSuccess(true);
      setTimeout(() => {
        router.replace('/auth/login');
      }, 2000);
    } catch (e: any) {
      let errorMessage = 'Hubo un problema al crear la cuenta. Intenta de nuevo.';
      if (!e.response) {
        errorMessage = 'No se pudo conectar con el servidor. Verifica tu conexión a internet.';
      } else if (e.response.status === 409) {
        errorMessage = 'Este correo ya está registrado.';
      } else if (e.response.status === 422) {
        errorMessage = 'Los datos ingresados son inválidos o están incompletos.';
      } else if (e.response.data?.detail) {
        errorMessage = e.response.data.detail;
      }
      
      Alert.alert('Error de Registro', errorMessage);
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const inputStyle = { backgroundColor: colors.background, borderColor: colors.border, borderWidth: 1, borderRadius: 12, paddingHorizontal: 16, paddingVertical: 10, color: colors.text };
  const labelStyle = { color: colors.text, fontSize: 12, fontWeight: '600' as const, marginBottom: 4, marginLeft: 4 };

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      style={{ flex: 1, backgroundColor: colors.background }}
    >
      <ScrollView
        contentContainerStyle={{
          flexGrow: 1,
          justifyContent: 'center',
          paddingBottom: Math.max(insets.bottom + 24, 48),
        }}
        className="px-6 pt-12"
      >
        <View className="items-center mb-6">
          <View style={{ marginBottom: 12 }}>
            <TutorIAAvatar size={64} />
          </View>
          <Text style={{ color: colors.text, fontSize: 24, fontWeight: 'bold' }}>
            {t('auth.register.title') || 'Crear Cuenta'}
          </Text>
          <Text style={{ color: colors.primary, fontSize: 12, textAlign: 'center', marginTop: 4 }}>
            {t('auth.register.subtitle') || 'Únete a TutorIA y potencia tu aprendizaje'}
          </Text>
        </View>

        <View style={{ backgroundColor: colors.surface, borderRadius: 24, padding: 24, shadowColor: '#000', shadowOffset: {width:0,height:2}, shadowOpacity:0.1, elevation:4 }}>
          {success ? (
            <View style={{ backgroundColor: colors.success + '20', borderColor: colors.success + '40', borderWidth: 1, borderRadius: 12, padding: 16, marginBottom: 16, alignItems: 'center' }}>
              <Text style={{ color: colors.success, fontWeight: 'bold', marginBottom: 4 }}>
                {t('auth.register.successTitle') || '¡Registro exitoso!'}
              </Text>
              <Text style={{ color: colors.success, fontSize: 12 }}>
                {t('auth.register.successMsg') || 'Redirigiéndote al inicio de sesión...'}
              </Text>
            </View>
          ) : null}

          {error ? (
            <View style={{ backgroundColor: colors.danger + '20', borderColor: colors.danger + '40', borderWidth: 1, borderRadius: 12, padding: 12, marginBottom: 16 }}>
              <Text style={{ color: colors.danger, fontSize: 12, textAlign: 'center' }}>{error}</Text>
            </View>
          ) : null}

          <View className="mb-3">
            <Text style={labelStyle}>{t('auth.register.fullName') || 'Nombre Completo'}</Text>
            <TextInput
              value={fullName}
              onChangeText={setFullName}
              placeholder="Juan Pérez"
              style={inputStyle}
              placeholderTextColor={colors.textSecondary}
            />
          </View>

          <View className="mb-3">
            <Text style={labelStyle}>{t('auth.register.email') || 'Correo Electrónico'}</Text>
            <TextInput
              value={email}
              onChangeText={setEmail}
              placeholder="juan.perez@universidad.edu"
              keyboardType="email-address"
              autoCapitalize="none"
              style={inputStyle}
              placeholderTextColor={colors.textSecondary}
            />
          </View>

          {/* Role selection tab */}
          <View className="mb-3">
            <Text style={labelStyle}>{t('auth.register.role') || 'Rol'}</Text>
            <View style={{ flexDirection: 'row', backgroundColor: colors.background, borderColor: colors.border, borderWidth: 1, borderRadius: 12, padding: 4 }}>
              <Pressable
                onPress={() => setRole('estudiante')}
                style={{ flex: 1, paddingVertical: 8, borderRadius: 8, alignItems: 'center', backgroundColor: role === 'estudiante' ? colors.primary : 'transparent' }}
              >
                <Text style={{ fontWeight: '600', fontSize: 12, color: role === 'estudiante' ? 'white' : colors.textSecondary }}>
                  {t('auth.register.student') || 'Estudiante'}
                </Text>
              </Pressable>
              <Pressable
                onPress={() => setRole('tutor')}
                style={{ flex: 1, paddingVertical: 8, borderRadius: 8, alignItems: 'center', backgroundColor: role === 'tutor' ? colors.primary : 'transparent' }}
              >
                <Text style={{ fontWeight: '600', fontSize: 12, color: role === 'tutor' ? 'white' : colors.textSecondary }}>
                  {t('auth.register.tutor') || 'Tutor'}
                </Text>
              </Pressable>
            </View>
          </View>

          <View className="mb-3">
            <Text style={labelStyle}>{t('auth.register.phone') || 'Teléfono (Opcional)'}</Text>
            <TextInput
              value={phoneNumber}
              onChangeText={setPhoneNumber}
              placeholder="+51 987654321"
              keyboardType="phone-pad"
              style={inputStyle}
              placeholderTextColor={colors.textSecondary}
            />
          </View>

          {role === 'estudiante' ? (
            <>
              <View className="mb-3">
                <Text style={labelStyle}>{t('auth.register.studentCode') || 'Código de Estudiante'}</Text>
                <TextInput
                  value={studentCode}
                  onChangeText={setStudentCode}
                  placeholder="202612345"
                  style={inputStyle}
                  placeholderTextColor={colors.textSecondary}
                />
              </View>
              <View className="mb-3">
                <Text style={labelStyle}>{t('auth.register.semester') || 'Semestre Actual (Opcional)'}</Text>
                <TextInput
                  value={currentSemester}
                  onChangeText={setCurrentSemester}
                  placeholder="Ej: 5"
                  keyboardType="numeric"
                  style={inputStyle}
                  placeholderTextColor={colors.textSecondary}
                />
              </View>
              <View className="mb-3">
                <Text style={labelStyle}>{t('auth.register.academicStatus') || 'Estado Académico (Opcional)'}</Text>
                <TextInput
                  value={academicStatus}
                  onChangeText={setAcademicStatus}
                  placeholder="Regular, Observado..."
                  style={inputStyle}
                  placeholderTextColor={colors.textSecondary}
                />
              </View>
            </>
          ) : null}

          {role === 'tutor' ? (
            <>
              <View className="mb-3">
                <Text style={labelStyle}>{t('auth.register.tutorCode') || 'Código de Tutor'}</Text>
                <TextInput
                  value={tutorCode}
                  onChangeText={setTutorCode}
                  placeholder="T-202612"
                  style={inputStyle}
                  placeholderTextColor={colors.textSecondary}
                />
              </View>
              <View className="mb-3">
                <Text style={labelStyle}>{t('auth.register.expertise') || 'Áreas de Especialidad (Opcional)'}</Text>
                <TextInput
                  value={expertiseAreas}
                  onChangeText={setExpertiseAreas}
                  placeholder="Matemáticas, Física..."
                  style={inputStyle}
                  placeholderTextColor={colors.textSecondary}
                />
              </View>
              <View className="mb-3">
                <Text style={labelStyle}>{t('auth.register.office') || 'Ubicación de Oficina (Opcional)'}</Text>
                <TextInput
                  value={officeLocation}
                  onChangeText={setOfficeLocation}
                  placeholder="Pabellón A, Aula 102"
                  style={inputStyle}
                  placeholderTextColor={colors.textSecondary}
                />
              </View>
            </>
          ) : null}

          <View className="mb-5">
            <Text style={labelStyle}>{t('auth.register.password') || 'Contraseña'}</Text>
            <TextInput
              value={password}
              onChangeText={setPassword}
              placeholder="Mínimo 6 caracteres"
              secureTextEntry
              autoCapitalize="none"
              style={inputStyle}
              placeholderTextColor={colors.textSecondary}
            />
          </View>

          <Pressable
            onPress={handleRegister}
            disabled={isLoading || success}
            style={{ backgroundColor: colors.primary, borderRadius: 12, paddingVertical: 12, alignItems: 'center', justifyContent: 'center', opacity: (isLoading || success) ? 0.8 : 1 }}
          >
            {isLoading ? (
              <ActivityIndicator color="white" />
            ) : (
              <Text style={{ color: 'white', fontWeight: 'bold', fontSize: 16 }}>
                {t('auth.register.button') || 'Registrarse'}
              </Text>
            )}
          </Pressable>
        </View>

        <View className="flex-row justify-center mt-6">
          <Text style={{ fontSize: 14, color: colors.text }}>
            {t('auth.register.hasAccount') || '¿Ya tienes una cuenta? '}
          </Text>
          <Link href="/auth/login" asChild>
            <Pressable>
              <Text style={{ fontSize: 14, fontWeight: 'bold', color: colors.primary }}>
                {t('auth.register.loginLink') || 'Inicia sesión'}
              </Text>
            </Pressable>
          </Link>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}
