// app/(tabs)/index.tsx
import React from 'react';
import { ScrollView, Pressable, Text, View, RefreshControl } from 'react-native';
import { useRouter } from 'expo-router';
import { useDashboard } from '@/src/components/dashboard/useDashboard';
import { DashboardHeader } from '@/src/components/dashboard/DashboardHeader';
import { ServicesGrid } from '@/src/components/dashboard/ServicesGrid';
import { StreakCard } from '@/src/components/dashboard/StreakCard';

export default function DashboardScreen() {
  const router = useRouter();
  const { streak, isLoading, onRefresh, firstName } = useDashboard();

  return (
    <ScrollView
      className="flex-1 bg-[#F5F5FB]"
      contentContainerStyle={{ paddingBottom: 60 }}
      refreshControl={
        <RefreshControl
          refreshing={isLoading}
          onRefresh={onRefresh}
          colors={['#9A3BEE']}
        />
      }
    >
      <DashboardHeader firstName={firstName} />

      {/* Action Button: Iniciar Chat */}
      <View className="px-6 mb-6">
        <Pressable
          onPress={() => router.push('/(tabs)/tutoria')}
          className="bg-[#9A3BEE] rounded-3xl py-4.5 items-center justify-center shadow-lg shadow-[#9A3BEE]/30"
          style={{ elevation: 5 }}
        >
          <Text className="text-white font-bold text-base">Iniciar Chat</Text>
        </Pressable>
      </View>

      <ServicesGrid />

      <StreakCard currentStreak={streak?.current_streak} />
    </ScrollView>
  );
}
