// src/components/dashboard/ServicesGrid.tsx
import React from 'react';
import { View, Text, Pressable } from 'react-native';
import { useRouter } from 'expo-router';

const services = [
  { name: 'Tutoría Académica', icon: '📖', color: 'bg-purple-100 text-purple-600', iconColor: '#9C3FE4' },
  { name: 'Tutoría Personal', icon: '💙', color: 'bg-blue-100 text-blue-600', iconColor: '#1E90FF' },
  { name: 'Tutoría Profesional', icon: '💼', color: 'bg-indigo-100 text-indigo-600', iconColor: '#9333EA' },
  { name: 'Apoyo Psicológico', icon: '🧠', color: 'bg-pink-100 text-pink-500', iconColor: '#EC4899' },
  { name: 'Bienestar Universitario', icon: '⭐', color: 'bg-cyan-100 text-cyan-600', iconColor: '#06B6D4' },
  { name: 'Prácticas Preprofesionales', icon: '🚀', color: 'bg-orange-100 text-orange-600', iconColor: '#F97316' },
  { name: 'Movilidad Estudiantil', icon: '🌐', color: 'bg-sky-100 text-sky-600', iconColor: '#3B82F6' },
  { name: 'Retroalimentación', icon: '💬', color: 'bg-purple-100 text-purple-600', iconColor: '#A855F7' },
];

export function ServicesGrid() {
  const router = useRouter();

  return (
    <View className="px-6 mb-6">
      <View className="flex-row justify-between items-center mb-4">
        <Text className="text-[17px] font-bold text-[#1E1E2F]">Explora servicios</Text>
        <Pressable>
          <Text className="text-sm font-semibold text-[#9A3BEE]">Ver todas</Text>
        </Pressable>
      </View>

      <View className="flex-row flex-wrap justify-between">
        {services.map((serv, index) => (
          <Pressable
            key={index}
            onPress={() => router.push('/(tabs)/calendar')}
            className="w-[22%] items-center mb-5"
          >
            <View
              className="w-14 h-14 rounded-[22px] items-center justify-center mb-2 shadow-sm"
              style={{
                backgroundColor:
                  serv.name.includes('Académica') ? '#9C3FE4' :
                  serv.name.includes('Personal') ? '#3B82F6' :
                  serv.name.includes('Profesional') ? '#8B5CF6' :
                  serv.name.includes('Psicológico') ? '#EC4899' :
                  serv.name.includes('Bienestar') ? '#06B6D4' :
                  serv.name.includes('Prácticas') ? '#F97316' :
                  serv.name.includes('Movilidad') ? '#3B82F6' : '#9333EA'
              }}
            >
              <Text className="text-white text-2xl font-bold">
                {serv.name.includes('Académica') ? '📖' :
                 serv.name.includes('Personal') ? '💙' :
                 serv.name.includes('Profesional') ? '💼' :
                 serv.name.includes('Psicológico') ? '🧠' :
                 serv.name.includes('Bienestar') ? '⭐' :
                 serv.name.includes('Prácticas') ? '🚀' :
                 serv.name.includes('Movilidad') ? '🌐' : '💬'}
              </Text>
            </View>
            <Text className="text-[10px] font-semibold text-[#4b4b60] text-center leading-3" numberOfLines={2}>
              {serv.name}
            </Text>
          </Pressable>
        ))}
      </View>
    </View>
  );
}
