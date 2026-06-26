export const lightTheme = {
  primary: '#9A3BEE',
  primaryLight: '#F3E8FF',
  primaryDark: '#7B2FD4',
  background: '#F8F7FC',
  surface: '#FFFFFF',
  text: '#111130',
  textSecondary: '#8E8EA0',
  border: '#EEEDFE',
  danger: '#EF4444',
  success: '#22C55E',
  warning: '#F59E0B',
};

export const darkTheme = {
  primary: '#9A3BEE',
  primaryLight: '#3B1A5C', // darker purple for backgrounds
  primaryDark: '#B366FF',  // lighter purple for hover/pressed
  background: '#121212',
  surface: '#1E1E1E',
  text: '#FFFFFF',
  textSecondary: '#A0A0A0',
  border: '#2C2C2C',
  danger: '#F87171',
  success: '#4ADE80',
  warning: '#FBBF24',
};

export type ThemeColors = typeof lightTheme;
