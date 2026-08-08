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

export interface ParsedDateTime {
  startsAt: Date;
  dateStr: string;
  timeStr: string;
}

export function isValidLocalDateTimeComponents(
  year: number,
  month: number,
  day: number,
  hour: number = 0,
  minute: number = 0,
  second: number = 0,
  millisecond: number = 0
): boolean {
  if (
    !Number.isInteger(year) ||
    !Number.isInteger(month) ||
    !Number.isInteger(day) ||
    !Number.isInteger(hour) ||
    !Number.isInteger(minute) ||
    !Number.isInteger(second) ||
    !Number.isInteger(millisecond)
  ) {
    return false;
  }

  if (
    year < 1900 ||
    year > 2100 ||
    month < 1 ||
    month > 12 ||
    day < 1 ||
    day > 31 ||
    hour < 0 ||
    hour > 23 ||
    minute < 0 ||
    minute > 59 ||
    second < 0 ||
    second > 59 ||
    millisecond < 0 ||
    millisecond > 999
  ) {
    return false;
  }

  const d = new Date(year, month - 1, day, hour, minute, second, millisecond);

  if (
    d.getFullYear() !== year ||
    d.getMonth() !== month - 1 ||
    d.getDate() !== day ||
    d.getHours() !== hour ||
    d.getMinutes() !== minute ||
    d.getSeconds() !== second ||
    d.getMilliseconds() !== millisecond
  ) {
    return false;
  }

  return true;
}

export function parseScheduledAt(scheduledAtStr: string): ParsedDateTime | null {
  if (!scheduledAtStr || typeof scheduledAtStr !== 'string') return null;

  const raw = scheduledAtStr.trim();
  let d: Date;

  const dateOnlyRegex = /^\d{4}-\d{2}-\d{2}$/;
  const localDateTimeRegex = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2}(\.\d+)?)?$/;
  const isoZonedRegex = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2}(\.\d+)?)?(Z|[+-]\d{2}:\d{2})$/;

  if (dateOnlyRegex.test(raw)) {
    const [y, m, day] = raw.split('-').map(Number);
    if (!isValidLocalDateTimeComponents(y, m, day, 0, 0, 0, 0)) {
      return null;
    }
    d = new Date(y, m - 1, day, 0, 0, 0, 0);
  } else if (localDateTimeRegex.test(raw)) {
    const [datePart, timePart] = raw.split('T');
    const [y, m, day] = datePart.split('-').map(Number);
    const timeSubParts = timePart.split(':');
    const h = Number(timeSubParts[0]);
    const min = Number(timeSubParts[1]);

    let sec = 0;
    let ms = 0;
    if (timeSubParts.length > 2) {
      const secParts = timeSubParts[2].split('.');
      sec = Number(secParts[0]);
      if (secParts.length > 1 && secParts[1]) {
        const msPadded = (secParts[1] + '000').substring(0, 3);
        ms = Number(msPadded);
      }
    }

    if (!isValidLocalDateTimeComponents(y, m, day, h, min, sec, ms)) {
      return null;
    }
    d = new Date(y, m - 1, day, h, min, sec, ms);
  } else if (isoZonedRegex.test(raw)) {
    let cleanIso = raw;
    if (raw.endsWith('Z')) {
      cleanIso = raw.slice(0, -1);
    } else {
      cleanIso = raw.slice(0, -6);
    }

    const [datePart, timePart] = cleanIso.split('T');
    const [y, m, day] = datePart.split('-').map(Number);
    const timeSubParts = timePart.split(':');
    const h = Number(timeSubParts[0]);
    const min = Number(timeSubParts[1]);

    let sec = 0;
    let ms = 0;
    if (timeSubParts.length > 2) {
      const secParts = timeSubParts[2].split('.');
      sec = Number(secParts[0]);
      if (secParts.length > 1 && secParts[1]) {
        const msPadded = (secParts[1] + '000').substring(0, 3);
        ms = Number(msPadded);
      }
    }

    if (!isValidLocalDateTimeComponents(y, m, day, h, min, sec, ms)) {
      return null;
    }

    d = new Date(raw);
  } else {
    d = new Date(raw);
  }

  if (Number.isNaN(d.getTime())) return null;

  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  const hours = String(d.getHours()).padStart(2, '0');
  const minutes = String(d.getMinutes()).padStart(2, '0');

  const dateStr = `${year}-${month}-${day}`;
  const timeStr = `${hours}:${minutes}`;

  return {
    startsAt: d,
    dateStr,
    timeStr,
  };
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

  if (!isValidLocalDateTimeComponents(year, month, day, hours, minutes, 0, 0)) {
    return null;
  }

  return new Date(year, month - 1, day, hours, minutes, 0, 0);
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

  const parsed = parseScheduledAt(session.scheduled_at);
  if (!parsed) return null;

  const { startsAt, dateStr, timeStr } = parsed;

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
