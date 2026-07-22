import type { TutorAssignment, User } from '@/src/types';

export type AssignedTutorResolutionStatus = 'none' | 'available' | 'ambiguous';

export interface AssignedTutorResolution {
  status: AssignedTutorResolutionStatus;
  tutor?: User;
}

export function resolveAssignedTutor(assignments: unknown): AssignedTutorResolution {
  if (!Array.isArray(assignments)) {
    return { status: 'none' };
  }

  const candidates: { tutor: User; key?: string | number }[] = [];

  for (const item of assignments as Partial<TutorAssignment>[]) {
    if (!item || typeof item !== 'object') {
      continue;
    }
    const tutor = item.tutor;
    if (!tutor || typeof tutor !== 'object') {
      continue;
    }

    const rawName = tutor.full_name;
    if (typeof rawName !== 'string') {
      continue;
    }

    const normalizedName = rawName.trim().replace(/\s+/g, ' ');
    if (normalizedName.length === 0) {
      continue;
    }

    const normalizedTutor: User = {
      ...tutor,
      full_name: normalizedName,
    };

    let key: string | number | undefined;
    const tutorId = tutor.id as unknown;
    const itemTutorId = item.tutor_id as unknown;

    if (typeof tutorId === 'number' || (typeof tutorId === 'string' && tutorId.trim() !== '')) {
      key = tutorId as string | number;
    } else if (typeof itemTutorId === 'number' || (typeof itemTutorId === 'string' && itemTutorId.trim() !== '')) {
      key = itemTutorId as string | number;
    } else if (typeof tutor.email === 'string' && tutor.email.trim().length > 0) {
      key = tutor.email.trim().toLowerCase();
    }

    candidates.push({ tutor: normalizedTutor, key });
  }

  if (candidates.length === 0) {
    return { status: 'none' };
  }

  if (candidates.length === 1) {
    return {
      status: 'available',
      tutor: candidates[0].tutor,
    };
  }

  const hasUnreliableCandidate = candidates.some((c) => c.key === undefined);
  if (hasUnreliableCandidate) {
    return { status: 'ambiguous' };
  }

  const tutorMap = new Map<string | number, User>();
  for (const c of candidates) {
    if (!tutorMap.has(c.key!)) {
      tutorMap.set(c.key!, c.tutor);
    }
  }

  if (tutorMap.size === 1) {
    const singleTutor = Array.from(tutorMap.values())[0];
    return {
      status: 'available',
      tutor: singleTutor,
    };
  }

  return { status: 'ambiguous' };
}
