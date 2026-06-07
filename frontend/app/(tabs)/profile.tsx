import React, { useState, useEffect } from 'react';
import { View, Text, ScrollView, Pressable, ActivityIndicator, Image } from 'react-native';
import { useAuthStore } from '../../src/store/auth';
import client from '../../src/api/client';
import { TutorAssignment } from '../../src/types';

export default function ProfileScreen() {
  const { user, logout } = useAuthStore();
  const [assignedTutors, setAssignedTutors] = useState<TutorAssignment[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (user?.role === 'estudiante') {
      fetchAssignedTutor();
    }
  }, []);

  const fetchAssignedTutor = async () => {
    setIsLoading(true);
    try {
      const response = await client.get('/tutors/assigned');
      setAssignedTutors(response.data);
    } catch (e) {
      console.error('Failed to load assigned tutor', e);
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
  };

  const menuItems = [
    { name: 'Configuración', icon: '⚙️', action: () => alert('Ajustes en desarrollo.') },
    { name: 'Privacidad', icon: '🔒', action: () => alert('Privacidad en desarrollo.') },
    { name: 'Centro de ayuda', icon: '❓', action: () => alert('Centro de ayuda en desarrollo.') },
    { name: 'Cerrar sesión', icon: '➔', action: handleLogout, color: 'text-red-500' },
  ];

  return (
    <ScrollView className="flex-1 bg-[#F5F5FB]" contentContainerStyle={{ paddingBottom: 60 }} showsVerticalScrollIndicator={false}>
      {/* Purple banner and Overlay Profile card */}
      <View className="bg-[#9A3BEE] pt-16 pb-24 px-6 rounded-b-[40px] relative">
        <View className="flex-row justify-between items-center mb-6">
          <Text className="text-white text-[20px] font-bold">Perfil</Text>
          <Pressable onPress={() => alert('Configuración general')}>
            <Text className="text-white text-xl">⚙️</Text>
          </Pressable>
        </View>
        
        {/* Profile Overlay Card */}
        <View className="absolute left-6 right-6 bottom-[-60px] bg-white rounded-3xl p-5 border border-[#EEEDFE] shadow-md flex-row items-center">
          <View className="w-16 h-16 rounded-full bg-[#E2E8F0] items-center justify-center mr-4">
            <Text className="text-3xl">👤</Text>
          </View>
          <View className="flex-1">
            <Text className="text-lg font-bold text-[#111130]">{user?.full_name || 'Sebastián Quispe'}</Text>
            <Text className="text-xs text-[#8E8EA0] font-medium mt-1">
              Código: {user?.student_code || '2123456'}
            </Text>
            <Text className="text-xs text-[#8E8EA0] font-medium mt-0.5" numberOfLines={1}>
              {user?.school || 'Ingeniería Informática y de Sistemas'}
            </Text>
            <Text className="text-[11px] text-[#8E8EA0] font-medium mt-0.5">
              VI Semestre
            </Text>
          </View>
        </View>
      </View>

      {/* Spacer to handle the overlay card offset */}
      <View className="h-20" />

      {/* Mi tutor Section matching mockup */}
      {user?.role === 'estudiante' ? (
        <View className="px-6 mb-6">
          <Text className="text-[15px] font-bold text-[#1E1E2F] mb-3">Mi tutor</Text>
          
          <View className="bg-white border border-[#EEEDFE] rounded-3xl p-4 shadow-sm flex-row items-center justify-between">
            <View className="flex-row items-center flex-1">
              <View className="w-10 h-10 rounded-full bg-[#C084FC]/30 items-center justify-center mr-3">
                <Text className="text-xl">👨‍🏫</Text>
              </View>
              <View className="flex-1">
                <Text className="text-sm font-bold text-[#1E1E2F]">
                  {assignedTutors.length > 0 && assignedTutors[0]?.tutor ? assignedTutors[0].tutor.full_name : 'Ing. Ana Torres'}
                </Text>
                <Text className="text-xs text-[#8E8EA0] mt-0.5 font-medium">Docente Tutor</Text>
              </View>
            </View>

            <Pressable onPress={() => alert(`Contacto: ${assignedTutors.length > 0 && assignedTutors[0]?.tutor ? assignedTutors[0].tutor.email : 'ana.torres@universidad.edu'}`)}>
              <Text className="text-xs font-bold text-[#9A3BEE]">Ver perfil</Text>
            </Pressable>
          </View>
        </View>
      ) : null}

      {/* Vertical buttons list stack matching mockup */}
      <View className="px-6">
        {menuItems.map((item, index) => (
          <Pressable
            key={index}
            onPress={item.action}
            className="bg-white border border-[#EEEDFE] rounded-2xl px-5 py-4.5 mb-3 shadow-sm flex-row justify-between items-center"
          >
            <View className="flex-row items-center">
              <View className="w-8 h-8 rounded-full bg-[#F5F5FB] items-center justify-center mr-3">
                <Text className="text-base">{item.icon}</Text>
              </View>
              <Text className={`text-sm font-bold ${item.color || 'text-[#1E1E2F]'}`}>{item.name}</Text>
            </View>
            <Text className="text-base text-[#8E8EA0] font-semibold">➔</Text>
          </Pressable>
        ))}
      </View>
    </ScrollView>
  );
}
