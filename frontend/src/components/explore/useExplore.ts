// src/components/explore/useExplore.ts
import { Platform, StyleSheet } from 'react-native';
import { Fonts } from '@/constants/theme';

export function useExplore() {
  const styles = StyleSheet.create({
    headerImage: {
      color: '#808080',
      bottom: -90,
      left: -35,
      position: 'absolute',
    },
    titleContainer: {
      flexDirection: 'row',
      gap: 8,
    },
  });

  return {
    styles,
    Fonts,
    Platform,
  };
}
