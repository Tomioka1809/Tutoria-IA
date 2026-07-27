// src/components/tutoria/TutoriaTabBarButton.tsx
import React from 'react';
import { View, Pressable, Platform, GestureResponderEvent, Image } from 'react-native';
import { useTheme } from '@/src/theme/ThemeContext';

interface TutoriaTabBarButtonProps {
  children?: React.ReactNode;
  onPress?: (event: GestureResponderEvent) => void;
  accessibilityLabel?: string;
}

export function TutoriaTabBarButton({ onPress, ...props }: TutoriaTabBarButtonProps) {
  const { colors } = useTheme();
  return (
    <Pressable
      {...props}
      onPress={onPress}
      accessibilityRole="button"
      accessibilityLabel={props.accessibilityLabel ?? 'TutorIA'}
      hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
      style={{
        top: -18,
        justifyContent: 'center',
        alignItems: 'center',
        width: 70,
        height: 70,
      }}
    >
      <View
        style={{
          width: 58,
          height: 58,
          borderRadius: 29,
          backgroundColor: colors.surface,
          borderWidth: 3,
          borderColor: colors.primary,
          justifyContent: 'center',
          alignItems: 'center',
          ...Platform.select({
            ios: {
              shadowColor: colors.primary,
              shadowOffset: { width: 0, height: 4 },
              shadowOpacity: 0.3,
              shadowRadius: 5,
            },
            android: {
              elevation: 6,
            },
          }),
        }}
      >
        <Image
          source={require('@/assets/images/tutoria-logo.png')}
          style={{
            width: 52,
            height: 52,
            borderRadius: 26,
          }}
          resizeMode="cover"
        />
      </View>
    </Pressable>
  );
}
