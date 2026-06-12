// src/components/calendar/CalendarActivitiesList.tsx
import React from 'react';
import { View, Text, ScrollView, Pressable } from 'react-native';
import { Feather, FontAwesome } from '@expo/vector-icons';

interface UnifiedActivity {
  id: string;
  name: string;
  type: 'Tutoría Académica' | 'Reunión con Tutor' | 'Sesión de Apoyo Psicológico' | 'Entrega de Tarea';
  date: string;
  time: string;
  isBackend: boolean;
}

interface CalendarActivitiesListProps {
  activities: UnifiedActivity[];
  onAddPress: () => void;
  onDeletePress: (id: string) => void;
}

export function CalendarActivitiesList({
  activities,
  onAddPress,
  onDeletePress,
}: CalendarActivitiesListProps) {

  // Formatear 24h a 12h AM/PM
  const formatTime12h = (time24: string) => {
    try {
      const [hoursStr, minutesStr] = time24.split(':');
      const hours = parseInt(hoursStr, 10);
      const minutes = parseInt(minutesStr, 10);
      const ampm = hours >= 12 ? 'PM' : 'AM';
      const displayHours = hours % 12 === 0 ? 12 : hours % 12;
      const displayMinutes = String(minutes).padStart(2, '0');
      const formattedHours = String(displayHours).padStart(2, '0');
      return `${formattedHours}:${displayMinutes} ${ampm}`;
    } catch (e) {
      return time24;
    }
  };

  // Obtener rango de hora (duración 1h por defecto para tutorías, hora fija para tareas)
  const getRangeString = (timeStr: string, type: string) => {
    const startTimeFormatted = formatTime12h(timeStr);
    if (type === 'Entrega de Tarea') {
      return startTimeFormatted;
    }
    try {
      const [hoursStr, minutesStr] = timeStr.split(':');
      let hours = parseInt(hoursStr, 10);
      const minutes = parseInt(minutesStr, 10);
      hours = (hours + 1) % 24;
      const endTimeStr = `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}`;
      const endTimeFormatted = formatTime12h(endTimeStr);
      return `${startTimeFormatted} - ${endTimeFormatted}`;
    } catch (e) {
      return timeStr;
    }
  };

  // Formatear fecha de la actividad
  const formatActivityDate = (dateStr: string) => {
    try {
      const [year, month, day] = dateStr.split('-').map(Number);
      const date = new Date(year, month - 1, day);
      const today = new Date();
      const tomorrow = new Date(today);
      tomorrow.setDate(today.getDate() + 1);

      if (
        date.getDate() === today.getDate() &&
        date.getMonth() === today.getMonth() &&
        date.getFullYear() === today.getFullYear()
      ) {
        return 'Hoy';
      } else if (
        date.getDate() === tomorrow.getDate() &&
        date.getMonth() === tomorrow.getMonth() &&
        date.getFullYear() === tomorrow.getFullYear()
      ) {
        return 'Mañana';
      } else {
        return date.toLocaleDateString('es-ES', { day: 'numeric', month: 'short' });
      }
    } catch (e) {
      return dateStr;
    }
  };

  // Mapeo de estilos y configuración de cada tipo de actividad
  const getActivityStyle = (type: string) => {
    switch (type) {
      case 'Tutoría Académica':
        return {
          icon: 'book-open',
          iconSet: 'Feather' as const,
          iconColor: '#9A3BEE',
          bgColor: 'bg-[#F3E8FF]',
        };
      case 'Reunión con Tutor':
        return {
          icon: 'calendar',
          iconSet: 'Feather' as const,
          iconColor: '#0EA5E9',
          bgColor: 'bg-[#E0F2FE]',
        };
      case 'Sesión de Apoyo Psicológico':
        return {
          icon: 'heart-o',
          iconSet: 'FontAwesome' as const,
          iconColor: '#EC4899',
          bgColor: 'bg-[#FCE7F3]',
        };
      case 'Entrega de Tarea':
        return {
          icon: 'file-text',
          iconSet: 'Feather' as const,
          iconColor: '#7C3AED',
          bgColor: 'bg-[#F5F3FF]',
        };
      default:
        return {
          icon: 'book-open',
          iconSet: 'Feather' as const,
          iconColor: '#9A3BEE',
          bgColor: 'bg-[#F3E8FF]',
        };
    }
  };

  return (
    <View className="flex-1 px-6">
      <View className="flex-row justify-between items-center mb-4">
        <Text className="text-[#1E1E2F] font-bold text-base">Próximas actividades</Text>
        <Pressable onPress={onAddPress} className="flex-row items-center">
          <Text className="text-sm font-bold text-[#9A3BEE]">+ Añadir</Text>
        </Pressable>
      </View>

      <ScrollView className="flex-1" showsVerticalScrollIndicator={false}>
        {activities.length > 0 ? (
          activities.map((activity) => {
            const style = getActivityStyle(activity.type);
            const dateDisplay = formatActivityDate(activity.date);
            const timeRange = getRangeString(activity.time, activity.type);

            return (
              <View
                key={activity.id}
                className="bg-white border border-[#EEEDFE] rounded-3xl p-4 mb-3 shadow-sm flex-row items-center justify-between"
              >
                <View className="flex-row items-center flex-1">
                  {/* Contenedor del Icono */}
                  <View className={`w-12 h-12 rounded-[20px] items-center justify-center mr-4 ${style.bgColor}`}>
                    {style.iconSet === 'Feather' ? (
                      <Feather name={style.icon as any} size={20} color={style.iconColor} />
                    ) : (
                      <FontAwesome name={style.icon as any} size={20} color={style.iconColor} />
                    )}
                  </View>

                  {/* Textos: Nombre y Horarios */}
                  <View className="flex-1 mr-2">
                    <Text className="text-sm font-bold text-[#1E1E2F]" numberOfLines={1}>
                      {activity.name}
                    </Text>
                    <Text className="text-xs text-[#8E8EA0] mt-1 font-medium">
                      {dateDisplay}, {timeRange}
                    </Text>
                  </View>
                </View>

                {/* Botón de Eliminar (disponible para actividades locales creadas por el usuario) */}
                {!activity.isBackend && (
                  <Pressable
                    onPress={() => onDeletePress(activity.id)}
                    className="p-2 hit-slop-8"
                  >
                    <Feather name="trash-2" size={16} color="#EF4444" />
                  </Pressable>
                )}
              </View>
            );
          })
        ) : (
          // Vista vacía con estilo premium si no hay actividades
          <View className="items-center justify-center py-12 px-4 bg-white/50 border border-dashed border-[#EEEDFE] rounded-3xl">
            <Feather name="calendar" size={36} color="#8E8EA0" />
            <Text className="text-sm font-bold text-[#1E1E2F] mt-3 text-center">
              No tienes actividades programadas
            </Text>
            <Text className="text-xs text-[#8E8EA0] mt-1 text-center">
              ¡Presiona "+ Añadir" para agendar tu primera actividad!
            </Text>
          </View>
        )}
      </ScrollView>
    </View>
  );
}

