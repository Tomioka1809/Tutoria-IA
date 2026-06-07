import React, { useEffect } from 'react';
import { View, Text, ScrollView, Pressable, RefreshControl } from 'react-native';
import { useRouter } from 'expo-router';
import { useAuthStore } from '../../src/store/auth';
import { useStreakStore } from '../../src/store/streak';
import { useSessionStore } from '../../src/store/session';

export default function DashboardScreen() {
  const router = useRouter();
  const { user } = useAuthStore();
  const { streak, fetchStreak, isLoading: isStreakLoading } = useStreakStore();
  const { sessions, fetchSessions, isLoading: isSessionsLoading } = useSessionStore();

  const onRefresh = () => {
    if (user?.role === 'estudiante') {
      fetchStreak();
    }
    fetchSessions();
  };

  useEffect(() => {
    if (user?.role === 'estudiante') {
      fetchStreak();
    }
    fetchSessions();
  }, []);

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

  return (
    <ScrollView
      className="flex-1 bg-[#F5F5FB]"
      contentContainerStyle={{ paddingBottom: 60 }}
      refreshControl={
        <RefreshControl
          refreshing={isStreakLoading || isSessionsLoading}
          onRefresh={onRefresh}
          colors={['#9A3BEE']}
        />
      }
    >
      {/* Header section with Greeting */}
      <View className="px-6 pt-16 pb-6 bg-[#F5F5FB]">
        <Text className="text-[32px] font-extrabold text-[#111130] tracking-tight">
          ¡Hola, {user?.full_name.split(' ')[0]}! 👋
        </Text>
        <Text className="text-sm text-[#8E8EA0] mt-1 font-medium">
          ¿Qué quieres aprender hoy?
        </Text>
      </View>

      {/* Action Button: Iniciar Chat */}
      <View className="px-6 mb-6">
        <Pressable
          onPress={() => router.push('/(tabs)/tutoria')}
          className="bg-[#9A3BEE] rounded-3xl py-4.5 items-center justify-center shadow-lg shadow-[#9A3BEE]/30"
          style={{ elevation: 5 }}
        >
          <Text className="text-white font-bold text-base">Iniciar Chat</Text>
        </Pressable>
      </View>

      {/* Explora servicios Section */}
      <View className="px-6 mb-6">
        <View className="flex-row justify-between items-center mb-4">
          <Text className="text-[17px] font-bold text-[#1E1E2F]">Explora servicios</Text>
          <Pressable>
            <Text className="text-sm font-semibold text-[#9A3BEE]">Ver todas</Text>
          </Pressable>
        </View>

        {/* 8-Grid Services layout matching mockup */}
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

      {/* Racha de tutorías Section */}
      <View className="px-6">
        <Text className="text-[17px] font-bold text-[#1E1E2F] mb-4">Racha de tutorías</Text>
        
        <View className="bg-white rounded-3xl p-6 border border-[#EEEDFE] shadow-sm items-center">
          <Text className="text-5xl mb-4">🔥</Text>
          <Text className="text-[#F97316] font-extrabold text-2xl tracking-tight text-center">
            {/* Displaying days as per the mockup */}
            ¡{streak?.current_streak || 13} días de racha!
          </Text>
          <Text className="text-[#8E8EA0] text-xs font-semibold text-center mt-2 px-4 leading-4">
            Completa tu siguiente tutoría para aumentar tu racha
          </Text>
        </View>
      </View>
    </ScrollView>
  );
}
