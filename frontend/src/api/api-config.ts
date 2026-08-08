export interface ResolveApiUrlOptions {
  envUrl?: string;
  expoHostUri?: string;
}

export function resolveApiUrl(options: ResolveApiUrlOptions = {}): string {
  const { envUrl, expoHostUri } = options;

  if (envUrl !== undefined && envUrl !== null) {
    const trimmedEnv = envUrl.trim();
    if (trimmedEnv !== '') {
      const hasHttp = trimmedEnv.startsWith('http://');
      const hasHttps = trimmedEnv.startsWith('https://');

      if (!hasHttp && !hasHttps) {
        throw new Error(
          `Invalid EXPO_PUBLIC_API_URL: '${envUrl}'. Must start with 'http://' or 'https://'.`
        );
      }

      let cleanUrl = trimmedEnv;
      while (cleanUrl.endsWith('/')) {
        cleanUrl = cleanUrl.slice(0, -1);
      }

      const afterProtocol = hasHttp ? cleanUrl.slice(7) : cleanUrl.slice(8);
      const hostnamePart = afterProtocol.split('/')[0].split(':')[0].trim();

      if (!hostnamePart) {
        throw new Error(
          `Invalid EXPO_PUBLIC_API_URL: '${envUrl}'. Missing valid hostname.`
        );
      }

      return cleanUrl;
    }
  }

  if (expoHostUri && expoHostUri.trim() !== '') {
    let host = expoHostUri.trim();
    if (host.includes('://')) {
      host = host.split('://')[1];
    }
    const hostname = host.split(':')[0];
    if (hostname && hostname.trim() !== '') {
      return `http://${hostname.trim()}:8000/api/v1`;
    }
  }

  return 'http://localhost:8000/api/v1';
}
