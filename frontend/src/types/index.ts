export interface User {
  id: number;
  full_name: string;
  email: string;
  student_code?: string;
  role: 'estudiante' | 'tutor' | 'admin';
  school?: string;
  semester?: string;
  current_semester?: number;
  academic_status?: string;
  tutor_code?: string;
  phone_number?: string;
  expertise_areas?: string;
  office_location?: string;
}

export interface ServiceType {
  id: number;
  name: string;
  description?: string;
  icon?: string;
}

export interface TutorAssignment {
  id: number;
  student_id: number;
  tutor_id: number;
  service_type_id: number;
  student?: User;
  tutor?: User;
  service_type?: ServiceType;
}

export interface Session {
  id: number;
  student_id: number;
  tutor_id: number;
  service_type_id: number;
  scheduled_at: string;
  status: string;
  notes?: string;
  title?: string;
  location?: string;
  student: { id: number; full_name: string; email: string };
  tutor: { id: number; full_name: string; email: string };
  service_type: { id: number; name: string; icon?: string };
}

export interface Event {
  id: number;
  created_by: number;
  session_id?: number;
  title: string;
  starts_at: string;
  ends_at: string;
  type: string; // e.g. "tutoria", "examen", "tarea"
  creator?: User;
  session?: Session;
}

export interface Streak {
  id: number;
  student_id: number;
  current_streak: number;
  max_streak: number;
  last_session_date?: string;
}

export interface Notification {
  id: number;
  user_id: number;
  title: string;
  body: string;
  type: string; // e.g. "session", "streak", "system"
  is_read: boolean;
  created_at: string;
}

export interface Message {
  id: number;
  conversation_id: number;
  role: 'user' | 'assistant';
  content: string;
  sent_at: string;
}

export interface Conversation {
  id: number;
  student_id: number;
  created_at: string;
  messages: Message[];
}
