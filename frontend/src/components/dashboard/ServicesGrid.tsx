// src/components/dashboard/ServicesGrid.tsx
import React from 'react';
import { useTheme } from '@/src/theme/ThemeContext';
import { View, Text, Pressable, Linking } from 'react-native';
import { useRouter } from 'expo-router';
import Feather from '@expo/vector-icons/Feather';
import MaterialCommunityIcons from '@expo/vector-icons/MaterialCommunityIcons';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTranslation } from 'react-i18next';

// A donde lleva cada tarjeta. Antes todas las externas apuntaban a la portada
// de unsaac.edu.pe, asi que siete de los ocho accesos terminaban en la misma
// pagina y ninguno resolvia la duda que prometia.
type Destino =
  | { tipo: 'web'; url: string }
  // Los tres tipos de tutoria no tienen pagina propia en el sitio de la
  // UNSAAC: son categorias del Reglamento de Tutoria Academica, que TutorIA ya
  // tiene indexado. Abren el chat con la pregunta correspondiente.
  | { tipo: 'chat'; promptKey: string }
  | { tipo: 'ruta'; pathname: string };

interface Servicio {
  nameKey: string;
  icon: string;
  iconType: 'Feather' | 'MaterialCommunityIcons' | 'Ionicons';
  bgColor: string;
  destino: Destino;
}

const services: Servicio[] = [
  { nameKey: 'dashboard.academicTutoring', icon: 'book-open', iconType: 'Feather', bgColor: '#9C3FE4', destino: { tipo: 'chat', promptKey: 'dashboard.academicTutoringPrompt' } },
  { nameKey: 'dashboard.personalTutoring', icon: 'heart', iconType: 'Feather', bgColor: '#3B82F6', destino: { tipo: 'chat', promptKey: 'dashboard.personalTutoringPrompt' } },
  { nameKey: 'dashboard.professionalTutoring', icon: 'briefcase', iconType: 'Feather', bgColor: '#8B5CF6', destino: { tipo: 'chat', promptKey: 'dashboard.professionalTutoringPrompt' } },
  { nameKey: 'dashboard.psychologicalSupport', icon: 'brain', iconType: 'MaterialCommunityIcons', bgColor: '#EC4899', destino: { tipo: 'web', url: 'https://www.unsaac.edu.pe/centro-universitario-de-salud/' } },
  { nameKey: 'dashboard.studentWelfare', icon: 'star', iconType: 'Feather', bgColor: '#06B6D4', destino: { tipo: 'web', url: 'https://www.unsaac.edu.pe/bienestar-universitario/' } },
  { nameKey: 'dashboard.internships', icon: 'rocket-outline', iconType: 'Ionicons', bgColor: '#F97316', destino: { tipo: 'web', url: 'https://www.unsaac.edu.pe/convocatorias/' } },
  { nameKey: 'dashboard.studentMobility', icon: 'globe', iconType: 'Feather', bgColor: '#3B82F6', destino: { tipo: 'web', url: 'https://octi.unsaac.edu.pe/movilidad-saliente-outgoing/' } },
  { nameKey: 'dashboard.feedback', icon: 'message-square', iconType: 'Feather', bgColor: '#9333EA', destino: { tipo: 'ruta', pathname: '/(estudiante)/retroalimentacion-quiz' } },
];

export function ServicesGrid() {
  const { colors } = useTheme();
  const { t } = useTranslation();
  const router = useRouter();

  const renderIcon = (type: string, name: string) => {
    const size = 22;
    const color = 'white';
    if (type === 'Feather') {
      return <Feather name={name as any} size={size} color={color} />;
    }
    if (type === 'MaterialCommunityIcons') {
      return <MaterialCommunityIcons name={name as any} size={size} color={color} />;
    }
    if (type === 'Ionicons') {
      return <Ionicons name={name as any} size={size} color={color} />;
    }
    return null;
  };

  const handlePress = (serv: Servicio) => {
    const destino = serv.destino;
    switch (destino.tipo) {
      case 'web':
        Linking.openURL(destino.url).catch((err) => {
          console.error("Failed to open URL:", err);
        });
        break;
      case 'chat':
        router.push({
          pathname: '/(estudiante)/tutoria',
          params: { pregunta: t(destino.promptKey) },
        } as any);
        break;
      case 'ruta':
        router.push(destino.pathname as any);
        break;
    }
  };

  return (
    <View style={{ paddingHorizontal: 24, marginBottom: 24 }}>
      <View style={{
        marginBottom: 16,
      }}>
        <Text style={{ fontSize: 17, fontWeight: 'bold', color: colors.text }}>
          {t('dashboard.servicesTitle')}
        </Text>
      </View>

      <View style={{
        flexDirection: 'row',
        flexWrap: 'wrap',
        justifyContent: 'space-between',
      }}>
        {services.map((serv, index) => (
          <Pressable
            key={index}
            onPress={() => handlePress(serv)}
            style={{
              width: '23%',
              alignItems: 'center',
              marginBottom: 20,
            }}
          >
            <View
              style={{
                width: 56,
                height: 56,
                borderRadius: 16,
                backgroundColor: serv.bgColor,
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: 8,
                shadowColor: '#000',
                shadowOffset: { width: 0, height: 2 },
                shadowOpacity: 0.08,
                shadowRadius: 4,
                elevation: 2,
              }}
            >
              {renderIcon(serv.iconType, serv.icon)}
            </View>
            <Text 
              style={{
                fontSize: 10,
                fontWeight: '600',
                color: colors.textSecondary,
                textAlign: 'center',
                lineHeight: 13,
                width: '100%',
              }}
              numberOfLines={2}
            >
              {t(serv.nameKey)}
            </Text>
          </Pressable>
        ))}
      </View>
    </View>
  );
}
