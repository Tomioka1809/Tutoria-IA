import React from 'react';
import { Image } from 'react-native';

interface TutorIAAvatarProps {
  size: number;
}

export function TutorIAAvatar({ size }: TutorIAAvatarProps) {
  return (
    <Image
      source={require('@/assets/images/tutoria-logo.png')}
      style={{
        width: size,
        height: size,
        borderRadius: size / 2,
      }}
      resizeMode="cover"
      accessible={false}
    />
  );
}
