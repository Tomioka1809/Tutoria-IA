import { Platform } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

/**
 * Geometria de la barra de pestanas, derivada del safe area del dispositivo.
 *
 * Los valores replican exactamente el calculo que hacen (estudiante)/_layout.tsx y
 * (tutor)/_layout.tsx para dimensionar la tabBar, de modo que el contenido scrolleable
 * termine justo por encima de ella en lugar de quedar tapado.
 */
export function useTabBarPadding() {
  const insets = useSafeAreaInsets();

  const minimumBottomPadding = Platform.OS === 'ios' ? 24 : 12;
  const bottomPadding = Math.max(insets.bottom, minimumBottomPadding);
  const tabBarBaseHeight = 62;
  const tabBarHeight = tabBarBaseHeight + bottomPadding;

  return {
    /** Alto total de la tabBar, insets incluidos. */
    tabBarHeight,
    /** paddingBottom para contentContainerStyle: la tabBar mas un respiro de 24. */
    scrollBottomPadding: tabBarHeight + 24,
  };
}
