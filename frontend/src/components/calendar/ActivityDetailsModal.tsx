import React from 'react';
import { View, Text, Modal, Pressable } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { Picker } from '@react-native-picker/picker';
import { useTheme } from '@/src/theme/ThemeContext';

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
  const { colors, isDark } = useTheme();
  if (!activity) return null;

  // Formatting date and time nicely
  const formatTime12h = (time24: string) => {
    try {
      const [hoursStr, minutesStr] = time24.split(':');
      const hours = parseInt(hoursStr, 10);
      const minutes = parseInt(minutesStr, 10);
      const ampm = hours >= 12 ? 'PM' : 'AM';
      const displayHours = hours % 12 === 0 ? 12 : hours % 12;
      return `${String(displayHours).padStart(2, '0')}:${String(minutes).padStart(2, '0')} ${ampm}`;
    } catch (e) {
      return time24;
    }
  };

  const isTutor = userRole === 'tutor' || userRole === 'admin';

  return (
    <Modal visible={!!activity} animationType="slide" transparent={true}>
      <View className="flex-1 bg-black/45 justify-end">
        <Pressable className="absolute inset-0" onPress={onClose} />
        
        <View style={{ backgroundColor: colors.surface }} className=" rounded-t-[40px] px-6 pt-8 pb-10 shadow-2xl border border-gray-100 max-h-[85%]">
          <View className="w-12 h-1 bg-gray-300 rounded-full align-self-center mx-auto mb-6" />
          
          <View className="flex-row justify-between items-center mb-6">
            <Text style={{ color: colors.text }} className="text-xl font-bold ">Detalles de la Actividad</Text>
            <Pressable onPress={onClose}>
              <Feather name="x" size={24} color={colors.textSecondary} />
            </Pressable>
          </View>

          <View className="mb-4">
            <Text className="text-sm font-bold uppercase tracking-wider mb-1" style={{ color: isDark ? '#FFFFFF' : colors.primary }}>{activity.type}</Text>
            <Text style={{ color: colors.text }} className="text-2xl font-bold ">{activity.name}</Text>
          </View>

          <View className="flex-row items-center mb-6">
            <View style={{ backgroundColor: colors.surface }} className=" px-3 py-1.5 rounded-lg flex-row items-center mr-3">
              <Feather name="calendar" size={14} color="#4B5563" />
              <Text className="text-sm font-bold text-[#4B5563] ml-2">{activity.date}</Text>
            </View>
            <View style={{ backgroundColor: colors.surface }} className=" px-3 py-1.5 rounded-lg flex-row items-center">
              <Feather name="clock" size={14} color="#4B5563" />
              <Text className="text-sm font-bold text-[#4B5563] ml-2">{formatTime12h(activity.time)}</Text>
            </View>
          </View>

          {activity.isBackend && (
            <View className="bg-[#F5F3FF] rounded-2xl p-4 mb-4 border border-primary/20">
              <View className="flex-row justify-between items-center mb-3">
                <Text className="text-xs font-bold text-textSecondary uppercase">Estado</Text>
                {isTutor && onStatusChange ? (
                  <View style={{ backgroundColor: colors.surface }} className=" border border-border rounded-xl overflow-hidden min-w-[150px]">
                    <Picker
                      selectedValue={activity.status}
                      onValueChange={(val) => onStatusChange(activity.rawId, val)}
                      style={{ height: 50, width: '100%' }}
                    >
                      <Picker.Item label="Pendiente" value="pendiente" color={colors.primary} />
                      <Picker.Item label="Programada" value="programada" color="#3B82F6" />
                      <Picker.Item label="Completada" value="completada" color="#10B981" />
                      <Picker.Item label="Cancelada" value="cancelada" color={colors.danger} />
                      <Picker.Item label="Ausente" value="ausente" color={colors.warning} />
                    </Picker>
                  </View>
                ) : (
                  <Text className={`text-xs font-bold uppercase ${
                    activity.status === 'completada' ? 'text-green-500' :
                    activity.status === 'cancelada' ? 'text-red-500' :
                    ''
                  }`} style={
                    activity.status !== 'completada' && activity.status !== 'cancelada' 
                      ? { color: isDark ? '#FFFFFF' : colors.primary } 
                      : undefined
                  }>
                    {activity.status}
                  </Text>
                )}
              </View>

              {!isTutor && activity.tutorName && (
                <View className="mb-3">
                  <Text className="text-xs font-bold text-textSecondary uppercase">Tutor Asignado</Text>
                  <Text style={{ color: colors.text }} className="text-sm font-bold ">{activity.tutorName}</Text>
                </View>
              )}

              {isTutor && activity.studentName && (
                <View className="mb-3">
                  <Text className="text-xs font-bold text-textSecondary uppercase">Estudiante</Text>
                  <Text style={{ color: colors.text }} className="text-sm font-bold ">{activity.studentName}</Text>
                </View>
              )}

              {activity.location && (
                <View className="mb-3">
                  <Text className="text-xs font-bold text-textSecondary uppercase">Lugar</Text>
                  <View className="flex-row items-center mt-1">
                    <Feather name="map-pin" size={14} color="#4B5563" />
                    <Text style={{ color: colors.text }} className="text-sm font-bold  ml-2">{activity.location}</Text>
                  </View>
                </View>
              )}

              {activity.notes && activity.notes !== activity.name && (
                <View>
                  <Text className="text-xs font-bold text-textSecondary uppercase">Notas</Text>
                  <Text className="text-sm text-[#4B5563] mt-1">{activity.notes}</Text>
                </View>
              )}
            </View>
          )}

          {!activity.isBackend && (
            <View style={{ backgroundColor: colors.surface }} className=" rounded-2xl p-4 mb-4">
              <Text className="text-xs font-bold text-textSecondary uppercase">Tipo de Actividad</Text>
              <Text style={{ color: colors.text }} className="text-sm font-bold  mt-1">Actividad personal programada localmente.</Text>
            </View>
          )}

        </View>
      </View>
    </Modal>
  );
}
