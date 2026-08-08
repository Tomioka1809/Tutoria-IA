import React, { createContext, useContext, useEffect, useState } from 'react';
import { useColorScheme as useNativeColorScheme } from 'react-native';
import { useColorScheme as useNWColorScheme } from 'nativewind';
import { lightTheme, darkTheme, ThemeColors } from './colors';
import { usePreferencesStore } from '../store/preferences';

interface ThemeContextType {
  isDark: boolean;
  colors: ThemeColors;
}

const ThemeContext = createContext<ThemeContextType>({
  isDark: false,
  colors: lightTheme,
});

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const systemColorScheme = useNativeColorScheme();
  const { theme } = usePreferencesStore();
  const { setColorScheme } = useNWColorScheme();
  const [isDark, setIsDark] = useState(false);

  useEffect(() => {
    const isDarkNow = theme === 'system' ? systemColorScheme === 'dark' : theme === 'dark';
    setIsDark(isDarkNow);
    setColorScheme(isDarkNow ? 'dark' : 'light');
  }, [theme, systemColorScheme, setColorScheme]);

  const colors = isDark ? darkTheme : lightTheme;

  return (
    <ThemeContext.Provider value={{ isDark, colors }}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = () => useContext(ThemeContext);
