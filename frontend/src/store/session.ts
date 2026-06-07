import { create } from 'zustand';
import client from '../api/client';
import { Session } from '../types';

interface SessionState {
  sessions: Session[];
  isLoading: boolean;
  fetchSessions: () => Promise<void>;
  createSession: (sessionData: {
    student_id: number;
    tutor_id: number;
    service_type_id: number;
    scheduled_at: string;
    notes?: string;
  }) => Promise<Session>;
  updateSessionStatus: (
    sessionId: number,
    status: 'confirmada' | 'completada' | 'cancelada',
    notes?: string
  ) => Promise<void>;
}

export const useSessionStore = create<SessionState>((set, get) => ({
  sessions: [],
  isLoading: false,
  fetchSessions: async () => {
    set({ isLoading: true });
    try {
      const response = await client.get<Session[]>('/sessions/');
      set({ sessions: response.data });
    } catch (error) {
      console.error('Failed to fetch sessions:', error);
    } finally {
      set({ isLoading: false });
    }
  },
  createSession: async (sessionData) => {
    set({ isLoading: true });
    try {
      const response = await client.post<Session>('/sessions/', sessionData);
      set((state) => ({ sessions: [response.data, ...state.sessions] }));
      return response.data;
    } catch (error) {
      console.error('Failed to create session:', error);
      throw error;
    } finally {
      set({ isLoading: false });
    }
  },
  updateSessionStatus: async (sessionId, status, notes) => {
    set({ isLoading: true });
    try {
      const response = await client.put<Session>(`/sessions/${sessionId}`, {
        status,
        notes,
      });
      set((state) => ({
        sessions: state.sessions.map((s) =>
          s.id === sessionId ? response.data : s
        ),
      }));
    } catch (error) {
      console.error('Failed to update session status:', error);
      throw error;
    } finally {
      set({ isLoading: false });
    }
  },
}));
