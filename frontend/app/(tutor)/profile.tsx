import React from 'react';
import { ScrollView, Platform } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useProfile } from '@/src/components/profile/useProfile';
import { ProfileHeader } from '@/src/components/profile/ProfileHeader';
import { AssignedTutorCard } from '@/src/components/profile/AssignedTutorCard';
import { ProfileMenu } from '@/src/components/profile/ProfileMenu';
import { useTheme } from '@/src/theme/ThemeContext';

export default function ProfileScreen() {
  const { colors } = useTheme();
  const insets = useSafeAreaInsets();

  const minimumBottomPadding = Platform.OS === 'ios' ? 24 : 12;
  const bottomPadding = Math.max(insets.bottom, minimumBottomPadding);
  const tabBarBaseHeight = 62;
  const totalTabBarHeight = tabBarBaseHeight + bottomPadding;
  const scrollBottomPadding = totalTabBarHeight + 24;

  const { user, assignedTutors, handleLogout } = useProfile();

  return (
    <ScrollView
      style={{ flex: 1, backgroundColor: colors.background }}
      contentContainerStyle={{ paddingBottom: scrollBottomPadding }}
      showsVerticalScrollIndicator={false}
    >
      <ProfileHeader user={user} />

      {user?.role === 'estudiante' ? (
        <AssignedTutorCard assignedTutors={assignedTutors} />
      ) : null}

      <ProfileMenu onLogout={handleLogout} />
    </ScrollView>
  );
}
