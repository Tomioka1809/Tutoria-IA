// src/components/calendar/ScheduleSessionModal.tsx
import React from 'react';
import { View, Text, TextInput, Modal, Pressable, ActivityIndicator } from 'react-native';
import { User, ServiceType } from '@/src/types';

interface ScheduleSessionModalProps {
  isModalOpen: boolean;
  onClose: () => void;
  selectedDate: Date;
  students: User[];
  serviceTypes: ServiceType[];
  selectedStudentId: number | null;
  setSelectedStudentId: (id: number) => void;
  selectedServiceTypeId: number | null;
  setSelectedServiceTypeId: (id: number) => void;
  sessionHour: string;
  setSessionHour: (hour: string) => void;
  sessionNotes: string;
  setSessionNotes: (notes: string) => void;
  isSubmitting: boolean;
  isDataLoading: boolean;
  onSubmit: () => void;
}

export function ScheduleSessionModal({
  isModalOpen,
  onClose,
  selectedDate,
  students,
  serviceTypes,
  selectedStudentId,
  setSelectedStudentId,
  selectedServiceTypeId,
  setSelectedServiceTypeId,
  sessionHour,
  setSessionHour,
  sessionNotes,
  setSessionNotes,
  isSubmitting,
  isDataLoading,
  onSubmit,
}: ScheduleSessionModalProps) {
  return (
    <Modal visible={isModalOpen} animationType="slide" transparent={true}>
      <View className="flex-1 bg-black/50 justify-end">
        <View className="bg-white rounded-t-[40px] px-6 pt-8 pb-12">
          <View className="flex-row justify-between items-center mb-6">
            <Text className="text-xl font-bold text-[#26215C]">Programar Tutoría</Text>
            <Pressable onPress={onClose}>
              <Text className="text-[#9A3BEE] font-bold text-sm">Cerrar</Text>
            </Pressable>
          </View>

          {isDataLoading ? (
            <ActivityIndicator size="large" color="#9A3BEE" className="py-12" />
          ) : (
            <View>
              <View className="mb-4 bg-[#EEEDFE] p-3.5 rounded-xl border border-[#7F77DD]/20">
                <Text className="text-xs text-[#26215C]/60 font-semibold">Fecha Seleccionada</Text>
                <Text className="text-base text-[#26215C] font-bold mt-1">
                  {selectedDate.toLocaleDateString('es-ES', { weekday: 'long', day: 'numeric', month: 'long' })}
                </Text>
              </View>

              {/* Student Select */}
              <View className="mb-4">
                <Text className="text-xs text-[#26215C] font-semibold mb-2 ml-1">Estudiante</Text>
                <View className="bg-[#EEEDFE]/50 border border-[#7F77DD]/30 rounded-xl p-1 flex-row flex-wrap">
                  {students.map((student) => (
                    <Pressable
                      key={student.id}
                      onPress={() => setSelectedStudentId(student.id)}
                      className={`px-3 py-2 rounded-lg m-1 border ${
                        selectedStudentId === student.id
                          ? 'bg-[#9A3BEE] border-[#9A3BEE]'
                          : 'bg-white border-[#7F77DD]/20'
                      }`}
                    >
                      <Text
                        className={`text-xs font-semibold ${
                          selectedStudentId === student.id ? 'text-white' : 'text-[#26215C]/80'
                        }`}
                      >
                        {student.full_name}
                      </Text>
                    </Pressable>
                  ))}
                </View>
              </View>

              {/* Service Type Select */}
              <View className="mb-4">
                <Text className="text-xs text-[#26215C] font-semibold mb-2 ml-1">Tipo de Servicio</Text>
                <View className="bg-[#EEEDFE]/50 border border-[#7F77DD]/30 rounded-xl p-1 flex-row flex-wrap">
                  {serviceTypes.map((type) => (
                    <Pressable
                      key={type.id}
                      onPress={() => setSelectedServiceTypeId(type.id)}
                      className={`px-3 py-2 rounded-lg m-1 border ${
                        selectedServiceTypeId === type.id
                          ? 'bg-[#9A3BEE] border-[#9A3BEE]'
                          : 'bg-white border-[#7F77DD]/20'
                      }`}
                    >
                      <Text
                        className={`text-xs font-semibold ${
                          selectedServiceTypeId === type.id ? 'text-white' : 'text-[#26215C]/80'
                        }`}
                      >
                        {type.name}
                      </Text>
                    </Pressable>
                  ))}
                </View>
              </View>

              {/* Hour selection input */}
              <View className="mb-4">
                <Text className="text-xs text-[#26215C] font-semibold mb-2 ml-1">Hora (Formato 24h)</Text>
                <TextInput
                  value={sessionHour}
                  onChangeText={setSessionHour}
                  placeholder="10:00"
                  className="bg-[#EEEDFE]/50 border border-[#7F77DD]/30 rounded-xl px-4 py-3 text-[#26215C] font-bold"
                />
              </View>

              {/* Notes Input */}
              <View className="mb-6">
                <Text className="text-xs text-[#26215C] font-semibold mb-2 ml-1">Notas / Detalles</Text>
                <TextInput
                  value={sessionNotes}
                  onChangeText={setSessionNotes}
                  placeholder="Repasar dudas..."
                  className="bg-[#EEEDFE]/50 border border-[#7F77DD]/30 rounded-xl px-4 py-3 text-[#26215C]"
                  multiline
                  numberOfLines={2}
                />
              </View>

              <Pressable
                onPress={onSubmit}
                disabled={isSubmitting}
                className="bg-[#9A3BEE] rounded-xl py-3 items-center justify-center shadow-md"
              >
                {isSubmitting ? (
                  <ActivityIndicator color="white" />
                ) : (
                  <Text className="text-white font-bold text-base">Crear Tutoría</Text>
                )}
              </Pressable>
            </View>
          )}
        </View>
      </View>
    </Modal>
  );
}
