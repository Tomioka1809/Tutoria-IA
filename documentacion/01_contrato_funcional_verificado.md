# Contrato Funcional Verificado — TutorIA

## 1. Objetivo y alcance

- **Objetivo:** Definir y documentar mediante inspección estática del código fuente el contrato funcional del sistema **TutorIA**, trazando la cadena de llamadas entre la interfaz de usuario (React Native / Expo Router), las tiendas de estado (Zustand), los clientes de API (`client.ts` Axios / `services.ts` Fetch), los controladores (FastAPI), la capa de aplicación/dominio y la persistencia (SQLAlchemy / pgvector).
- **Alcance:** Inspección estática del código existente para los flujos de autenticación, perfiles, navegación por roles (Estudiante, Tutor, Administrador), funcionalidad del Chatbot RAG con *Tool Calling* y gestión administrativa. La validación en ejecución se difiere a fases posteriores de prueba.

---

## 2. Método de inspección

Se realizó el trazado estático en el código fuente:
$$\text{Pantalla Expo Router} \longrightarrow \text{Zustand Store / API Service} \longrightarrow \text{HTTP Endpoint (FastAPI)} \longrightarrow \text{Auth Dependency} \longrightarrow \text{Use Case} \longrightarrow \text{Repository} \longrightarrow \text{SQLAlchemy Model}$$

- **Inspección de API Endpoints:** `backend/app/infrastructure/api/v1/endpoints/` (`auth.py`, `chat.py`, `sessions.py`, `tutors.py`, `events.py`, `notifications.py`, `streaks.py`, `quotes.py`, `quiz.py`, `admin.py`).
- **Inspección de Frontend:** `frontend/app/` (rutas `auth/`, `(estudiante)/`, `(tutor)/`, `(admin)/`) y `frontend/src/` (`store/`, `api/`, `components/`).

---

## 3. Resumen de flujos por estado

### 3.1 Flujos funcionales principales

Cuenta únicamente las filas únicas de las secciones:
- Navegación y autenticación.
- Contrato funcional del estudiante.
- Contrato funcional del tutor.
- Contrato funcional del administrador.

Los pasos internos del chatbot RAG (sección 9) no se vuelven a contabilizar porque representan el desglose técnico de `EST-002`.

| Estado | Cantidad |
|---|---:|
| COMPLETO_EN_CODIGO | 30 |
| PARCIAL | 2 |
| REQUIERE_DECISION_FUNCIONAL | 1 |

### 3.2 Hallazgos auxiliares

| Estado | Cantidad |
|---|---:|
| SOLO_FRONTEND | 2 |
| SOLO_BACKEND | 1 |
| ENDPOINT_POTENCIALMENTE_REDUNDANTE | 1 |
| USA_MOCK | 2 |

Nota: Los datos mock y pantallas estáticas se registran como hallazgos auxiliares y no se suman como flujos funcionales adicionales del core.

### 3.3 Casos pendientes de ejecución

Se identifican cuatro casos funcionales de aceptación para la validación en tiempo de ejecución:
- `CF-001` (Inicio de sesión correcto)
- `CF-002` (Consulta al Chatbot RAG)
- `CF-003` (Programación de tutoría)
- `CF-004` (Sorteo de tutores)

Todos requieren ejecución en el entorno levantado. Esta cantidad no se suma a los flujos principales porque corresponde a pruebas de flujos ya contabilizados.

---

## 4. Roles detectados

| Rol | Valor usado en código | Ruta inicial | Evidencia en código |
|---|---|---|---|
| **Estudiante** | `"estudiante"` | `/(estudiante)` | `frontend/app/_layout.tsx` L59, `backend/app/domain/entities/user.py` L9 |
| **Tutor** | `"tutor"` | `/(tutor)` | `frontend/app/_layout.tsx` L55, `backend/app/domain/entities/user.py` L9 |
| **Administrador** | `"admin"` | `/(admin)` | `frontend/app/_layout.tsx` L51, `backend/app/domain/entities/user.py` L9 |

---

## 5. Navegación y autenticación

| ID | Flujo | Pantalla | Store/servicio | Endpoint | Estado | Evidencia | Observación |
|---|---|---|---|---|---|---|---|
| `NAV-001` | Hidratación e Inicio | `frontend/app/_layout.tsx` | `useAuthStore.persist` | N/A | `COMPLETO_EN_CODIGO` | `_layout.tsx` L27-L36 | Verifica `hasHydrated()` y redirige según rol o al login si falta token. |
| `AUTH-001` | Inicio de Sesión (Login) | `frontend/app/auth/login.tsx` | `client.post` / `useAuthStore` | `POST /auth/login` & `GET /auth/me` | `COMPLETO_EN_CODIGO` | `login.tsx` L34, L41, `auth.py` L34, L43 | Recibe token JWT, consulta `/auth/me` y persiste sesión en AsyncStorage. |
| `AUTH-002` | Registro Estudiante | `frontend/app/auth/register.tsx` | `client.post` | `POST /auth/register` | `COMPLETO_EN_CODIGO` | `register.tsx` L46, `auth.py` L12 | Registro público con perfil de estudiante por defecto. |
| `AUTH-003` | Cierre de Sesión | `frontend/app/(estudiante)/configuracion.tsx` | `useAuthStore.logout` | N/A | `COMPLETO_EN_CODIGO` | `auth.ts` L49 | Limpia token y datos del usuario localmente en Zustand y AsyncStorage. |
| `AUTH-004` | Edición de Perfil | `frontend/app/(estudiante)/editar-perfil.tsx` | `useAuthStore.updateProfile` | `PUT /auth/profile` | `COMPLETO_EN_CODIGO` | `auth.ts` L30, `auth.py` L47 | Actualiza datos del perfil y sincroniza la tienda de autenticación. |
| `AUTH-005` | Cambio de Contraseña | `frontend/app/(estudiante)/configuracion.tsx` | `useAuthStore.changePassword` | `PUT /auth/change-password` | `COMPLETO_EN_CODIGO` | `auth.ts` L39, `auth.py` L55 | Envía `current_password` y `new_password` para validación y hash bcrypt. |
| `AUTH-006` | Olvidé mi contraseña | `frontend/app/auth/forgot-password.tsx` | `client.post` | `POST /auth/forgot-password` | `PARCIAL` | `forgot-password.tsx` L23, `auth.py` L66 | Endpoint retorna mensaje informativo; no genera token de restablecimiento ni integra SMTP real. |

---

## 6. Contrato funcional del estudiante

| ID | Funcionalidad | Pantalla | Store/servicio | Método y endpoint | Request | Response esperada | Estado | Evidencia |
|---|---|---|---|---|---|---|---|---|
| `EST-001` | Dashboard Estudiante | `frontend/app/(estudiante)/index.tsx` | `useDashboard` (`useStreakStore`, `useSessionStore`) | `GET /streaks/` & `GET /sessions/` | Query Params vacíos (`Header: Bearer token`) | `StreakOut` y `List[SessionOut]` | `COMPLETO_EN_CODIGO` | `useDashboard.ts` L8-L10, `streaks.py` L11 | Muestra racha actual y próximas tutorías agendadas. |
| `EST-002` | Chat TutorIA RAG | `frontend/app/(estudiante)/tutoria.tsx` | `useChatStore` | `GET /chat/conversation` & `POST /chat/message` | `{ "content": "string" }` | `MessageOut` | `PARCIAL` | `chat.ts` L24, L62, `chat.py` L11, L23 | GeminiAdapter declara las herramientas y recibe peticiones de Tool Calling, pero `ChatUseCase` ejecuta directamente modelos ORM SQLAlchemy. |
| `EST-003` | Solicitar Tutoría | `frontend/src/components/calendar/ScheduleSessionModal.tsx` | `useSessionStore.createSession` | `POST /sessions/` | `{ tutor_id, service_type_id, scheduled_at, notes, location }` | `SessionOut` | `COMPLETO_EN_CODIGO` | `session.ts` L40, `sessions.py` L18 | Crea una sesión de tutoría con estado inicial `"programada"`. |
| `EST-004` | Quiz Generativo LLM | `frontend/app/(estudiante)/retroalimentacion-quiz.tsx` | `QuizAPI.generateQuiz` | `GET /quiz/generate` | Header `Authorization: Bearer token` | `List[QuizQuestionOut]` | `COMPLETO_EN_CODIGO` | `services.ts` L16, `quiz.py` L22 | Inconsistencia de cliente HTTP: usa `fetch` independiente con 60s timeout duplicando la gestión de tokens. |
| `EST-005` | Actividades Personales | `frontend/src/components/calendar/AddActivityModal.tsx` | `useActivityStore` | N/A (Local Storage) | `{ name, type, date, time }` | `Activity` (local) | `DECISION_FUNCIONAL_RESUELTA_EN_FASE_4C` | `activity.ts` L20-L54, `events.py` L15, L41 | Persistencia local en AsyncStorage para recordatorios personales. Las tutorías persistidas se gestionan en `useSessionStore` y PostgreSQL. `/events/` es una proyección interna vinculada a sesiones y no se consume para evitar duplicidad. |
| `EST-006` | Frase Motivacional | `frontend/app/(estudiante)/index.tsx` | `QuotesAPI.getRandomQuote` | `GET /quotes/random` | Ninguno | `QuoteOut` | `COMPLETO_EN_CODIGO` | `services.ts` L58, `quotes.py` L19 | Obtiene una frase aleatoria almacenada en la base de datos. |

---

## 7. Contrato funcional del tutor

| ID | Funcionalidad | Pantalla | Store/servicio | Método y endpoint | Request | Response esperada | Estado | Evidencia |
|---|---|---|---|---|---|---|---|---|
| `TUT-001` | Dashboard Tutor | `frontend/app/(tutor)/index.tsx` | `client.get` (`useAuthStore`) | `GET /tutors/periods` & `GET /tutors/students` | Header `Authorization: Bearer token` | `List[str]` y `List[UserOut]` | `COMPLETO_EN_CODIGO` | `(tutor)/index.tsx` L30, L45, `tutors.py` L54, L63 | Obtiene periodos académicos y lista de estudiantes tutorados asignados. |
| `TUT-002` | Calendario / Sesiones | `frontend/app/(tutor)/calendar.tsx` | `useSessionStore` | `GET /sessions/` & `PUT /sessions/{session_id}` | `{ status: "completada" \| "cancelada", notes }` | `SessionOut` | `COMPLETO_EN_CODIGO` | `session.ts` L53, `sessions.py` L28 | Permite al tutor cambiar el estado de la sesión y añadir notas de atención. |
| `TUT-003` | Notificaciones | `frontend/app/(tutor)/notifications.tsx` | `useNotificationStore` | `GET /notifications/` & `PUT /notifications/{notification_id}/read` | Path `notification_id` | `List[NotificationOut]` y `NotificationOut` | `COMPLETO_EN_CODIGO` | `notification.ts` L19, L29, `notifications.py` L12 | Consulta alertas del tutor y marca notificaciones como leídas. |

---

## 8. Contrato funcional del administrador

Rutas administrativas verificadas de manera exacta sobre `backend/app/infrastructure/api/v1/endpoints/admin.py`:

| ID | Funcionalidad | Pantalla | Store/servicio | Método y endpoint exacto | Request | Response esperada | Estado | Evidencia |
|---|---|---|---|---|---|---|---|---|
| `ADM-001` | Panel de Estadísticas | `frontend/app/(admin)/index.tsx` | `client.get` | `GET /api/v1/admin/stats` | Header `Authorization: Bearer token` | `AdminStats` | `COMPLETO_EN_CODIGO` | `(admin)/index.tsx` L29, `admin.py` L73 |
| `ADM-002` | Listar Usuarios | `frontend/app/(admin)/users.tsx` | `client.get` | `GET /api/v1/admin/users` | Header `Authorization: Bearer token` | `List[AdminUserOut]` | `COMPLETO_EN_CODIGO` | `users.tsx` L36, `admin.py` L104 |
| `ADM-003` | Crear Usuario Staff | `frontend/app/(admin)/users.tsx` | `client.post` | `POST /api/v1/admin/users` | `AdminUserCreate` | `AdminUserOut` | `COMPLETO_EN_CODIGO` | `users.tsx` L82, `admin.py` L122 |
| `ADM-004` | Cambiar Estado Usuario | `frontend/app/(admin)/users.tsx` | `client.patch` | `PATCH /api/v1/admin/users/{user_id}/status` | `{ is_active: boolean }` | `AdminUserOut` | `COMPLETO_EN_CODIGO` | `users.tsx` L62, `admin.py` L139 |
| `ADM-005` | Cambiar Capacidad Tutor | `frontend/app/(admin)/users.tsx` | `client.patch` | `PATCH /api/v1/admin/users/{user_id}/capacity` | `{ max_capacity: int }` | `AdminUserOut` | `COMPLETO_EN_CODIGO` | `users.tsx` L131, `admin.py` L158 |
| `ADM-006` | Ver Estudiantes de Tutor | `frontend/app/(admin)/users.tsx` | `client.get` | `GET /api/v1/admin/users/{user_id}/students` | Path `user_id` | `List[UserOut]` | `COMPLETO_EN_CODIGO` | `users.tsx` L113, `admin.py` L174 |
| `ADM-007` | Asignación Individual | `frontend/app/(admin)/sorteo.tsx` | `client.post` | `POST /api/v1/admin/assignments` | `{ tutor_id, student_id, period }` | HTTP 201 Created | `COMPLETO_EN_CODIGO` | `sorteo.tsx` L57, `admin.py` L199 |
| `ADM-008` | Reasignación Masiva | `frontend/app/(admin)/sorteo.tsx` | `client.post` | `POST /api/v1/admin/assignments/bulk-transfer` | `{ source_tutor_id, target_tutor_id, period }` | HTTP 200 OK | `COMPLETO_EN_CODIGO` | `sorteo.tsx` L88, `admin.py` L218 |
| `ADM-009` | Sorteo de Tutores | `frontend/app/(admin)/sorteo.tsx` | `client.post` | `POST /api/v1/admin/sorteo` | Query param `period` opcional | `dict` | `COMPLETO_EN_CODIGO` | `sorteo.tsx` L118, `admin.py` L245 |
| `ADM-010` | Listar Corpus RAG | `frontend/app/(admin)/contenido.tsx` | `client.get` | `GET /api/v1/admin/corpus` | Header `Authorization: Bearer token` | `List[CorpusChunkOut]` | `COMPLETO_EN_CODIGO` | `contenido.tsx` L39, `admin.py` L297 |
| `ADM-011` | Crear Chunk Corpus | `frontend/app/(admin)/contenido.tsx` | `client.post` | `POST /api/v1/admin/corpus` | `{ source, text_content }` | `CorpusChunkOut` | `COMPLETO_EN_CODIGO` | `contenido.tsx` L81, `admin.py` L302 |
| `ADM-012` | Editar Chunk Corpus | `frontend/app/(admin)/contenido.tsx` | `client.put` | `PUT /api/v1/admin/corpus/{chunk_id}` | `{ source, text_content }` | `CorpusChunkOut` | `COMPLETO_EN_CODIGO` | `contenido.tsx` L79, `admin.py` L326 |
| `ADM-013` | Eliminar Chunk Corpus | `frontend/app/(admin)/contenido.tsx` | `client.delete` | `DELETE /api/v1/admin/corpus/{chunk_id}` | Path `chunk_id` | HTTP 200 OK | `COMPLETO_EN_CODIGO` | `contenido.tsx` L61, `admin.py` L317 |
| `ADM-014` | Listar Frases | `frontend/app/(admin)/contenido.tsx` | `client.get` | `GET /api/v1/admin/quotes` | Header `Authorization: Bearer token` | `List[QuoteOut]` | `COMPLETO_EN_CODIGO` | `contenido.tsx` L40, `admin.py` L344 |
| `ADM-015` | Crear Frase | `frontend/app/(admin)/contenido.tsx` | `client.post` | `POST /api/v1/admin/quotes` | `{ text }` | `QuoteOut` | `COMPLETO_EN_CODIGO` | `contenido.tsx` L112, `admin.py` L349 |
| `ADM-016` | Editar Frase | `frontend/app/(admin)/contenido.tsx` | `client.put` | `PUT /api/v1/admin/quotes/{quote_id}` | `{ text }` | `QuoteOut` | `COMPLETO_EN_CODIGO` | `contenido.tsx` L110, `admin.py` L357 |
| `ADM-017` | Eliminar Frase | `frontend/app/(admin)/contenido.tsx` | `client.delete` | `DELETE /api/v1/admin/quotes/{quote_id}` | Path `quote_id` | HTTP 200 OK | `COMPLETO_EN_CODIGO` | `contenido.tsx` L93, `admin.py` L369 |

---

## 9. Contrato del chatbot RAG

Diferenciación estricta de responsabilidades entre el adaptador LLM y el caso de uso:

- **`GeminiAdapter` (`gemini_adapter.py`):** Declara la especificación de las herramientas (`get_assigned_tutor`, `get_my_students`, `get_upcoming_events`) hacia la API de Gemini y recibe las respuestas estructuradas de *Tool Calling*.
- **`ChatUseCase` (`chat_use_cases.py`):** Orquesta el flujo RAG, invoca la similitud vectorial y ejecuta las funciones de las herramientas cuando Gemini las solicita.

| Paso | Componente | Archivo | Entrada | Salida | Estado | Observación |
|---|---|---|---|---|---|---|
| 1 | Petición HTTP | `endpoints/chat.py` | `MessageCreate` (`content`) | `MessageOut` | `COMPLETO_EN_CODIGO` | Punto de entrada expuesto en API v1. |
| 2 | Invocación Caso de Uso | `chat_use_cases.py` | `user_id`, `content` | `Message` (Dominio) | `PARCIAL` | Involucra la ejecución de herramientas mediante consultas ORM directas. |
| 3 | Búsqueda Vectorial | `corpus_repository.py` | `query_embedding` (768 dim), `limit=6`, `query_text` | `List[str]` (Contexto RAG) | `COMPLETO_EN_CODIGO` | Ejecuta similitud Coseno con fallback por palabras clave. |
| 4 | Declaración de Tools | `gemini_adapter.py` | Prompt + Contexto + Tools | Tool Call Request | `COMPLETO_EN_CODIGO` | Declara firmas de funciones para Gemini. |
| 5 | Ejecución de Tools | `chat_use_cases.py` | Function Call Arguments | Datos de BD (`TutorAssignment`, `Event`) | `PARCIAL` | `ChatUseCase` ejecuta consultas SQL directas (`select(TutorAssignment)`), violando parcialmente la arquitectura hexagonal. |
| 6 | Persistencia de Chat | `chat_repository.py` | `conversation_id`, `role`, `content` | `Message` persistido | `COMPLETO_EN_CODIGO` | Almacena el historial en PostgreSQL. |

---

## 10. Matriz frontend frente a backend

| ID | Llamada frontend | Endpoint backend | Método coincide | Ruta coincide | Contrato coincide | Autorización | Resultado |
|---|---|---|---|---|---|---|---|
| `API-001` | `client.post('/auth/login', formData)` | `POST /api/v1/auth/login` | Sí (`POST`) | Sí (`/auth/login`) | Sí (`FormData: username, password`) | Pública | `COMPLETO_EN_CODIGO` |
| `API-002` | `client.get('/auth/me')` | `GET /api/v1/auth/me` | Sí (`GET`) | Sí (`/auth/me`) | Sí (`UserOut`) | `Bearer Token` | `COMPLETO_EN_CODIGO` |
| `API-003` | `client.get('/chat/conversation')` | `GET /api/v1/chat/conversation` | Sí (`GET`) | Sí (`/chat/conversation`) | Sí (`ConversationOut`) | `Bearer Token` | `COMPLETO_EN_CODIGO` |
| `API-004` | `client.post('/chat/message', { content })` | `POST /api/v1/chat/message` | Sí (`POST`) | Sí (`/chat/message`) | Sí (`{ content: str }`) | `Bearer Token` | `COMPLETO_EN_CODIGO` |
| `API-005` | `QuizAPI.generateQuiz()` (`fetch`) | `GET /api/v1/quiz/generate` | Sí (`GET`) | Sí (`/quiz/generate`) | Inconsistencia de Cliente | `Bearer Token` | `COMPLETO_EN_CODIGO` |
| `API-006` | `client.get('/sessions/')` | `GET /api/v1/sessions/` | Sí (`GET`) | Sí (`/sessions/`) | Sí (`List[SessionOut]`) | `Bearer Token` | `COMPLETO_EN_CODIGO` |
| `API-007` | `client.post('/sessions/', sessionData)` | `POST /api/v1/sessions/` | Sí (`POST`) | Sí (`/sessions/`) | Sí (`SessionCreate`) | `Bearer Token` | `COMPLETO_EN_CODIGO` |

---

## 11. Pantallas sin conexión confirmada

| Pantalla | Archivo | Problema | Estado |
|---|---|---|---|
| **Explorar (Estudiante)** | `frontend/app/(estudiante)/explore.tsx` | Contenido puramente estático de plantilla Expo Router. | `SOLO_FRONTEND` |
| **Explorar (Tutor)** | `frontend/app/(tutor)/explore.tsx` | Contenido puramente estático de plantilla Expo Router. | `SOLO_FRONTEND` |

---

## 12. Endpoints sin consumidor o redundantes

| Endpoint | Archivo backend | Clasificación | Observación |
|---|---|---|---|
| `POST /api/v1/auth/register-staff` | `endpoints/auth.py` L23 | `ENDPOINT_POTENCIALMENTE_REDUNDANTE` | La creación de personal administrativo/tutores es asumida por `POST /admin/users`. |
| `GET /api/v1/tutors/service-types` | `endpoints/tutors.py` L99 | `SOLO_BACKEND` | El frontend envía `service_type_id: 1` fijo o ingresado en modales sin consultar dinámicamente este catálogo. |

---

## 13. Uso de mocks y datos estáticos

| Archivo | Dato simulado | Funcionalidad afectada | Severidad |
|---|---|---|---|
| `frontend/src/components/profile/AssignedTutorCard.tsx` L23-L27 | `'Ing. Ana Torres'` / `'ana.torres@universidad.edu'` | Muestra datos ficticios si el array de tutores asignados viene vacío. | Media |
| `frontend/src/components/notifications/NotificationsHeader.tsx` L21 | Filtro mock visual de tipos de notificación | Desplegable de selección en pantalla de Notificaciones sin conexión a backend. | Baja |

---

## 14. Flujos adicionales pendientes de confirmación

Los siguientes componentes existen en código pero requieren validación en ejecución para confirmar su comportamiento dinámico completo:

- **Configuración:** `frontend/app/(estudiante)/configuracion.tsx`, `frontend/app/(tutor)/configuracion.tsx` y `frontend/app/(admin)/configuracion.tsx`.
- **Privacidad:** `frontend/app/(estudiante)/privacidad.tsx` y `frontend/app/(tutor)/privacidad.tsx`.
- **Centro de Ayuda:** `frontend/app/(estudiante)/centro-ayuda.tsx` y `frontend/app/(tutor)/centro-ayuda.tsx`.
- **Perfiles por Rol:** `frontend/app/(estudiante)/profile.tsx` y `frontend/app/(tutor)/perfil-tutor.tsx`.
- **Edición de Perfil:** `frontend/app/(estudiante)/editar-perfil.tsx` y `frontend/app/(tutor)/editar-perfil.tsx`.
- **Manejo de Errores 401/403:** Comportamiento del interceptor Axios en `client.ts` frente a respuestas de error.
- **Cierre Automático de Sesión:** Expiración de tokens JWT en la tienda `useAuthStore`.
- **Autorización Específica por Rol:** Verificación de dependencias `get_current_active_tutor` y `get_current_active_admin`.
- **Notificaciones del Estudiante:** `frontend/app/(estudiante)/notifications.tsx` (consumo de `/notifications/`).
- **Idioma y Tema:** Cambios dinámicos de tema e i18n desde `usePreferencesStore` y `ThemeContext.tsx`.
- **Errores de Red:** Feedback visual en la interfaz en situaciones de desconexión.

---

## 15. Incompatibilidades detectadas

| ID | Tipo | Frontend | Backend | Impacto | Fase de corrección |
|---|---|---|---|---|---|
| `INC-001` | Cliente HTTP Centralizado | `QuizAPI` utiliza `client.get('/quiz/generate')`. | Cliente centralizado con timeout de 60000 ms. | JWT inyectado mediante interceptor de Axios. | RESUELTO_EN_FASE_4A |
| `INC-002` | Resolución Dinámica de URL | No existe IP privada fija en `client.ts`. | Se prioriza `EXPO_PUBLIC_API_URL`, luego se utiliza `expoConfig.hostUri` y fallback `localhost`. | Eliminada IP estática hardcodeada de desarrollo. | RESUELTO_EN_FASE_4A |
| `INC-003` | Documentación Embeddings | Modelos anteriores retirados unificados a `gemini-embedding-2`. | `gemini_adapter.py` unificado a `gemini-embedding-2`. | Resuelto en la Fase 3. | Fase 3 |

---

## 16. Casos funcionales de aceptación

### CF-001 — Inicio de Sesión Correcto
- **Actor:** Estudiante / Tutor / Administrador.
- **Precondiciones:** Usuario registrado en la base de datos.
- **Entrada:** `username` (email), `password`.
- **Pasos:** 1. Ingresar credenciales en `app/auth/login.tsx`. 2. Presionar "Iniciar Sesión".
- **Resultado esperado:** Retorna JWT `access_token`, guarda usuario en `useAuthStore` y redirige a la ruta del rol correspondiente (`/(estudiante)`, `/(tutor)` o `/(admin)`).
- **Endpoint relacionado:** `POST /api/v1/auth/login` y `GET /api/v1/auth/me`.
- **Evidencia:** `login.tsx` L34, L41.
- **Estado actual:** `COMPLETO_EN_CODIGO`.
- **Requiere ejecución:** Sí.

---

### CF-002 — Consulta al Chatbot RAG
- **Actor:** Estudiante.
- **Precondiciones:** Estudiante autenticado con token JWT activo.
- **Entrada:** Mensaje textual sobre el reglamento universitario.
- **Pasos:** 1. Navegar a `app/(estudiante)/tutoria.tsx`. 2. Escribir pregunta y enviar.
- **Resultado esperado:** `ChatUseCase` busca fragmentos vectoriales en `pgvector`, consulta a Gemini y devuelve la respuesta fundamentada en el contexto disponible.
- **Endpoint relacionado:** `POST /api/v1/chat/message`.
- **Evidencia:** `chat.ts` L62, `chat_use_cases.py` L55.
- **Estado actual:** `PARCIAL`.
- **Requiere ejecución:** Sí.

---

### CF-003 — Programación de Tutoría
- **Actor:** Estudiante.
- **Precondiciones:** Estudiante con tutor asignado.
- **Entrada:** `tutor_id`, `service_type_id`, `scheduled_at`, `notes`.
- **Pasos:** 1. Abrir `ScheduleSessionModal.tsx`. 2. Completar formulario y guardar.
- **Resultado esperado:** Registra la sesión en la base de datos PostgreSQL con estado `"programada"`.
- **Endpoint relacionado:** `POST /api/v1/sessions/`.
- **Evidencia:** `session.ts` L43, `sessions.py` L18.
- **Estado actual:** `COMPLETO_EN_CODIGO`.
- **Requiere ejecución:** Sí.

---

### CF-004 — Asignación Aleatoria de Tutores (Sorteo)
- **Actor:** Administrador.
- **Precondiciones:** Administrador autenticado.
- **Entrada:** Petición POST a `/admin/sorteo`.
- **Pasos:** 1. Ingresar a `app/(admin)/sorteo.tsx`. 2. Presionar "Ejecutar Sorteo".
- **Resultado esperado:** Asigna estudiantes sin tutor a docentes tutores respetando su capacidad máxima.
- **Endpoint relacionado:** `POST /api/v1/admin/sorteo`.
- **Evidencia:** `sorteo.tsx` L118, `admin.py` L245.
- **Estado actual:** `COMPLETO_EN_CODIGO`.
- **Requiere ejecución:** Sí.

---

## 17. Flujos mínimos para pruebas posteriores

1. **Flujo de Autenticación & Rol:** Login (`POST /auth/login`) $\rightarrow$ `/auth/me` $\rightarrow$ Redirección por rol.
2. **Flujo RAG & Tool Calling:** `GET /chat/conversation` $\rightarrow$ `POST /chat/message` $\rightarrow$ Similitud Coseno `pgvector` $\rightarrow$ Inferencia Gemini.
3. **Flujo de Tutorías:** `GET /sessions/` $\rightarrow$ `POST /sessions/` $\rightarrow$ `PUT /sessions/{session_id}`.
4. **Flujo Administrativo:** `GET /admin/stats` $\rightarrow$ `GET /admin/users` $\rightarrow$ `POST /admin/sorteo`.

---

## 18. Hallazgos priorizados

| ID | Componente | Hallazgo | Severidad | Fase recomendada |
|---|---|---|---|---|
| `HALL-AUTH-001` | Autenticación | Flujo de recuperación de contraseña (`forgot-password`) no envía correos de restablecimiento reales. | Media | Fase 2 |
| `HALL-NAV-001` | Navegación | Pantallas `explore.tsx` en estudiante y tutor mantienen contenido estático de plantilla Expo Router. | Baja | Fase 4 |
| `HALL-EST-001` | Estudiante | Actividades del calendario se persisten localmente en `useActivityStore` (recordatorios privados) sin consumir `/events/`. Las tutorías persistidas se consumen desde `/sessions/`. | Media | DECISION_FUNCIONAL_RESUELTA_EN_FASE_4C |
| `HALL-TUT-001` | Tutor | El selector de tipos de servicio consume `GET /tutors/service-types` (`useCalendar.ts` L62). | Baja | Resuelto en Código |
| `HALL-ADM-001` | Admin | El endpoint `POST /auth/register-staff` no tiene vista consumidora directa en el frontend de administración. | Baja | Fase 2 |
| `HALL-CHAT-001` | Chatbot | `ChatUseCase` desacoplado de SQLAlchemy; utiliza `CorpusRepositoryPort` y DTOs tipados `RetrievedChunkDTO`. | Alta | Resuelto Fase 2 / Fase 3 |
| `HALL-API-001` | API Client | `client.ts` contenía IP hardcodeada (`192.168.18.27`); eliminada y resuelta con `resolveApiUrl`. | Media | Resuelto Fase 4A |
| `HALL-MOCK-001` | Frontend / UX | `AssignedTutorCard.tsx` muestra datos mock hardcodeados (`Ing. Ana Torres`) si el usuario no tiene tutor asignado. | Media | Fase 4 |

---

## 19. Criterio de cierre de la Fase 1

Se han satisfecho los criterios obligatorios de la Fase 1:
- Inspección estática del código realizada sobre los controladores backend, tiendas Zustand y pantallas Expo Router.
- Mapeo del contrato funcional entre frontend y backend documentado con rutas exactas y parámetros.
- Ejecución de `verificar_tutoria.py --fase 1 --verbose` en estado `PASS=4, FAIL=0`.
- Documento `documentacion/01_contrato_funcional_verificado.md` actualizado sin modificar código funcional.

---

## 20. Conclusión

Mediante la inspección estática del código fuente se ha formalizado el contrato funcional verificado entre el frontend React Native y el backend FastAPI. La mayoría de flujos principales de autenticación, chat RAG, programación de sesiones y administración se encuentran estructurados en código. Se han identificado claramente las desviaciones arquitectónicas (como las consultas SQL directas en `ChatUseCase`), las inconsistencias de cliente HTTP y los fallbacks estáticos, dejando la línea base funcional totalmente establecida para las siguientes fases de desarrollo.
