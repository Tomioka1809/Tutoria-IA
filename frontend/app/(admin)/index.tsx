import { View, Text, ScrollView, ActivityIndicator, Dimensions, Platform, Pressable } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useAuthStore } from '../../src/store/auth';
import { useState, useCallback } from 'react';
import client from '../../src/api/client';
import { useFocusEffect } from 'expo-router';
import { PieChart } from 'react-native-chart-kit';
import { Feather } from '@expo/vector-icons';
import { useTheme } from '@/src/theme/ThemeContext';
import { useTranslation } from 'react-i18next';

const screenWidth = Dimensions.get("window").width;

export default function AdminDashboard() {
  const { colors } = useTheme();
  const { t } = useTranslation();
  const insets = useSafeAreaInsets();
  const user = useAuthStore(state => state.user);
  const token = useAuthStore(state => state.token);

  const minimumBottomPadding = Platform.OS === 'ios' ? 24 : 12;
  const bottomPadding = Math.max(insets.bottom, minimumBottomPadding);
  const tabBarBaseHeight = 62;
  const totalTabBarHeight = tabBarBaseHeight + bottomPadding;
  const scrollBottomPadding = totalTabBarHeight + 24;

  const [stats, setStats] = useState({
    total_students: 0,
    active_tutors: 0,
    pending_tutors: 0,
    completed_sessions: 0,
    total_capacity: 0,
    assigned_students: 0
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStats = useCallback(async () => {
    setError(null);
    setLoading(true);
    try {
      const res = await client.get('/admin/stats', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setStats(res.data);
    } catch (e) {
      const safeErrorMessage = e instanceof Error ? e.message : 'unknown_error';
      console.log('[AdminDashboard] No se pudieron cargar las estadísticas:', safeErrorMessage);
      setError(t('errors.network', {
        defaultValue: 'No fue posible conectarse con el servidor. Revisa tu conexión a internet.'
      }));
    } finally {
      setLoading(false);
    }
  }, [token, t]);

  useFocusEffect(
    useCallback(() => {
      fetchStats();
    }, [fetchStats])
  );

  const chartData = [
    {
      name: "Ocupado",
      population: stats.assigned_students,
      color: colors.primary,
      legendFontColor: colors.text,
      legendFontSize: 13
    },
    {
      name: "Libre",
      population: Math.max(0, stats.total_capacity - stats.assigned_students),
      color: "#CBD5E1",
      legendFontColor: colors.text,
      legendFontSize: 13
    }
  ];

  return (
    <ScrollView
      className="flex-1 bg-background dark:bg-black p-4"
      contentContainerStyle={{ paddingBottom: scrollBottomPadding }}
    >
      <View className="mb-6 mt-2">
        <Text className="text-2xl font-bold text-text dark:text-white">{t('admin.welcome', { name: user?.full_name })}</Text>
        <Text className="text-primary dark:text-white">{t('admin.centralPanel')}</Text>
      </View>

      {loading ? (
        <ActivityIndicator size="large" color={colors.primary} className="mt-10" />
      ) : error ? (
        <View style={{ backgroundColor: colors.surface }} className="p-6 rounded-2xl shadow-sm border border-red-200 dark:border-red-800 items-center my-6">
          <Feather name="alert-circle" size={40} color="#DC2626" style={{ marginBottom: 12 }} />
          <Text className="text-text dark:text-white text-center font-medium mb-4 text-sm">
            {error}
          </Text>
          <Pressable
            onPress={fetchStats}
            disabled={loading}
            style={{ backgroundColor: colors.primary }}
            className={`px-6 py-3 rounded-xl items-center shadow-sm ${loading ? 'opacity-70' : ''}`}
          >
            <Text className="text-white font-bold text-sm">{t('common.retry')}</Text>
          </Pressable>
        </View>
      ) : (
        <>
          <View className="flex-row flex-wrap justify-between">
            <View style={{ backgroundColor: colors.surface }} className="w-[48%] p-4 rounded-xl shadow-sm mb-4 border-l-4 border-primary dark:border dark:border-white">
              <Text className="text-text dark:text-white text-xs font-semibold">{t('admin.totalStudents')}</Text>
              <Text className="text-3xl font-bold text-text dark:text-white mt-2">{stats.total_students}</Text>
            </View>
            <View style={{ backgroundColor: colors.surface }} className="w-[48%] p-4 rounded-xl shadow-sm mb-4 border-l-4 border-green-500 dark:border dark:border-white">
              <Text className="text-text dark:text-white text-xs font-semibold">{t('admin.activeTutors')}</Text>
              <Text className="text-3xl font-bold text-text dark:text-white mt-2">{stats.active_tutors}</Text>
            </View>
            <View style={{ backgroundColor: colors.surface }} className="w-[48%] p-4 rounded-xl shadow-sm mb-4 border-l-4 border-yellow-500 dark:border dark:border-white">
              <Text className="text-text dark:text-white text-xs font-semibold">{t('admin.pendingTutors')}</Text>
              <Text className="text-3xl font-bold text-text dark:text-white mt-2">{stats.pending_tutors}</Text>
            </View>
            <View style={{ backgroundColor: colors.surface }} className="w-[48%] p-4 rounded-xl shadow-sm mb-4 border-l-4 border-blue-500 dark:border dark:border-white">
              <Text className="text-text dark:text-white text-xs font-semibold">{t('admin.completedSessions')}</Text>
              <Text className="text-3xl font-bold text-text dark:text-white mt-2">{stats.completed_sessions}</Text>
            </View>
          </View>

          {/* Gráfico de Capacidad */}
          <View style={{ backgroundColor: colors.surface }} className="p-4 rounded-2xl shadow-sm mb-10 border border-primary/20 dark:border-white">
            <Text className="text-lg font-bold text-text dark:text-white mb-2">{t('admin.semesterCapacity')}</Text>
            <Text className="text-xs text-primary dark:text-white mb-4">
              {t('admin.capacityDescription')}
            </Text>
            {stats.total_capacity > 0 ? (
              <PieChart
                data={chartData}
                width={screenWidth - 60}
                height={180}
                chartConfig={{
                  backgroundColor: colors.surface,
                  backgroundGradientFrom: colors.surface,
                  backgroundGradientTo: colors.surface,
                  color: (opacity = 1) => colors.primary,
                  labelColor: (opacity = 1) => colors.text,
                }}
                accessor={"population"}
                backgroundColor={"transparent"}
                paddingLeft={"10"}
                center={[10, 0]}
                absolute
              />
            ) : (
              <Text className="text-center text-gray-400 dark:text-white py-6">{t('admin.noCapacity')}</Text>
            )}
          </View>
        </>
      )}
    </ScrollView>
  );
}
