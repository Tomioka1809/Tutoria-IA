// app/(tabs)/profile.tsx
import React from 'react';
import { ScrollView } from 'react-native';
import { useProfile } from '@/src/components/profile/useProfile';
import { ProfileHeader } from '@/src/components/profile/ProfileHeader';
import { AssignedTutorCard } from '@/src/components/profile/AssignedTutorCard';
import { ProfileMenu } from '@/src/components/profile/ProfileMenu';

export default function ProfileScreen() {
  const { user, assignedTutors, handleLogout } = useProfile();

  return (
    <ScrollView
      style={{ flex: 1, backgroundColor: '#F8F7FC' }}
      contentContainerStyle={{ paddingBottom: 130 }}
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
