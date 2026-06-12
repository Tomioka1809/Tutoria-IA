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
      style={{ flex: 1, backgroundColor: '#F8F7FC' }}
      contentContainerStyle={{ paddingBottom: 110 }}
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
      <View style={{ paddingHorizontal: 24, marginBottom: 24 }}>
        <Pressable
          onPress={() => router.push('/(tabs)/tutoria')}
          style={{
            backgroundColor: '#9A3BEE',
            borderRadius: 16,
            paddingVertical: 18,
            alignItems: 'center',
            justifyContent: 'center',
            shadowColor: '#9A3BEE',
            shadowOffset: { width: 0, height: 4 },
            shadowOpacity: 0.2,
            shadowRadius: 6,
            elevation: 4,
          }}
        >
          <Text style={{ color: 'white', fontWeight: 'bold', fontSize: 16 }}>Iniciar Chat</Text>
        </Pressable>
      </View>

      <ServicesGrid />

      <StreakCard currentStreak={streak?.current_streak} />
    </ScrollView>
  );
}
