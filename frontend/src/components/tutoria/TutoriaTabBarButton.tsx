// src/components/tutoria/TutoriaTabBarButton.tsx
import React from 'react';
import { View, Pressable, Text, Platform, GestureResponderEvent } from 'react-native';

interface TutoriaTabBarButtonProps {
  children?: React.ReactNode;
  onPress?: (event: GestureResponderEvent) => void;
}

export function TutoriaTabBarButton({ onPress, ...props }: TutoriaTabBarButtonProps) {
  return (
    <Pressable
      onPress={onPress}
      {...props}
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
          backgroundColor: 'white',
          borderWidth: 3,
          borderColor: '#9A3BEE',
          justifyContent: 'center',
          alignItems: 'center',
          ...Platform.select({
            ios: {
              shadowColor: '#9A3BEE',
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
        <Text style={{ fontSize: 30 }}>🦖</Text>
      </View>
    </Pressable>
  );
}
