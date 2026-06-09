// src/components/profile/useProfile.ts
import { useState, useEffect } from 'react';
import { useAuthStore } from '@/src/store/auth';
import client from '@/src/api/client';
import { TutorAssignment } from '@/src/types';

export function useProfile() {
  const { user, logout } = useAuthStore();
  const [assignedTutors, setAssignedTutors] = useState<TutorAssignment[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (user?.role === 'estudiante') {
      fetchAssignedTutor();
    }
  }, []);

  const fetchAssignedTutor = async () => {
    setIsLoading(true);
    try {
      const response = await client.get('/tutors/assigned');
      setAssignedTutors(response.data);
    } catch (e) {
      console.error('Failed to load assigned tutor', e);
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
  };

  return {
    user,
    assignedTutors,
    isLoading,
    handleLogout,
  };
}
