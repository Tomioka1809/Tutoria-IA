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
- `npm run verify:errors`: Ejecuta la verificación estática y funcional del sistema centralizado de errores.
- `npm run verify:calendar`: Ejecuta la verificación estática y funcional del módulo de calendario.
- `npm run verify:data`: Ejecuta la verificación estática de integridad de datos reales del frontend.
- `npm run lint`: Ejecuta ESLint sobre el proyecto.

---

## 🛡️ Sistema Centralizado de Errores HTTP

El frontend implementa una normalización y clasificación pura de errores (`src/api/api-error.ts`) combinada con un servicio de retroalimentación (`src/services/error-feedback.ts`):

- **Normalización Pura:** Clasifica fallos en tipos semánticos (`network`, `timeout`, `unauthorized`, `forbidden`, `not_found`, `conflict`, `validation`, `server`, `unknown`).
- **Detalle Seguro:** Conserva `detail` únicamente para respuestas HTTP 400, 409 y 422. Filtra automáticamente credenciales, tokens Bearer/JWT, cookies y trazas de pila (*stack traces*), imponiendo un límite de 240 caracteres.
- **Retroalimentación Configurable (`notify`):** Presenta alertas visuales mediante `Alert.alert` utilizando el botón `errors.close`. Admite la opción `{ notify: false }` para silenciar alertas automáticas en operaciones cuyos consumidores/pantallas ya muestran su propia notificación visual.
- **Deduplicación por Mapa:** Mantiene un registro de huellas semánticas en un `Map` para evitar mostrar alertas duplicadas dentro de un intervalo de 1500 ms.

---

## 📅 Gestión del Calendario y Separación Funcional

El módulo de calendario desacopla conceptual y técnicamente los recordatorios locales de las tutorías académicas:

- **Recordatorios Locales:** Almacenados en `useActivityStore` (`AsyncStorage`). Representan tareas/recordatorios privados del dispositivo.
- **Tutorías Persistidas:** Consumidas desde `/sessions/` a través de `useSessionStore` con persistencia en PostgreSQL.
- **Proyección Backend (`/events/`):** El backend vincula eventos a cada sesión de forma automática. El frontend no consume `/events/` directamente para prevenir la duplicación de tutorías.
- **Modelo Puro (`src/components/calendar/calendar-items.ts`):** Normaliza y ordena elementos asignando identificadores estables `activity:<id>` y `session:<id>`, aplicando análisis numérico seguro de fechas locales.
- **Conservación de Datos y Notificaciones:** Actividades locales inválidas se retienen en `AsyncStorage` (`shouldRetainStoredActivity`), excluyéndolas únicamente de las vistas. Las notificaciones del backend y recordatorios locales provienen de fuentes independientes sin duplicación sintética.

---

## 👤 Política de Integridad de Datos Reales y Estados Vacíos

Todo contenido mostrado en la interfaz procede del usuario autenticado, respuestas de endpoints reales respaldados por el backend o estado local del usuario. La asignación de tutor utiliza la función resolutora determinista `resolveAssignedTutor()` que clasifica la respuesta en `none` (ausencia), `available` (unívoco) y `ambiguous` (múltiple ambigüedad), mientras que `useProfile` diferencia fallos de carga (`assignedTutorLoadError`). Si un dato no está disponible o existe un error de red, la app presenta un estado explícito y localizado en lugar de utilizar datos o personas ficticias.
