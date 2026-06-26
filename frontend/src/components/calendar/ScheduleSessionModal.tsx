// src/components/calendar/ScheduleSessionModal.tsx
import React from 'react';
import { View, Text, TextInput, Modal, Pressable, ActivityIndicator } from 'react-native';
import { User, ServiceType } from '@/src/types';
import { useTheme } from '@/src/theme/ThemeContext';

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
  const { colors, isDark } = useTheme();
  return (
    <Modal visible={isModalOpen} animationType="slide" transparent={true}>
      <View className="flex-1 bg-black/50 justify-end">
        <View style={{ backgroundColor: colors.surface }} className=" rounded-t-[40px] px-6 pt-8 pb-12">
          <View className="flex-row justify-between items-center mb-6">
            <Text className="text-xl font-bold text-text">Programar Tutoría</Text>
            <Pressable onPress={onClose}>
              <Text className="font-bold text-sm" style={{ color: isDark ? '#FFFFFF' : colors.primary }}>Cerrar</Text>
            </Pressable>
          </View>

          {isDataLoading ? (
            <ActivityIndicator size="large" color={colors.primary} className="py-12" />
          ) : (
            <View>
              <View className="mb-4 bg-border p-3.5 rounded-xl border border-primary/20">
                <Text className="text-xs text-text/60 font-semibold">Fecha Seleccionada</Text>
                <Text className="text-base text-text font-bold mt-1">
                  {selectedDate.toLocaleDateString('es-ES', { weekday: 'long', day: 'numeric', month: 'long' })}
                </Text>
              </View>

              {/* Student Select */}
              <View className="mb-4">
                <Text className="text-xs text-text font-semibold mb-2 ml-1">Estudiante</Text>
                <View className="bg-border/50 border border-primary/30 rounded-xl p-1 flex-row flex-wrap">
                  {students.map((student) => (
                    <Pressable
                      key={student.id}
                      onPress={() => setSelectedStudentId(student.id)}
                      className={`px-3 py-2 rounded-lg m-1 border ${
                        selectedStudentId === student.id
                          ? 'bg-primary border-primary'
                          : 'bg-surface border-primary/20'
                      }`}
                    >
                      <Text
                        className={`text-xs font-semibold ${
                          selectedStudentId === student.id ? 'text-white' : 'text-text/80'
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
                <Text className="text-xs text-text font-semibold mb-2 ml-1">Tipo de Servicio</Text>
                <View className="bg-border/50 border border-primary/30 rounded-xl p-1 flex-row flex-wrap">
                  {serviceTypes.map((type) => (
                    <Pressable
                      key={type.id}
                      onPress={() => setSelectedServiceTypeId(type.id)}
                      className={`px-3 py-2 rounded-lg m-1 border ${
                        selectedServiceTypeId === type.id
                          ? 'bg-primary border-primary'
                          : 'bg-surface border-primary/20'
                      }`}
                    >
                      <Text
                        className={`text-xs font-semibold ${
                          selectedServiceTypeId === type.id ? 'text-white' : 'text-text/80'
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
                <Text className="text-xs text-text font-semibold mb-2 ml-1">Hora (Formato 24h)</Text>
                <TextInput
                  value={sessionHour}
                  onChangeText={setSessionHour}
                  placeholder="10:00"
                  className="bg-border/50 border border-primary/30 rounded-xl px-4 py-3 text-text font-bold"
                />
              </View>

              {/* Notes Input */}
              <View className="mb-6">
                <Text className="text-xs text-text font-semibold mb-2 ml-1">Notas / Detalles</Text>
                <TextInput
                  value={sessionNotes}
                  onChangeText={setSessionNotes}
                  placeholder="Repasar dudas..."
                  className="bg-border/50 border border-primary/30 rounded-xl px-4 py-3 text-text"
                  multiline
                  numberOfLines={2}
                />
              </View>

              <Pressable
                onPress={onSubmit}
                disabled={isSubmitting}
                className="bg-primary rounded-xl py-3 items-center justify-center shadow-md"
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
