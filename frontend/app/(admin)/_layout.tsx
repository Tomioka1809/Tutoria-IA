import { Tabs } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { View } from 'react-native';
import { useTranslation } from 'react-i18next';
import { useTheme } from '@/src/theme/ThemeContext';

export default function AdminLayout() {
  const { t } = useTranslation();
  const { colors, isDark } = useTheme();

  return (
    <Tabs screenOptions={{
      headerShown: true,
      headerStyle: { backgroundColor: colors.background },
      headerTitleStyle: { color: colors.text, fontWeight: 'bold' },
      tabBarStyle: { backgroundColor: colors.surface, borderTopWidth: 1, borderTopColor: isDark ? '#FFFFFF' : colors.border },
      tabBarActiveTintColor: isDark ? '#FFFFFF' : colors.primary,
      tabBarInactiveTintColor: isDark ? '#FFFFFF' : colors.textSecondary,
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
