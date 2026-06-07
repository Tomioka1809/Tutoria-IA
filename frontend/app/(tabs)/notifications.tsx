import React, { useEffect } from 'react';
import { View, Text, ScrollView, Pressable, RefreshControl } from 'react-native';
import { useNotificationStore } from '../../src/store/notification';

export default function NotificationsScreen() {
  const { notifications, fetchNotifications, markAsRead, isLoading } = useNotificationStore();

  useEffect(() => {
    fetchNotifications();
  }, []);

  const handleMarkRead = (id: number, isRead: boolean) => {
    if (!isRead) {
      markAsRead(id);
    }
  };

  return (
    <View className="flex-1 bg-[#F5F5FB] pt-16">
      {/* Header section matching mockup with Filter dropdown */}
      <View className="px-6 mb-6 flex-row items-center justify-between">
        <View className="flex-row items-center">
          <Pressable onPress={() => {}} className="mr-3 p-1">
            <Text className="text-xl text-[#26215C]">←</Text>
          </Pressable>
          <Text className="text-[20px] font-bold text-[#111130]">Notificaciones</Text>
        </View>
        
        {/* Filter selection mock dropdown */}
        <Pressable className="bg-white border border-[#9A3BEE] rounded-xl px-4 py-1.5 flex-row items-center shadow-sm">
          <Text className="text-xs font-semibold text-[#9A3BEE] mr-1.5">Todas</Text>
          <Text className="text-xs text-[#9A3BEE]">∨</Text>
        </Pressable>
      </View>

      <ScrollView
        className="flex-1 px-6"
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={isLoading}
            onRefresh={fetchNotifications}
            colors={['#9A3BEE']}
          />
        }
      >
        {notifications.length > 0 ? (
          notifications.map((notif) => {
            // Determine colors and icon based on notification type/mockup
            let iconStr = '🔔';
            let iconBg = 'bg-[#F3E8FF]';
            
            if (notif.title.includes('Sesión') || notif.type === 'session') {
              iconStr = '📅';
              iconBg = 'bg-[#F3E8FF]';
            } else if (notif.title.includes('Práctica')) {
              iconStr = '💼';
              iconBg = 'bg-[#FFEDD5]';
            } else if (notif.title.includes('Bienestar')) {
              iconStr = '⭐';
              iconBg = 'bg-[#ECFEFF]';
            } else if (notif.title.includes('Mesa') || notif.title.includes('Beca')) {
              iconStr = '✈️';
              iconBg = 'bg-[#DBEAFE]';
            }

            return (
              <Pressable
                key={notif.id}
                onPress={() => handleMarkRead(notif.id, notif.is_read)}
                className="bg-white border border-[#EEEDFE] rounded-3xl p-4 mb-3 shadow-sm flex-row items-center"
              >
                {/* Circular soft-colored icon on the left */}
                <View className={`w-12 h-12 rounded-[20px] items-center justify-center mr-4 ${iconBg}`}>
                  <Text className="text-xl">{iconStr}</Text>
                </View>

                {/* Content detail */}
                <View className="flex-1">
                  <Text className="text-sm font-bold text-[#1E1E2F]">{notif.title}</Text>
                  <Text className="text-xs text-[#8E8EA0] mt-1 font-medium">Hace 2 horas</Text>
                </View>

                {/* Unread purple dot indicator on the right */}
                {!notif.is_read ? (
                  <View className="w-2.5 h-2.5 rounded-full bg-[#9A3BEE] ml-2" />
                ) : null}
              </Pressable>
            );
          })
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
    </View>
  );
}
