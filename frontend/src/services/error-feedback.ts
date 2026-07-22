import { Alert } from 'react-native';
import i18n from '../i18n';
import { normalizeApiError } from '../api/api-error';
import type { NormalizedApiError } from '../api/api-error';

const recentFingerprints = new Map<string, number>();

export function reportApiError(
  error: unknown,
  fallbackMessageKey?: string,
  options?: {
    notify?: boolean;
  }
): NormalizedApiError {
  const normErr = normalizeApiError(error, fallbackMessageKey);
  const notify = options?.notify ?? true;

  if (!notify) {
    return normErr;
  }

  const now = Date.now();
  const fingerprint = `${normErr.kind}:${normErr.status}:${normErr.messageKey}:${normErr.detail || ''}`;

  for (const [key, timestamp] of recentFingerprints.entries()) {
    if (now - timestamp >= 1500) {
      recentFingerprints.delete(key);
    }
  }

  if (recentFingerprints.has(fingerprint)) {
    return normErr;
  }

  recentFingerprints.set(fingerprint, now);

  const title = i18n.t('errors.title');
  const baseMessage = i18n.t(normErr.messageKey);
  const displayMessage = normErr.detail
    ? `${baseMessage}: ${normErr.detail}`
    : baseMessage;

  Alert.alert(title, displayMessage, [{ text: i18n.t('errors.close') }]);

  return normErr;
}
