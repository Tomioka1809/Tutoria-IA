// src/components/profile/AssignedTutorCard.tsx
import React from 'react';
import { View, Text, Pressable } from 'react-native';
import { TutorAssignment } from '@/src/types';

interface AssignedTutorCardProps {
  assignedTutors: TutorAssignment[];
}

export function AssignedTutorCard({ assignedTutors }: AssignedTutorCardProps) {
  const tutorName = assignedTutors.length > 0 && assignedTutors[0]?.tutor 
    ? assignedTutors[0].tutor.full_name 
    : 'Ing. Ana Torres';

  const tutorEmail = assignedTutors.length > 0 && assignedTutors[0]?.tutor 
    ? assignedTutors[0].tutor.email 
    : 'ana.torres@universidad.edu';

  return (
    <View className="px-6 mb-6">
      <Text className="text-[15px] font-bold text-[#1E1E2F] mb-3">Mi tutor</Text>
      
      <View className="bg-white border border-[#EEEDFE] rounded-3xl p-4 shadow-sm flex-row items-center justify-between">
        <View className="flex-row items-center flex-1">
          <View className="w-10 h-10 rounded-full bg-[#C084FC]/30 items-center justify-center mr-3">
            <Text className="text-xl">👨‍🏫</Text>
          </View>
          <View className="flex-1">
            <Text className="text-sm font-bold text-[#1E1E2F]">{tutorName}</Text>
            <Text className="text-xs text-[#8E8EA0] mt-0.5 font-medium">Docente Tutor</Text>
          </View>
        </View>

        <Pressable onPress={() => alert(`Contacto: ${tutorEmail}`)}>
          <Text className="text-xs font-bold text-[#9A3BEE]">Ver perfil</Text>
        </Pressable>
      </View>
    </View>
  );
}
