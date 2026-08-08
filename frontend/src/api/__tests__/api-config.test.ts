import { resolveApiUrl } from '../api-config';

/**
 * `resolveApiUrl` decide contra qué backend habla la app. Es la pieza que hace que
 * el celular encuentre la PC sin configurar nada, y hasta ahora sólo la cubría un
 * script de grep. Si se equivoca, la app no conecta y el síntoma es indistinguible
 * de un problema de red.
 */
describe('resolveApiUrl', () => {
  describe('con EXPO_PUBLIC_API_URL definida', () => {
    it('la usa tal cual cuando es válida', () => {
      expect(resolveApiUrl({ envUrl: 'https://api.unsaac.edu.pe/api/v1' })).toBe(
        'https://api.unsaac.edu.pe/api/v1'
      );
    });

    it('quita las barras finales', () => {
      expect(resolveApiUrl({ envUrl: 'https://api.unsaac.edu.pe/api/v1///' })).toBe(
        'https://api.unsaac.edu.pe/api/v1'
      );
    });

    it('acepta http además de https', () => {
      expect(resolveApiUrl({ envUrl: 'http://192.168.1.5:8000/api/v1' })).toBe(
        'http://192.168.1.5:8000/api/v1'
      );
    });

    it('rechaza una URL sin protocolo en vez de construir uno inválido', () => {
      expect(() => resolveApiUrl({ envUrl: 'api.unsaac.edu.pe' })).toThrow(
        /must start with/i
      );
    });

    it('rechaza un protocolo que no sea http o https', () => {
      expect(() => resolveApiUrl({ envUrl: 'ftp://api.unsaac.edu.pe' })).toThrow();
    });

    it('rechaza una URL sin host', () => {
      expect(() => resolveApiUrl({ envUrl: 'https://' })).toThrow(/hostname/i);
    });

    it('ignora la variable vacía y cae al siguiente método', () => {
      expect(resolveApiUrl({ envUrl: '   ', expoHostUri: '192.168.1.5:8081' })).toBe(
        'http://192.168.1.5:8000/api/v1'
      );
    });
  });

  describe('sin variable, deduciendo de Expo', () => {
    it('toma la IP de LAN del host de Expo y le pone el puerto del backend', () => {
      expect(resolveApiUrl({ expoHostUri: '192.168.1.5:8081' })).toBe(
        'http://192.168.1.5:8000/api/v1'
      );
    });

    it('descarta el esquema si el host lo trae', () => {
      expect(resolveApiUrl({ expoHostUri: 'exp://10.0.0.7:8081' })).toBe(
        'http://10.0.0.7:8000/api/v1'
      );
    });

    it('funciona con un host sin puerto', () => {
      expect(resolveApiUrl({ expoHostUri: '192.168.1.5' })).toBe(
        'http://192.168.1.5:8000/api/v1'
      );
    });
  });

  describe('sin ninguna pista', () => {
    it('cae a localhost', () => {
      expect(resolveApiUrl()).toBe('http://localhost:8000/api/v1');
      expect(resolveApiUrl({})).toBe('http://localhost:8000/api/v1');
      expect(resolveApiUrl({ expoHostUri: '   ' })).toBe('http://localhost:8000/api/v1');
    });
  });
});
