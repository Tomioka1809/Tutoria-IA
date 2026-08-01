import React from 'react';
import { View } from 'react-native';
import { useTheme } from '@/src/theme/ThemeContext';
import { useNotifications } from '@/src/components/notifications/useNotifications';
import { NotificationsHeader } from '@/src/components/notifications/NotificationsHeader';
import { NotificationsList } from '@/src/components/notifications/NotificationsList';

/**
 * Pantalla de notificaciones compartida por estudiante y tutor.
 *
 * Ambas rutas tenian el mismo cuerpo, byte por byte salvo el comentario de ruta, de modo
 * que cualquier arreglo habia que aplicarlo dos veces.
 */
export function NotificationsScreen() {
  const { colors } = useTheme();
  const { notifications, isLoading, fetchNotifications, handleMarkRead } = useNotifications();

  return (
    <View style={{ backgroundColor: colors.background }} className="flex-1  pt-16">
      <NotificationsHeader />

      <NotificationsList
        notifications={notifications}
        isLoading={isLoading}
        onRefresh={fetchNotifications}
        onMarkRead={handleMarkRead}
      />
    </View>
  );
}
