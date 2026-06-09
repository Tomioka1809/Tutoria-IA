// src/components/notifications/NotificationsList.tsx
import React from 'react';
import { ScrollView, View, Text, RefreshControl } from 'react-native';
import { Notification } from '@/src/types';
import { NotificationItem } from './NotificationItem';

interface NotificationsListProps {
  notifications: Notification[];
  isLoading: boolean;
  onRefresh: () => void;
  onMarkRead: (id: number, isRead: boolean) => void;
}

export function NotificationsList({
  notifications,
  isLoading,
  onRefresh,
  onMarkRead,
}: NotificationsListProps) {
  return (
    <ScrollView
      className="flex-1 px-6"
      showsVerticalScrollIndicator={false}
      refreshControl={
        <RefreshControl
          refreshing={isLoading}
          onRefresh={onRefresh}
          colors={['#9A3BEE']}
        />
      }
    >
      {notifications.length > 0 ? (
        notifications.map((notif) => (
          <NotificationItem
            key={notif.id}
            notification={notif}
            onPress={() => onMarkRead(notif.id, notif.is_read)}
          />
        ))
      ) : (
        // Default mockup items if database is empty to show the premium interface
        <View>
          <View className="bg-white border border-[#EEEDFE] rounded-3xl p-4 mb-3 shadow-sm flex-row items-center">
            <View className="w-12 h-12 rounded-[20px] bg-[#F3E8FF] items-center justify-center mr-4">
              <Text className="text-xl">🔔</Text>
            </View>
            <View className="flex-1">
              <Text className="text-sm font-bold text-[#1E1E2F]">Nueva tutoría asignada</Text>
              <Text className="text-xs text-[#8E8EA0] mt-1 font-medium">Hace 2 horas</Text>
            </View>
            <View className="w-2.5 h-2.5 rounded-full bg-[#9A3BEE] ml-2" />
          </View>

          <View className="bg-white border border-[#EEEDFE] rounded-3xl p-4 mb-3 shadow-sm flex-row items-center">
            <View className="w-12 h-12 rounded-[20px] bg-[#F3E8FF] items-center justify-center mr-4">
              <Text className="text-xl">📅</Text>
            </View>
            <View className="flex-1">
              <Text className="text-sm font-bold text-[#1E1E2F]">Recordatorio: Sesión mañana 10:00 AM</Text>
              <Text className="text-xs text-[#8E8EA0] mt-1 font-medium">Hace 5 horas</Text>
            </View>
            <View className="w-2.5 h-2.5 rounded-full bg-[#9A3BEE] ml-2" />
          </View>

          <View className="bg-white border border-[#EEEDFE] rounded-3xl p-4 mb-3 shadow-sm flex-row items-center">
            <View className="w-12 h-12 rounded-[20px] bg-[#FFEDD5] items-center justify-center mr-4">
              <Text className="text-xl">💼</Text>
            </View>
            <View className="flex-1">
              <Text className="text-sm font-bold text-[#1E1E2F]">Práctica disponible en Ing. Civil</Text>
              <Text className="text-xs text-[#8E8EA0] mt-1 font-medium">Hace 1 día</Text>
            </View>
            <View className="w-2.5 h-2.5 rounded-full bg-[#9A3BEE] ml-2" />
          </View>

          <View className="bg-white border border-[#EEEDFE] rounded-3xl p-4 mb-3 shadow-sm flex-row items-center">
            <View className="w-12 h-12 rounded-[20px] bg-[#ECFEFF] items-center justify-center mr-4">
              <Text className="text-xl">⭐</Text>
            </View>
            <View className="flex-1">
              <Text className="text-sm font-bold text-[#1E1E2F]">Bienestar: Taller de manejo del estrés</Text>
              <Text className="text-xs text-[#8E8EA0] mt-1 font-medium">Hace 2 días</Text>
            </View>
            <View className="w-2.5 h-2.5 rounded-full bg-[#9A3BEE] ml-2" />
          </View>

          <View className="bg-white border border-[#EEEDFE] rounded-3xl p-4 mb-3 shadow-sm flex-row items-center">
            <View className="w-12 h-12 rounded-[20px] bg-[#DBEAFE] items-center justify-center mr-4">
              <Text className="text-xl">✈️</Text>
            </View>
            <View className="flex-1">
              <Text className="text-sm font-bold text-[#1E1E2F]">Beca de Movilidad Internacional</Text>
              <Text className="text-xs text-[#8E8EA0] mt-1 font-medium">Hace 3 días</Text>
            </View>
            <View className="w-2.5 h-2.5 rounded-full bg-[#9A3BEE] ml-2" />
          </View>
        </View>
      )}
    </ScrollView>
  );
}
