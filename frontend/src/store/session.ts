import { create } from 'zustand';
import client from '../api/client';
import { Session } from '../types';
import { reportApiError } from '../services/error-feedback';

interface SessionState {
  sessions: Session[];
  isLoading: boolean;
  fetchSessions: () => Promise<boolean>;
  createSession: (sessionData: {
    student_id?: number;
    tutor_id: number;
    service_type_id: number;
    scheduled_at: string;
    notes?: string;
    location?: string;
    status?: string;
    title?: string;
  }) => Promise<Session>;
  updateSessionStatus: (
    sessionId: number,
    status: string,
    notes?: string
  ) => Promise<void>;
}

export const useSessionStore = create<SessionState>((set) => ({
  sessions: [],
  isLoading: false,
  fetchSessions: async (): Promise<boolean> => {
    set({ isLoading: true });
    try {
      const response = await client.get<Session[]>('/sessions/');
      set({ sessions: response.data });
      return true;
    } catch (error) {
      reportApiError(error, 'errors.loadSessions', { notify: false });
      return false;
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
      reportApiError(error, 'errors.createSession', { notify: false });
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
      reportApiError(error, 'errors.updateSession', { notify: false });
      throw error;
    } finally {
      set({ isLoading: false });
    }
  },
}));
