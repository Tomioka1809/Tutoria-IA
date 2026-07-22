# App Móvil TutorIA (React Native + Expo SDK 54) 👋

Aplicación móvil del sistema **TutorIA** desarrollada con Expo, Expo Router (v6), NativeWind y Zustand.

---

## ⚙️ Configuración del Cliente API Backend

Todas las peticiones HTTP del frontend utilizan un cliente centralizado de **Axios** con interceptores de autenticación JWT.

### Resolución de la URL Base del Backend (`API_URL`)

El cliente resuelve la URL base en el siguiente orden de prioridad:

1. **`EXPO_PUBLIC_API_URL`**: Variable de entorno configurada en `.env` (solo admite protocolo `http://` o `https://`, ej: `http://localhost:8000/api/v1`).
2. **Detección Dinámica de Expo (`expoConfig.hostUri`)**: Cuando la app se ejecuta con Expo Go en un dispositivo físico conectado a la misma red Wi-Fi, detecta automáticamente la IP LAN del host (ej: `http://<IP_LAN_DEL_EQUIPO>:8000/api/v1`).
3. **`localhost`**: Fallback por defecto (`http://localhost:8000/api/v1`).

### Configuración para Dispositivo Físico
- Crea un archivo `.env` local basándote en `.env.example`:
  ```bash
  EXPO_PUBLIC_API_URL=http://<IP_LAN_DEL_EQUIPO>:8000/api/v1
  ```
- **Nota:** El archivo `.env` real **nunca se versiona en Git**.

---

## 🚀 Inicio Rápido

1. Instalar dependencias:
   ```bash
   npm install
   ```

2. Verificar la capa API:
   ```bash
   npm run verify:api
   ```

3. Iniciar el servidor de desarrollo de Expo:
   ```bash
   npx expo start
   ```

---

## 🧪 Comandos de Calidad

- `npm run verify:api`: Ejecuta la verificación estática y funcional de la capa API.
- `npm run lint`: Ejecuta ESLint sobre el proyecto.
