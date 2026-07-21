import { View, Text, ScrollView, ActivityIndicator, Dimensions } from 'react-native';
import { useAuthStore } from '../../src/store/auth';
import { useState, useCallback } from 'react';
import client from '../../src/api/client';
import { useFocusEffect } from 'expo-router';
import { PieChart } from 'react-native-chart-kit';
import { useTheme } from '@/src/theme/ThemeContext';
import { useTranslation } from 'react-i18next';

const screenWidth = Dimensions.get("window").width;

export default function AdminDashboard() {
  const { colors } = useTheme();
  const { t } = useTranslation();
  const user = useAuthStore(state => state.user);
  const token = useAuthStore(state => state.token);
  const [stats, setStats] = useState({ 
    total_students: 0, 
    active_tutors: 0, 
    pending_tutors: 0, 
    completed_sessions: 0,
    total_capacity: 0,
    assigned_students: 0
  });
  const [loading, setLoading] = useState(true);

  const fetchStats = async () => {
    try {
      const res = await client.get('/admin/stats', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setStats(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useFocusEffect(
    useCallback(() => {
      fetchStats();
    }, [])
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
      legendFontColor: colors.primary,
      legendFontSize: 13
    }
  ];

  return (
    <ScrollView className="flex-1 bg-background dark:bg-black p-4">
      <View className="mb-6 mt-2">
        <Text className="text-2xl font-bold text-text dark:text-white">{t('admin.welcome', { name: user?.full_name })}</Text>
        <Text className="text-primary dark:text-white">{t('admin.centralPanel')}</Text>
      </View>
      
      {loading ? (
        <ActivityIndicator size="large" color={colors.primary} className="mt-10" />
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
          <View style={{ backgroundColor: colors.surface }} className=" p-4 rounded-2xl shadow-sm mb-10 border border-primary/20 dark:border-white">
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
                  backgroundColor: "#ffffff",
                  backgroundGradientFrom: "#ffffff",
                  backgroundGradientTo: "#ffffff",
                  color: (opacity = 1) => `rgba(154, 59, 238, ${opacity})`,
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
