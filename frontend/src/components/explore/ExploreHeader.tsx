// src/components/explore/ExploreHeader.tsx
import React from 'react';
import { StyleSheet, StyleProp, ViewStyle } from 'react-native';
import { IconSymbol } from '@/components/ui/icon-symbol';

interface ExploreHeaderProps {
  style: StyleProp<ViewStyle>;
}

export function ExploreHeader({ style }: ExploreHeaderProps) {
  return (
    <IconSymbol
      size={310}
      color="#808080"
      name="chevron.left.forwardslash.chevron.right"
      style={style}
    />
  );
}
