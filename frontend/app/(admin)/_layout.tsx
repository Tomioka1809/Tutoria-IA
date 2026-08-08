import { Tabs } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { Platform } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';
import { useTheme } from '@/src/theme/ThemeContext';

export default function AdminLayout() {
  const { t } = useTranslation();
  const { colors } = useTheme();
  const insets = useSafeAreaInsets();

  const minimumBottomPadding = Platform.OS === 'ios' ? 24 : 12;
  const bottomPadding = Math.max(insets.bottom, minimumBottomPadding);
  const tabBarBaseHeight = 62;

  return (
    <Tabs screenOptions={{
      headerShown: true,
      headerStyle: { backgroundColor: colors.background },
      headerTitleStyle: { color: colors.text, fontWeight: 'bold' },
      tabBarActiveTintColor: colors.primary,
      tabBarInactiveTintColor: colors.textSecondary,
      tabBarHideOnKeyboard: true,
      tabBarStyle: {
        backgroundColor: colors.surface,
        borderTopWidth: 1,
        borderTopColor: colors.border,
        height: tabBarBaseHeight + bottomPadding,
        paddingBottom: bottomPadding,
        paddingTop: 8,
        position: 'absolute',
        bottom: 0,
        left: 0,
        right: 0,
      },
    }}>
      <Tabs.Screen 
        name="index" 
        options={{ 
          title: t('tabs.dashboard') || 'Dashboard',
          tabBarIcon: ({ color }) => <Ionicons name="pie-chart" size={24} color={color} />
        }} 
      />
      <Tabs.Screen 
        name="users" 
        options={{ 
          title: t('tabs.users') || 'Usuarios',
          tabBarIcon: ({ color }) => <Ionicons name="people" size={24} color={color} />
        }} 
      />
      <Tabs.Screen 
        name="sorteo" 
        options={{ 
          title: t('tabs.assignments') || 'Asignaciones',
          tabBarIcon: ({ color }) => <Ionicons name="shuffle" size={24} color={color} />
        }} 
      />
      <Tabs.Screen 
        name="contenido" 
        options={{ 
          title: t('tabs.content') || 'Contenido',
          tabBarIcon: ({ color }) => <Ionicons name="book" size={24} color={color} />
        }} 
      />
      <Tabs.Screen 
        name="configuracion" 
        options={{ 
          title: t('tabs.settings') || 'Ajustes',
          tabBarIcon: ({ color }) => <Ionicons name="settings" size={24} color={color} />
        }} 
      />
    </Tabs>
  );
}
