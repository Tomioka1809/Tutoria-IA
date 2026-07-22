import React from 'react';
import { View, Text, ScrollView, Pressable } from 'react-native';
import { Feather, FontAwesome } from '@expo/vector-icons';
import { useTheme } from '@/src/theme/ThemeContext';
import { useTranslation } from 'react-i18next';
import { CalendarItem } from './calendar-items';

interface CalendarActivitiesListProps {
  activities: CalendarItem[];
  userRole?: string;
  onAddPress: () => void;
  onViewPress?: (activity: CalendarItem) => void;
  onDeletePress: (activity: CalendarItem) => void;
}

export function CalendarActivitiesList({
  activities,
  userRole,
  onAddPress,
  onViewPress,
  onDeletePress,
}: CalendarActivitiesListProps) {
  const isTutor = userRole === 'tutor' || userRole === 'admin';
  const { colors } = useTheme();
  const { t, i18n } = useTranslation();

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
    } catch {
      return time24;
    }
  };

  const getRangeString = (timeStr: string, type: string) => {
    const startTimeFormatted = formatTime12h(timeStr);
    if (type === 'Trabajos') {
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
    } catch {
      return timeStr;
    }
  };

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
        return t('calendar.today');
      } else if (
        date.getDate() === tomorrow.getDate() &&
        date.getMonth() === tomorrow.getMonth() &&
        date.getFullYear() === tomorrow.getFullYear()
      ) {
        return t('calendar.tomorrow');
      } else {
        return date.toLocaleDateString(i18n.language === 'en' ? 'en-US' : 'es-ES', { day: 'numeric', month: 'short' });
      }
    } catch {
      return dateStr;
    }
  };

  const getActivityStyle = (type: string) => {
    if (type === 'Tutoría Académica') {
      return {
        icon: 'book-open',
        iconSet: 'Feather' as const,
        iconColor: colors.primary,
        bgColor: 'bg-[#F3E8FF]',
      };
    } else if (type === 'Tutoría Personal' || type === 'Sesión de Apoyo Psicológico') {
      return {
        icon: 'user',
        iconSet: 'Feather' as const,
        iconColor: '#EC4899',
        bgColor: 'bg-[#FCE7F3]',
      };
    } else if (type === 'Tutoría Profesional') {
      return {
        icon: 'briefcase',
        iconSet: 'Feather' as const,
        iconColor: '#4F46E5',
        bgColor: 'bg-[#E0E7FF]',
      };
    } else if (type === 'Trabajos') {
      return {
        icon: 'file-text',
        iconSet: 'Feather' as const,
        iconColor: '#7C3AED',
        bgColor: 'bg-[#F5F3FF]',
      };
    } else {
      return {
        icon: 'book-open',
        iconSet: 'Feather' as const,
        iconColor: colors.primary,
        bgColor: 'bg-[#F3E8FF]',
      };
    }
  };

  return (
    <View className="flex-1 px-6">
      <View className="flex-row justify-between items-center mb-4">
        <Text style={{ color: colors.text }} className=" font-bold text-base">{t('calendar.upcoming')}</Text>
        <Pressable onPress={onAddPress} className="flex-row items-center">
          <Text className="text-sm font-bold" style={{ color: colors.primary }}>{t('calendar.add')}</Text>
        </Pressable>
      </View>

      <ScrollView className="flex-1" showsVerticalScrollIndicator={false}>
        {activities.length > 0 ? (
          activities.map((activity) => {
            const dateStr = activity.dateStr;
            const timeStr = activity.timeStr;
            const nameStr = activity.name;
            const style = getActivityStyle(activity.type);
            const dateDisplay = formatActivityDate(dateStr);
            const timeRange = getRangeString(timeStr, activity.type);
            
            const canDelete = !activity.isBackend || isTutor;

            return (
              <Pressable
                key={activity.id}
                onPress={() => onViewPress && onViewPress(activity)}
                style={{ backgroundColor: colors.surface }} className=" border border-border rounded-3xl p-4 mb-3 shadow-sm flex-row items-center justify-between"
              >
                <View className="flex-row items-center flex-1">
                  <View className={`w-12 h-12 rounded-[20px] items-center justify-center mr-4 ${style.bgColor}`}>
                    {style.iconSet === 'Feather' ? (
                      <Feather name={style.icon as any} size={20} color={style.iconColor} />
                    ) : (
                      <FontAwesome name={style.icon as any} size={20} color={style.iconColor} />
                    )}
                  </View>

                  <View className="flex-1 mr-2">
                    <Text style={{ color: colors.text }} className="text-sm font-bold " numberOfLines={1}>
                      {nameStr}
                    </Text>
                    <Text className="text-xs text-textSecondary mt-1 font-medium">
                      {dateDisplay}, {timeRange}
                    </Text>
                  </View>
                </View>

                {canDelete && (
                  <Pressable
                    onPress={() => onDeletePress(activity)}
                    className="p-2 hit-slop-8"
                  >
                    <Feather name="trash-2" size={16} color={colors.danger} />
                  </Pressable>
                )}
              </Pressable>
            );
          })
        ) : (
          <View style={{ backgroundColor: colors.surface }} className="items-center justify-center py-12 px-4 /50 border border-dashed border-border rounded-3xl">
            <Feather name="calendar" size={36} color={colors.textSecondary} />
            <Text style={{ color: colors.text }} className="text-sm font-bold  mt-3 text-center">
              {t('calendar.emptyScheduled')}
            </Text>
            <Text className="text-xs text-textSecondary mt-1 text-center">
              {t('calendar.emptyScheduledHint')}
            </Text>
          </View>
        )}
      </ScrollView>
    </View>
  );
}
