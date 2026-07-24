import React from 'react';
import { View, Text, Modal, Pressable } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { Picker } from '@react-native-picker/picker';
import { useTheme } from '@/src/theme/ThemeContext';
import { useTranslation } from 'react-i18next';

interface UnifiedActivity {
  id: string;
  name: string;
  type: string;
  date: string;
  time: string;
  isBackend: boolean;
  rawId: number;
  status?: string;
  notes?: string;
  location?: string;
  tutorName?: string;
  studentName?: string;
}

interface ActivityDetailsModalProps {
  activity: UnifiedActivity | null;
  onClose: () => void;
  userRole?: string;
  onStatusChange?: (sessionId: number, newStatus: string) => void;
}

export function ActivityDetailsModal({ activity, onClose, userRole, onStatusChange }: ActivityDetailsModalProps) {
  const { colors } = useTheme();
  const { t } = useTranslation();
  if (!activity) return null;

  const formatTime12h = (time24: string) => {
    try {
      const [hoursStr, minutesStr] = time24.split(':');
      const hours = parseInt(hoursStr, 10);
      const minutes = parseInt(minutesStr, 10);
      const ampm = hours >= 12 ? 'PM' : 'AM';
      const displayHours = hours % 12 === 0 ? 12 : hours % 12;
      return `${String(displayHours).padStart(2, '0')}:${String(minutes).padStart(2, '0')} ${ampm}`;
    } catch {
      return time24;
    }
  };

  const isTutor = userRole === 'tutor' || userRole === 'admin';

  return (
    <Modal visible={!!activity} animationType="slide" transparent={true}>
      <View className="flex-1 bg-black/45 justify-end">
        <Pressable className="absolute inset-0" onPress={onClose} />
        
        <View style={{ backgroundColor: colors.surface, borderColor: colors.border }} className="rounded-t-[40px] px-6 pt-8 pb-10 shadow-2xl border max-h-[85%]">
          <View style={{ backgroundColor: colors.border }} className="w-12 h-1 rounded-full align-self-center mx-auto mb-6" />
          
          <View className="flex-row justify-between items-center mb-6">
            <Text style={{ color: colors.text }} className="text-xl font-bold">{t('calendar.details')}</Text>
            <Pressable onPress={onClose} className="p-1">
              <Feather name="x" size={24} color={colors.textSecondary} />
            </Pressable>
          </View>

          <View className="mb-4">
            <Text className="text-sm font-bold uppercase tracking-wider mb-1" style={{ color: colors.primary }}>{activity.type}</Text>
            <Text style={{ color: colors.text }} className="text-2xl font-bold">{activity.name}</Text>
          </View>

          <View className="flex-row items-center mb-6">
            <View style={{ backgroundColor: colors.background, borderColor: colors.border }} className="px-3 py-1.5 rounded-lg flex-row items-center mr-3 border">
              <Feather name="calendar" size={14} color={colors.textSecondary} />
              <Text style={{ color: colors.text }} className="text-sm font-bold ml-2">{activity.date}</Text>
            </View>
            <View style={{ backgroundColor: colors.background, borderColor: colors.border }} className="px-3 py-1.5 rounded-lg flex-row items-center border">
              <Feather name="clock" size={14} color={colors.textSecondary} />
              <Text style={{ color: colors.text }} className="text-sm font-bold ml-2">{formatTime12h(activity.time)}</Text>
            </View>
          </View>

          {activity.isBackend && (
            <View style={{ backgroundColor: colors.background, borderColor: colors.border }} className="rounded-2xl p-4 mb-4 border">
              <View className="flex-row justify-between items-center mb-3">
                <Text style={{ color: colors.textSecondary }} className="text-xs font-bold uppercase">{t('calendar.status')}</Text>
                {isTutor && onStatusChange ? (
                  <View style={{ backgroundColor: colors.surface, borderColor: colors.border }} className="border rounded-xl overflow-hidden min-w-[150px]">
                    <Picker
                      selectedValue={activity.status}
                      onValueChange={(val) => onStatusChange(activity.rawId, val)}
                      style={{ height: 50, width: '100%', color: colors.text }}
                    >
                      <Picker.Item label={t('calendar.pending')} value="pendiente" color={colors.primary} />
                      <Picker.Item label={t('calendar.scheduled')} value="programada" color="#3B82F6" />
                      <Picker.Item label={t('calendar.completed')} value="completada" color="#10B981" />
                      <Picker.Item label={t('calendar.cancelled')} value="cancelada" color={colors.danger} />
                      <Picker.Item label={t('calendar.absent')} value="ausente" color={colors.warning} />
                    </Picker>
                  </View>
                ) : (
                  <Text className={`text-xs font-bold uppercase ${
                    activity.status === 'completada' ? 'text-green-500' :
                    activity.status === 'cancelada' ? 'text-red-500' :
                    ''
                  }`} style={
                    activity.status !== 'completada' && activity.status !== 'cancelada'
                      ? { color: colors.primary }
                      : undefined
                  }>
                    {activity.status}
                  </Text>
                )}
              </View>

              {!isTutor && activity.tutorName && (
                <View className="mb-3">
                  <Text style={{ color: colors.textSecondary }} className="text-xs font-bold uppercase">{t('calendar.assignedTutor')}</Text>
                  <Text style={{ color: colors.text }} className="text-sm font-bold">{activity.tutorName}</Text>
                </View>
              )}

              {isTutor && activity.studentName && (
                <View className="mb-3">
                  <Text style={{ color: colors.textSecondary }} className="text-xs font-bold uppercase">{t('calendar.student')}</Text>
                  <Text style={{ color: colors.text }} className="text-sm font-bold">{activity.studentName}</Text>
                </View>
              )}

              {activity.location && (
                <View className="mb-3">
                  <Text style={{ color: colors.textSecondary }} className="text-xs font-bold uppercase">{t('calendar.location')}</Text>
                  <View className="flex-row items-center mt-1">
                    <Feather name="map-pin" size={14} color={colors.textSecondary} />
                    <Text style={{ color: colors.text }} className="text-sm font-bold ml-2">{activity.location}</Text>
                  </View>
                </View>
              )}

              {activity.notes && activity.notes !== activity.name && (
                <View>
                  <Text style={{ color: colors.textSecondary }} className="text-xs font-bold uppercase">{t('calendar.notes')}</Text>
                  <Text style={{ color: colors.text }} className="text-sm mt-1">{activity.notes}</Text>
                </View>
              )}
            </View>
          )}

          {!activity.isBackend && (
            <View style={{ backgroundColor: colors.background, borderColor: colors.border }} className="rounded-2xl p-4 mb-4 border">
              <Text style={{ color: colors.textSecondary }} className="text-xs font-bold uppercase">{t('calendar.activityKind')}</Text>
              <Text style={{ color: colors.text }} className="text-sm font-bold mt-1">{t('calendar.personalActivity')}</Text>
            </View>
          )}

        </View>
      </View>
    </Modal>
  );
}
