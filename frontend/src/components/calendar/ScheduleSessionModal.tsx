import React from 'react';
import { View, Text, TextInput, Modal, Pressable, ActivityIndicator } from 'react-native';
import { User, ServiceType } from '@/src/types';
import { useTheme } from '@/src/theme/ThemeContext';
import { useTranslation } from 'react-i18next';

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
  const { colors } = useTheme();
  const { t, i18n } = useTranslation();
  return (
    <Modal visible={isModalOpen} animationType="slide" transparent={true}>
      <View className="flex-1 bg-black/50 justify-end">
        <View style={{ backgroundColor: colors.surface, borderColor: colors.border }} className="rounded-t-[40px] px-6 pt-8 pb-12 border">
          <View className="flex-row justify-between items-center mb-6">
            <Text style={{ color: colors.text }} className="text-xl font-bold">{t('calendar.schedule')}</Text>
            <Pressable onPress={onClose}>
              <Text style={{ color: colors.primary }} className="font-bold text-sm">{t('common.close')}</Text>
            </Pressable>
          </View>

          {isDataLoading ? (
            <ActivityIndicator size="large" color={colors.primary} className="py-12" />
          ) : (
            <View>
              <View style={{ backgroundColor: colors.background, borderColor: colors.border }} className="mb-4 p-3.5 rounded-xl border">
                <Text style={{ color: colors.textSecondary }} className="text-xs font-semibold">{t('calendar.selectedDate')}</Text>
                <Text style={{ color: colors.text }} className="text-base font-bold mt-1">
                  {selectedDate.toLocaleDateString(i18n.language === 'en' ? 'en-US' : 'es-ES', { weekday: 'long', day: 'numeric', month: 'long' })}
                </Text>
              </View>

              {/* Student Select */}
              <View className="mb-4">
                <Text style={{ color: colors.text }} className="text-xs font-semibold mb-2 ml-1">{t('calendar.student')}</Text>
                <View style={{ backgroundColor: colors.background, borderColor: colors.border }} className="border rounded-xl p-1 flex-row flex-wrap">
                  {students.map((student) => (
                    <Pressable
                      key={student.id}
                      onPress={() => setSelectedStudentId(student.id)}
                      style={{
                        backgroundColor: selectedStudentId === student.id ? colors.primary : colors.surface,
                        borderColor: selectedStudentId === student.id ? colors.primary : colors.border,
                      }}
                      className="px-3 py-2 rounded-lg m-1 border"
                    >
                      <Text
                        className="text-xs font-semibold"
                        style={{
                          color: selectedStudentId === student.id ? '#FFFFFF' : colors.text,
                        }}
                      >
                        {student.full_name}
                      </Text>
                    </Pressable>
                  ))}
                </View>
              </View>

              {/* Service Type Select */}
              <View className="mb-4">
                <Text style={{ color: colors.text }} className="text-xs font-semibold mb-2 ml-1">{t('calendar.serviceType')}</Text>
                <View style={{ backgroundColor: colors.background, borderColor: colors.border }} className="border rounded-xl p-1 flex-row flex-wrap">
                  {serviceTypes.map((type) => (
                    <Pressable
                      key={type.id}
                      onPress={() => setSelectedServiceTypeId(type.id)}
                      style={{
                        backgroundColor: selectedServiceTypeId === type.id ? colors.primary : colors.surface,
                        borderColor: selectedServiceTypeId === type.id ? colors.primary : colors.border,
                      }}
                      className="px-3 py-2 rounded-lg m-1 border"
                    >
                      <Text
                        className="text-xs font-semibold"
                        style={{
                          color: selectedServiceTypeId === type.id ? '#FFFFFF' : colors.text,
                        }}
                      >
                        {type.name}
                      </Text>
                    </Pressable>
                  ))}
                </View>
              </View>

              {/* Hour selection input */}
              <View className="mb-4">
                <Text style={{ color: colors.text }} className="text-xs font-semibold mb-2 ml-1">{t('calendar.time24')}</Text>
                <TextInput
                  value={sessionHour}
                  onChangeText={setSessionHour}
                  placeholder="10:00"
                  placeholderTextColor={colors.textSecondary}
                  style={{ backgroundColor: colors.surface, borderColor: colors.border, color: colors.text }}
                  className="border rounded-xl px-4 py-3 font-bold"
                />
              </View>

              {/* Notes Input */}
              <View className="mb-6">
                <Text style={{ color: colors.text }} className="text-xs font-semibold mb-2 ml-1">{t('calendar.detailsNotes')}</Text>
                <TextInput
                  value={sessionNotes}
                  onChangeText={setSessionNotes}
                  placeholder={t('calendar.detailsPlaceholder')}
                  placeholderTextColor={colors.textSecondary}
                  style={{ backgroundColor: colors.surface, borderColor: colors.border, color: colors.text }}
                  className="border rounded-xl px-4 py-3"
                  multiline
                  numberOfLines={2}
                />
              </View>

              <Pressable
                onPress={onSubmit}
                disabled={isSubmitting}
                style={{ backgroundColor: colors.primary, opacity: isSubmitting ? 0.5 : 1 }}
                className="rounded-xl py-3 items-center justify-center shadow-md"
              >
                {isSubmitting ? (
                  <ActivityIndicator color="white" />
                ) : (
                  <Text className="text-white font-bold text-base">{t('calendar.createTutoring')}</Text>
                )}
              </Pressable>
            </View>
          )}
        </View>
      </View>
    </Modal>
  );
}
