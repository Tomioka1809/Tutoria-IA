import { DarkTheme, DefaultTheme, ThemeProvider as NavThemeProvider } from '@react-navigation/native';
import { Stack, useSegments, useRouter, useRootNavigationState } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import 'react-native-reanimated';
import '../global.css';
import '../src/i18n';
import { useEffect, useState } from 'react';
import { useAuthStore } from '../src/store/auth';
import { ActivityIndicator, View } from 'react-native';

import { useColorScheme } from '@/hooks/use-color-scheme';
import { ThemeProvider as AppThemeProvider } from '@/src/theme/ThemeContext';

export const unstable_settings = {
  anchor: '(estudiante)',
};

function RootLayoutNav() {
  const colorScheme = useColorScheme();
  const segments = useSegments();
  const router = useRouter();
  const token = useAuthStore((state) => state.token);
  const user = useAuthStore((state) => state.user);
  const navigationState = useRootNavigationState();
  const [isHydrated, setIsHydrated] = useState(false);

  useEffect(() => {
    if (useAuthStore.persist.hasHydrated()) {
      setIsHydrated(true);
    } else {
      const unsub = useAuthStore.persist.onFinishHydration(() => {
        setIsHydrated(true);
      });
      return () => unsub();
    }
  }, []);

  useEffect(() => {
    if (!isHydrated || !navigationState?.key) {
      return;
    }

    const inAuthGroup = segments[0] === 'auth';
    const inAdminGroup = segments[0] === '(admin)';
    const inTutorGroup = segments[0] === '(tutor)';
    const inEstudianteGroup = segments[0] === '(estudiante)';

    if (!token && !inAuthGroup) {
      router.replace('/auth/login');
    } else if (token) {
      if (user?.role === 'admin') {
        if (!inAdminGroup) {
          router.replace('/(admin)');
        }
      } else if (user?.role === 'tutor') {
        if (!inTutorGroup) {
          router.replace('/(tutor)');
        }
      } else if (user?.role === 'estudiante') {
        if (!inEstudianteGroup) {
          router.replace('/(estudiante)');
        }
      } else {
        // Fallback for default role if not assigned properly
        if (!inEstudianteGroup) {
          router.replace('/(estudiante)');
        }
      }
    }
  }, [token, user, segments, isHydrated, navigationState?.key]);

  if (!isHydrated) {
    return (
      <NavThemeProvider value={colorScheme === 'dark' ? DarkTheme : DefaultTheme}>
        <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
          <ActivityIndicator size="large" color="#9A3BEE" />
        </View>
      </NavThemeProvider>
    );
  }

  return (
    <NavThemeProvider value={colorScheme === 'dark' ? DarkTheme : DefaultTheme}>
      <Stack screenOptions={{ headerShown: false }}>
        <Stack.Screen name="auth/login" />
        <Stack.Screen name="auth/register" />
        <Stack.Screen name="(estudiante)" />
        <Stack.Screen name="(tutor)" />
        <Stack.Screen name="(admin)" />
        <Stack.Screen name="modal" options={{ presentation: 'modal' }} />
      </Stack>
      <StatusBar style="auto" />
    </NavThemeProvider>
  );
}

export default function RootLayout() {
  return (
    <AppThemeProvider>
      <RootLayoutNav />
    </AppThemeProvider>
  );
}
