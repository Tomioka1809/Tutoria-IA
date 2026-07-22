import { useState, useEffect, useCallback } from 'react';
import { useAuthStore } from '@/src/store/auth';
import client from '@/src/api/client';
import { TutorAssignment } from '@/src/types';
import { reportApiError } from '@/src/services/error-feedback';

export function useProfile() {
  const user = useAuthStore((state) => state.user);
  const logout = useAuthStore((state) => state.logout);
  const userRole = user?.role;

  const [assignedTutors, setAssignedTutors] = useState<TutorAssignment[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [assignedTutorLoadError, setAssignedTutorLoadError] = useState(false);

  const fetchAssignedTutor = useCallback(async () => {
    setIsLoading(true);
    setAssignedTutorLoadError(false);
    try {
      const response = await client.get<TutorAssignment[]>('/tutors/assigned');
      if (Array.isArray(response.data)) {
        setAssignedTutors(response.data);
        setAssignedTutorLoadError(false);
      } else {
        setAssignedTutors([]);
        setAssignedTutorLoadError(true);
      }
    } catch (e) {
      setAssignedTutors([]);
      setAssignedTutorLoadError(true);
      reportApiError(e, 'errors.loadAssignedTutor');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (userRole === 'estudiante') {
      fetchAssignedTutor();
    }
  }, [userRole, fetchAssignedTutor]);

  const handleLogout = () => {
    logout();
  };

  return {
    user,
    assignedTutors,
    isLoading,
    assignedTutorLoadError,
    handleLogout,
  };
}
