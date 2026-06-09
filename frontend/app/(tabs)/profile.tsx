// app/(tabs)/profile.tsx
import React from 'react';
import { View, ScrollView } from 'react-native';
import { useProfile } from '@/src/components/profile/useProfile';
import { ProfileHeader } from '@/src/components/profile/ProfileHeader';
import { AssignedTutorCard } from '@/src/components/profile/AssignedTutorCard';
import { ProfileMenu } from '@/src/components/profile/ProfileMenu';

export default function ProfileScreen() {
  const { user, assignedTutors, handleLogout } = useProfile();

  return (
    <ScrollView
      className="flex-1 bg-[#F5F5FB]"
      contentContainerStyle={{ paddingBottom: 60 }}
      showsVerticalScrollIndicator={false}
    >
      <ProfileHeader user={user} />

      {/* Spacer to handle the overlay card offset */}
      <View className="h-20" />

      {user?.role === 'estudiante' ? (
        <AssignedTutorCard assignedTutors={assignedTutors} />
      ) : null}

      <ProfileMenu onLogout={handleLogout} />
    </ScrollView>
  );
}
