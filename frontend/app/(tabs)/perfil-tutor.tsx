// app/(tabs)/perfil-tutor.tsx
import React from 'react';
import { View, Text, ScrollView, Pressable } from 'react-native';
import { useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Feather from '@expo/vector-icons/Feather';
import Ionicons from '@expo/vector-icons/Ionicons';

const PURPLE = '#9A3BEE';
const PURPLE_LIGHT = '#F3E8FF';

/* ─── Datos del tutor (estáticos por ahora) ───────────────── */
const TUTOR = {
  name: 'Ing. Ana Torres',
  role: 'Docente Tutor',
  email: 'ana.torres@unsaac.edu.pe',
  school: 'Ingeniería Informática y de Sistemas',
  specialty: 'Tutoría académica y acompañamiento estudiantil',
  schedule: 'Lunes a viernes, 9:00 AM - 1:00 PM',
  modality: 'Presencial y virtual',
  description:
    'Brinda orientación académica, seguimiento del progreso y acompañamiento durante el semestre.',
};

/* ─── Filas de información ────────────────────────────────── */
const infoRows = [
  {
    iconName: 'mail' as const,
    label: 'Correo institucional',
    value: TUTOR.email,
  },
  {
    iconName: 'award' as const,
    label: 'Escuela / área',
    value: TUTOR.school,
  },
  {
    iconName: 'star' as const,
    label: 'Especialidad',
    value: TUTOR.specialty,
  },
  {
    iconName: 'clock' as const,
    label: 'Horario de atención',
    value: TUTOR.schedule,
  },
  {
    iconName: 'monitor' as const,
    label: 'Modalidad',
    value: TUTOR.modality,
  },
  {
    iconName: 'file-text' as const,
    label: 'Breve descripción',
    value: TUTOR.description,
  },
];

export default function PerfilTutorScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const paddingTop = Math.max(insets.top, 16);

  return (
    <ScrollView
      style={{ flex: 1, backgroundColor: '#F8F7FC' }}
      contentContainerStyle={{ paddingBottom: 130 }}
      showsVerticalScrollIndicator={false}
    >
      {/* ─── Encabezado morado ─────────────────────────────── */}
      <View
        style={{
          backgroundColor: PURPLE,
          paddingTop: paddingTop + 16,
          paddingBottom: 56,
          paddingHorizontal: 24,
          borderBottomLeftRadius: 0,
          borderBottomRightRadius: 0,
        }}
      >
        {/* Fila: flecha + título */}
        <View style={{ flexDirection: 'row', alignItems: 'center' }}>
          <Pressable
            onPress={() => router.replace('/(tabs)/profile' as any)}
            style={{ marginRight: 16 }}
            hitSlop={{ top: 12, bottom: 12, left: 12, right: 12 }}
          >
            <Feather name="arrow-left" size={24} color="white" />
          </Pressable>
          <Text style={{ fontSize: 20, fontWeight: 'bold', color: 'white' }}>
            Perfil de tutor/a
          </Text>
        </View>
      </View>

      {/* ─── Tarjeta principal del tutor ───────────────────── */}
      <View style={{ paddingHorizontal: 20, marginTop: -36, marginBottom: 20 }}>
        <View
          style={{
            backgroundColor: 'white',
            borderRadius: 24,
            padding: 20,
            flexDirection: 'row',
            alignItems: 'center',
            shadowColor: '#000',
            shadowOffset: { width: 0, height: 4 },
            shadowOpacity: 0.08,
            shadowRadius: 12,
            elevation: 5,
          }}
        >
          {/* Avatar circular morado claro */}
          <View
            style={{
              width: 72,
              height: 72,
              borderRadius: 36,
              backgroundColor: '#D8B4FE',
              marginRight: 16,
            }}
          />
          <View style={{ flex: 1 }}>
            <Text style={{ fontSize: 18, fontWeight: 'bold', color: '#111130' }}>
              {TUTOR.name}
            </Text>
            <Text style={{ fontSize: 13, color: '#8E8EA0', marginTop: 4, fontWeight: '500' }}>
              {TUTOR.role}
            </Text>
          </View>
        </View>
      </View>

      {/* ─── Tarjeta de información ────────────────────────── */}
      <View style={{ paddingHorizontal: 20, marginBottom: 16 }}>
        <View
          style={{
            backgroundColor: 'white',
            borderRadius: 24,
            borderWidth: 1,
            borderColor: '#EEEDFE',
            shadowColor: '#000',
            shadowOffset: { width: 0, height: 2 },
            shadowOpacity: 0.04,
            shadowRadius: 6,
            elevation: 2,
            overflow: 'hidden',
          }}
        >
          {infoRows.map((row, index) => (
            <View key={index}>
              {/* Fila de información */}
              <View
                style={{
                  flexDirection: 'row',
                  alignItems: 'flex-start',
                  paddingHorizontal: 16,
                  paddingVertical: 16,
                }}
              >
                {/* Ícono en recuadro morado claro */}
                <View
                  style={{
                    width: 42,
                    height: 42,
                    borderRadius: 14,
                    backgroundColor: PURPLE_LIGHT,
                    alignItems: 'center',
                    justifyContent: 'center',
                    marginRight: 14,
                    flexShrink: 0,
                  }}
                >
                  <Feather name={row.iconName} size={20} color={PURPLE} />
                </View>
                {/* Textos */}
                <View style={{ flex: 1 }}>
                  <Text style={{ fontSize: 14, fontWeight: '700', color: '#1E1E2F', marginBottom: 3 }}>
                    {row.label}
                  </Text>
                  <Text style={{ fontSize: 13, color: '#8E8EA0', lineHeight: 18 }}>
                    {row.value}
                  </Text>
                </View>
              </View>
              {/* Divisor entre filas */}
              {index < infoRows.length - 1 && (
                <View
                  style={{
                    height: 1,
                    backgroundColor: '#F3F4F6',
                    marginLeft: 72,
                    marginRight: 16,
                  }}
                />
              )}
            </View>
          ))}
        </View>
      </View>
    </ScrollView>
  );
}
