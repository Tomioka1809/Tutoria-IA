// app/(estudiante)/index.tsx
import React from 'react';
import { ScrollView, Pressable, Text, View, RefreshControl } from 'react-native';
import { useRouter } from 'expo-router';
import { useDashboard } from '@/src/components/dashboard/useDashboard';
import { DashboardHeader } from '@/src/components/dashboard/DashboardHeader';
import { ServicesGrid } from '@/src/components/dashboard/ServicesGrid';
import { StreakCard } from '@/src/components/dashboard/StreakCard';
import { useTheme } from '@/src/theme/ThemeContext';

export default function DashboardScreen() {
  const { colors } = useTheme();
  const router = useRouter();
  const { streak, isLoading, onRefresh, firstName } = useDashboard();

  return (
    <ScrollView
      style={{ flex: 1, backgroundColor: colors.background }}
      contentContainerStyle={{ paddingBottom: 110 }}
      refreshControl={
        <RefreshControl
          refreshing={isLoading}
          onRefresh={onRefresh}
          colors={[colors.primary]}
        />
      }
    >
      <DashboardHeader firstName={firstName} />

      {/* Action Button: Iniciar Chat */}
      <View style={{ paddingHorizontal: 24, marginBottom: 24 }}>
        <Pressable
          onPress={() => router.push('/(estudiante)/tutoria')}
          style={{
            backgroundColor: colors.primary,
            borderRadius: 16,
            paddingVertical: 18,
            alignItems: 'center',
            justifyContent: 'center',
            shadowColor: colors.primary,
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
