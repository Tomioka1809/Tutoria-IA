// src/components/dashboard/ServicesGrid.tsx
import React from 'react';
import { View, Text, Pressable } from 'react-native';
import { useRouter } from 'expo-router';
import Feather from '@expo/vector-icons/Feather';
import MaterialCommunityIcons from '@expo/vector-icons/MaterialCommunityIcons';
import Ionicons from '@expo/vector-icons/Ionicons';

const services = [
  { name: 'Tutoría Académica', icon: 'book-open', iconType: 'Feather', bgColor: '#9C3FE4' },
  { name: 'Tutoría Personal', icon: 'heart', iconType: 'Feather', bgColor: '#3B82F6' },
  { name: 'Tutoría Profesional', icon: 'briefcase', iconType: 'Feather', bgColor: '#8B5CF6' },
  { name: 'Apoyo Psicológico', icon: 'brain', iconType: 'MaterialCommunityIcons', bgColor: '#EC4899' },
  { name: 'Bienestar Universitario', icon: 'star', iconType: 'Feather', bgColor: '#06B6D4' },
  { name: 'Prácticas Preprofesionales', icon: 'rocket-outline', iconType: 'Ionicons', bgColor: '#F97316' },
  { name: 'Movilidad Estudiantil', icon: 'globe', iconType: 'Feather', bgColor: '#3B82F6' },
  { name: 'Retroalimentación', icon: 'message-square', iconType: 'Feather', bgColor: '#9333EA' },
];

export function ServicesGrid() {
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

  return (
    <View style={{ paddingHorizontal: 24, marginBottom: 24 }}>
      <View style={{
        marginBottom: 16,
      }}>
        <Text style={{ fontSize: 17, fontWeight: 'bold', color: '#1E1E2F' }}>
          Explora servicios
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
            onPress={() => router.push('/(tabs)/calendar')}
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
                color: '#4B4B60',
                textAlign: 'center',
                lineHeight: 13,
                width: '100%',
              }}
              numberOfLines={2}
            >
              {serv.name}
            </Text>
          </Pressable>
        ))}
      </View>
    </View>
  );
}
