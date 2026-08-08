import AsyncStorage from '@react-native-async-storage/async-storage';
import * as SecureStore from 'expo-secure-store';
import { Platform } from 'react-native';
import type { StateStorage } from 'zustand/middleware';

/**
 * Almacenamiento del estado de sesión: el token va cifrado, el resto no.
 *
 * Antes el bloque entero —token JWT incluido— se persistía en `AsyncStorage`, que es
 * texto plano: en Android es un XML dentro del sandbox de la app, legible en cuanto el
 * dispositivo está rooteado o se saca un backup. `expo-secure-store` lo respalda con
 * el Keychain en iOS y el Keystore en Android.
 *
 * **Sólo el token se guarda ahí, no el objeto completo.** SecureStore documenta que
 * los payloads grandes pueden ser rechazados por la plataforma (históricamente iOS
 * cortaba alrededor de 2048 bytes), y el estado persistido incluye el perfil y el URI
 * de la foto. Un JWT ronda los 250 bytes y entra sobrado; el resto no es sensible y
 * se queda en `AsyncStorage`.
 *
 * En web SecureStore no existe, así que se usa `AsyncStorage` para todo. Es una
 * degradación consciente: el soporte web del proyecto es parcial y allí el
 * equivalente real sería una cookie `httpOnly`, que exige cambios en el backend.
 */

const TOKEN_KEY = 'tutoria.auth.token';

// SecureStore no está disponible en web; ahí todo cae a AsyncStorage.
const secureStoreDisponible = Platform.OS !== 'web';

async function leerToken(): Promise<string | null> {
  if (!secureStoreDisponible) return null;
  try {
    return await SecureStore.getItemAsync(TOKEN_KEY);
  } catch {
    // Un fallo del Keychain no puede dejar la app inarrancable: se trata como
    // "no hay sesión guardada" y el usuario vuelve a iniciar sesión.
    return null;
  }
}

async function guardarToken(token: string | null): Promise<void> {
  if (!secureStoreDisponible) return;
  try {
    if (token) {
      await SecureStore.setItemAsync(TOKEN_KEY, token);
    } else {
      await SecureStore.deleteItemAsync(TOKEN_KEY);
    }
  } catch {
    // Si no se pudo guardar, la sesión no sobrevive al reinicio. Es preferible a
    // caer al texto plano, que es justo lo que se está corrigiendo.
  }
}

export const secureAuthStorage: StateStorage = {
  getItem: async (name) => {
    const guardado = await AsyncStorage.getItem(name);
    if (!guardado) return null;
    if (!secureStoreDisponible) return guardado;

    try {
      const blob = JSON.parse(guardado);
      const token = await leerToken();
      return JSON.stringify({
        ...blob,
        state: { ...blob.state, token },
      });
    } catch {
      return guardado;
    }
  },

  setItem: async (name, value) => {
    if (!secureStoreDisponible) {
      await AsyncStorage.setItem(name, value);
      return;
    }

    try {
      const blob = JSON.parse(value);
      const { token, ...resto } = blob.state ?? {};

      await guardarToken(token ?? null);
      // El token se reemplaza por null en el bloque no cifrado para que no quede
      // también en texto plano: la protección no sirve si hay una segunda copia.
      await AsyncStorage.setItem(
        name,
        JSON.stringify({ ...blob, state: { ...resto, token: null } })
      );
    } catch {
      await AsyncStorage.setItem(name, value);
    }
  },

  removeItem: async (name) => {
    await guardarToken(null);
    await AsyncStorage.removeItem(name);
  },
};
