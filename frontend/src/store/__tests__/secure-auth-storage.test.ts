import AsyncStorage from '@react-native-async-storage/async-storage';
import * as SecureStore from 'expo-secure-store';

import { secureAuthStorage } from '../secure-auth-storage';

jest.mock('@react-native-async-storage/async-storage', () => ({
  __esModule: true,
  default: {
    getItem: jest.fn(),
    setItem: jest.fn(),
    removeItem: jest.fn(),
  },
}));

jest.mock('expo-secure-store', () => ({
  getItemAsync: jest.fn(),
  setItemAsync: jest.fn(),
  deleteItemAsync: jest.fn(),
}));

const asyncGet = AsyncStorage.getItem as jest.Mock;
const asyncSet = AsyncStorage.setItem as jest.Mock;
const asyncRemove = AsyncStorage.removeItem as jest.Mock;
const secureGet = SecureStore.getItemAsync as jest.Mock;
const secureSet = SecureStore.setItemAsync as jest.Mock;
const secureDelete = SecureStore.deleteItemAsync as jest.Mock;

const CLAVE = 'tutoria-auth-storage';

function blob(state: Record<string, unknown>) {
  return JSON.stringify({ state, version: 0 });
}

/**
 * El token JWT se persistía en AsyncStorage, que es texto plano. Estas pruebas fijan
 * el reparto: el token va al almacén cifrado y **no** queda una segunda copia en
 * claro, que anularía la protección.
 */
describe('secureAuthStorage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    secureSet.mockResolvedValue(undefined);
    secureDelete.mockResolvedValue(undefined);
    asyncSet.mockResolvedValue(undefined);
    asyncRemove.mockResolvedValue(undefined);
  });

  describe('al guardar', () => {
    it('manda el token a SecureStore', async () => {
      await secureAuthStorage.setItem(
        CLAVE,
        blob({ token: 'jwt.de.prueba', user: { id: 1 } })
      );

      expect(secureSet).toHaveBeenCalledWith('tutoria.auth.token', 'jwt.de.prueba');
    });

    it('no deja el token en el bloque de texto plano', async () => {
      await secureAuthStorage.setItem(
        CLAVE,
        blob({ token: 'jwt.de.prueba', user: { id: 1 } })
      );

      const guardado = asyncSet.mock.calls[0][1];
      expect(guardado).not.toContain('jwt.de.prueba');
      expect(JSON.parse(guardado).state.token).toBeNull();
    });

    it('conserva el resto del estado en AsyncStorage', async () => {
      await secureAuthStorage.setItem(
        CLAVE,
        blob({ token: 'jwt', user: { id: 7, email: 'a@b.pe' }, profileImage: 'file://x' })
      );

      const guardado = JSON.parse(asyncSet.mock.calls[0][1]);
      expect(guardado.state.user).toEqual({ id: 7, email: 'a@b.pe' });
      expect(guardado.state.profileImage).toBe('file://x');
    });

    it('borra el token cifrado al cerrar sesión', async () => {
      await secureAuthStorage.setItem(CLAVE, blob({ token: null, user: null }));

      expect(secureDelete).toHaveBeenCalledWith('tutoria.auth.token');
      expect(secureSet).not.toHaveBeenCalled();
    });

    it('un fallo del Keychain no deja el token en claro', async () => {
      secureSet.mockRejectedValue(new Error('keychain caído'));

      await secureAuthStorage.setItem(CLAVE, blob({ token: 'jwt.secreto', user: null }));

      expect(asyncSet.mock.calls[0][1]).not.toContain('jwt.secreto');
    });
  });

  describe('al leer', () => {
    it('recompone el estado uniendo ambos almacenes', async () => {
      asyncGet.mockResolvedValue(blob({ token: null, user: { id: 3 } }));
      secureGet.mockResolvedValue('jwt.recuperado');

      const leido = JSON.parse((await secureAuthStorage.getItem(CLAVE)) as string);

      expect(leido.state.token).toBe('jwt.recuperado');
      expect(leido.state.user).toEqual({ id: 3 });
    });

    it('devuelve null si no hay nada guardado', async () => {
      asyncGet.mockResolvedValue(null);

      await expect(secureAuthStorage.getItem(CLAVE)).resolves.toBeNull();
    });

    it('deja la sesión sin token si el Keychain falla, en vez de romper el arranque', async () => {
      asyncGet.mockResolvedValue(blob({ token: null, user: { id: 3 } }));
      secureGet.mockRejectedValue(new Error('keychain caído'));

      const leido = JSON.parse((await secureAuthStorage.getItem(CLAVE)) as string);

      expect(leido.state.token).toBeNull();
    });
  });

  describe('al limpiar', () => {
    it('borra los dos almacenes', async () => {
      await secureAuthStorage.removeItem(CLAVE);

      expect(secureDelete).toHaveBeenCalledWith('tutoria.auth.token');
      expect(asyncRemove).toHaveBeenCalledWith(CLAVE);
    });
  });
});
