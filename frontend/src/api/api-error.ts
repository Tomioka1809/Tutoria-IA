export type ApiErrorKind =
  | 'network'
  | 'timeout'
  | 'unauthorized'
  | 'forbidden'
  | 'not_found'
  | 'conflict'
  | 'validation'
  | 'server'
  | 'unknown';

export interface NormalizedApiError {
  kind: ApiErrorKind;
  status: number | null;
  messageKey: string;
  detail?: string;
  retryable: boolean;
}

function sanitizeDetail(value: string): string | undefined {
  if (typeof value !== 'string') return undefined;

  let clean = value.replace(/\s+/g, ' ').trim();
  if (!clean) return undefined;

  const isTrace =
    /Traceback\s*\(most recent call last\):/i.test(clean) ||
    /stack\s*trace/i.test(clean) ||
    /\bat\s+[\w\$.]+\s*\(/i.test(clean) ||
    /File\s+["'][^"']+["'],\s+line\s+\d+/i.test(clean);

  if (isTrace) {
    return undefined;
  }

  const sensitiveRegex =
    /\b(Authorization|Bearer\s+[A-Za-z0-9\-_\.=]+|eyJ[A-Za-z0-9\-_=]+\.eyJ[A-Za-z0-9\-_=]+\.[A-Za-z0-9\-_=]+|Cookie|Set-Cookie|access_token|refresh_token|api_key|secret|AIza[0-9A-Za-z-_]{35}|password\s*[:=]\s*\S+)\b/i;

  if (sensitiveRegex.test(clean)) {
    return undefined;
  }

  if (clean.length > 240) {
    clean = clean.slice(0, 240).trim();
  }

  return clean.length > 0 ? clean : undefined;
}

export function normalizeApiError(
  error: unknown,
  fallbackMessageKey: string = 'errors.unknown'
): NormalizedApiError {
  let kind: ApiErrorKind = 'unknown';
  let status: number | null = null;
  let rawDetail: string | undefined = undefined;

  if (typeof error === 'object' && error !== null) {
    const errObj = error as Record<string, unknown>;
    const code = String(errObj.code || '');
    const message = String(errObj.message || '');
    const name = String(errObj.name || '');

    const isTimeout =
      code === 'ECONNABORTED' ||
      code === 'ETIMEDOUT' ||
      message.toLowerCase().includes('timeout') ||
      name.toLowerCase().includes('timeout');

    if (errObj.response && typeof errObj.response === 'object') {
      const respObj = errObj.response as Record<string, unknown>;
      status = typeof respObj.status === 'number' ? respObj.status : null;
      const data = respObj.data;

      if (data && typeof data === 'object') {
        const dataObj = data as Record<string, unknown>;
        if (typeof dataObj.detail === 'string') {
          rawDetail = dataObj.detail;
        } else if (typeof dataObj.message === 'string') {
          rawDetail = dataObj.message;
        } else if (Array.isArray(dataObj.detail)) {
          const msgs = dataObj.detail
            .map((item: unknown) =>
              typeof item === 'object' && item !== null && 'msg' in item
                ? String((item as { msg: unknown }).msg)
                : ''
            )
            .filter((m: string) => m.length > 0);
          if (msgs.length > 0) {
            rawDetail = msgs.join('; ');
          }
        }
      }

      if (isTimeout) {
        kind = 'timeout';
      } else if (status === 401) {
        kind = 'unauthorized';
      } else if (status === 403) {
        kind = 'forbidden';
      } else if (status === 404) {
        kind = 'not_found';
      } else if (status === 409) {
        kind = 'conflict';
      } else if (status === 400 || status === 422) {
        kind = 'validation';
      } else if (status !== null && status >= 500 && status <= 599) {
        kind = 'server';
      } else {
        kind = 'unknown';
      }
    } else if (isTimeout) {
      kind = 'timeout';
    } else if (
      errObj.request ||
      errObj.isAxiosError ||
      message.toLowerCase().includes('network error')
    ) {
      kind = 'network';
    }
  }

  let safeDetail: string | undefined = undefined;
  if ((kind === 'validation' || kind === 'conflict') && rawDetail) {
    safeDetail = sanitizeDetail(rawDetail);
  }

  const retryableMap: Record<ApiErrorKind, boolean> = {
    network: true,
    timeout: true,
    server: true,
    unauthorized: false,
    forbidden: false,
    not_found: false,
    conflict: false,
    validation: false,
    unknown: false,
  };

  const messageKeyMap: Record<ApiErrorKind, string> = {
    network: 'errors.network',
    timeout: 'errors.timeout',
    unauthorized: 'errors.unauthorized',
    forbidden: 'errors.forbidden',
    not_found: 'errors.notFound',
    conflict: 'errors.conflict',
    validation: 'errors.validation',
    server: 'errors.server',
    unknown: fallbackMessageKey || 'errors.unknown',
  };

  return {
    kind,
    status,
    messageKey: messageKeyMap[kind],
    detail: safeDetail,
    retryable: retryableMap[kind],
  };
}
