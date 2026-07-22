export type CalendarItemSource = 'local_activity' | 'tutoring_session';

export interface CalendarItem {
  id: string;
  source: CalendarItemSource;
  title: string;
  name: string;
  startsAt: Date;
  type: string;
  dateStr: string;
  timeStr: string;
  date: string;
  time: string;
  isBackend: boolean;
  rawId: number;
  status?: string;
  localActivityId?: string;
  sessionId?: number;
  location?: string;
  notes?: string;
  tutorName?: string;
  studentName?: string;
}

export interface LocalActivityInput {
  id: string | number;
  name?: string;
  type?: string;
  date?: string;
  time?: string;
  notes?: string;
  location?: string;
  status?: string;
}

export interface TutoringSessionInput {
  id: number;
  scheduled_at: string;
  title?: string;
  status?: string;
  notes?: string;
  location?: string;
  tutor?: { full_name: string };
  student?: { full_name: string };
  service_type?: { name: string };
}

export function parseLocalActivityDate(activity: { date?: string; time?: string }): Date | null {
  if (!activity || typeof activity.date !== 'string' || typeof activity.time !== 'string') {
    return null;
  }

  const dateParts = activity.date.split('-').map(Number);
  const timeParts = activity.time.split(':').map(Number);

  if (dateParts.length !== 3 || timeParts.length < 2) {
    return null;
  }

  const [year, month, day] = dateParts;
  const [hours, minutes] = timeParts;

  if (
    isNaN(year) ||
    isNaN(month) ||
    isNaN(day) ||
    isNaN(hours) ||
    isNaN(minutes) ||
    year < 1900 ||
    year > 2100 ||
    month < 1 ||
    month > 12 ||
    day < 1 ||
    day > 31 ||
    hours < 0 ||
    hours > 23 ||
    minutes < 0 ||
    minutes > 59
  ) {
    return null;
  }

  const parsedDate = new Date(year, month - 1, day, hours, minutes, 0, 0);

  if (
    parsedDate.getFullYear() !== year ||
    parsedDate.getMonth() !== month - 1 ||
    parsedDate.getDate() !== day
  ) {
    return null;
  }

  return parsedDate;
}

export function shouldRetainStoredActivity(
  activity: { date?: string; time?: string },
  now: Date = new Date()
): boolean {
  const parsedDate = parseLocalActivityDate(activity);
  if (!parsedDate) {
    return true;
  }
  return parsedDate.getTime() >= now.getTime();
}

export function mapActivityToCalendarItem(activity: LocalActivityInput): CalendarItem | null {
  const startsAt = parseLocalActivityDate(activity);
  if (!startsAt) return null;

  const rawIdStr = String(activity.id);
  const title = activity.name || 'Actividad';
  const type = activity.type || 'Trabajos';
  const dateStr = activity.date || '';
  const timeStr = activity.time || '';

  return {
    id: `activity:${rawIdStr}`,
    source: 'local_activity',
    title,
    name: title,
    startsAt,
    type,
    dateStr,
    timeStr,
    date: dateStr,
    time: timeStr,
    isBackend: false,
    rawId: 0,
    status: activity.status,
    localActivityId: rawIdStr,
    location: activity.location,
    notes: activity.notes,
  };
}

export function mapSessionToCalendarItem(session: TutoringSessionInput): CalendarItem | null {
  if (!session || !session.scheduled_at) return null;

  const startsAt = new Date(session.scheduled_at);
  if (isNaN(startsAt.getTime())) return null;

  const serviceName = session.service_type?.name || 'Tutoría Académica';
  let type = 'Tutoría Académica';
  if (serviceName.includes('Personal')) {
    type = 'Tutoría Personal';
  } else if (serviceName.includes('Profesional')) {
    type = 'Tutoría Profesional';
  } else if (serviceName.includes('Tarea') || serviceName.includes('Entrega') || serviceName.includes('Trabajo')) {
    type = 'Trabajos';
  }

  const title = session.title || session.notes || serviceName;
  const dateStr = session.scheduled_at.split('T')[0] || '';
  const timePart = session.scheduled_at.split('T')[1] || '';
  const timeStr = timePart.substring(0, 5) || '00:00';

  return {
    id: `session:${session.id}`,
    source: 'tutoring_session',
    title,
    name: title,
    startsAt,
    type,
    dateStr,
    timeStr,
    date: dateStr,
    time: timeStr,
    isBackend: true,
    rawId: session.id,
    status: session.status,
    sessionId: session.id,
    location: session.location,
    notes: session.notes,
    tutorName: session.tutor?.full_name,
    studentName: session.student?.full_name,
  };
}

export function buildCalendarItems(
  activities: LocalActivityInput[] = [],
  sessions: TutoringSessionInput[] = []
): CalendarItem[] {
  const items: CalendarItem[] = [];

  for (const act of activities) {
    if (act) {
      const item = mapActivityToCalendarItem(act);
      if (item) {
        items.push(item);
      }
    }
  }

  for (const sess of sessions) {
    if (sess && sess.status !== 'cancelada') {
      const item = mapSessionToCalendarItem(sess);
      if (item) {
        items.push(item);
      }
    }
  }

  items.sort((a, b) => {
    const diff = a.startsAt.getTime() - b.startsAt.getTime();
    if (diff !== 0) return diff;
    return a.id.localeCompare(b.id);
  });

  return items;
}

export function isUpcomingCalendarItem(item: CalendarItem, now: Date = new Date()): boolean {
  return item.startsAt.getTime() >= now.getTime();
}
