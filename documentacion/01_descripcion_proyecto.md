# Descripción General del Proyecto — TutorIA

## 1. Propósito e Introducción

**TutorIA** es una plataforma integral de gestión de tutorías académicas y asistencia conversacional inteligente, desarrollada en el marco del curso de Inteligencia Artificial (IF651) de la Universidad Nacional de San Antonio Abad del Cusco (UNSAAC).

El sistema combina una **aplicación móvil multiplataforma (React Native / Expo)** con un **backend en FastAPI (Python)** estructurado bajo **Arquitectura Hexagonal (Ports and Adapters)**. El núcleo funcional de la asistencia inteligente es un pipeline **RAG (Retrieval-Augmented Generation)** anclado en la normativa universitaria oficial (Reglamento de Tutoría Académica, Malla Curricular, Cronograma Académico, Servicios de Bienestar y Biblioteca, etc.) y enriquecido con **Function Calling / Tool Execution en tiempo real** sobre la base de datos operativa.

---

## 2. Arquitectura del Sistema

El sistema implementa una separación estricta de responsabilidades entre el cliente móvil y el servidor backend:

```text
+-------------------------------------------------------------------+
|                     REACT NATIVE MOBILE APP                       |
|           (Expo SDK 54, Expo Router, NativeWind, Zustand)        |
+-------------------------------------------------------------------+
                                  │
                                  │ HTTPS / REST (JSON)
                                  ▼
+-------------------------------------------------------------------+
|                        FASTAPI BACKEND                            |
|     (Arquitectura Hexagonal: Infrastructure -> Application -> Domain) |
+-------------------------------------------------------------------+
             │                                          │
             │ SQL / pgvector                           │ Async API
             ▼                                          ▼
+--------------------------+              +--------------------------+
|  POSTGRESQL + PGVECTOR   |              |    GOOGLE GEMINI API     |
| (Vectores, Usuarios, DB) |              | (gemini-3.5-flash-lite & |
+--------------------------+              |  gemini-embedding-2)   |
                                          +--------------------------+
```

---

## 3. Arquitectura Hexagonal del Backend

El backend se divide en tres capas concéntricas donde el flujo de dependencias apunta siempre hacia el centro (Dominio):

```mermaid
graph TD
    subgraph Infrastructure ["Capa de Infraestructura (Adapters & External)"]
        API["FastAPI Endpoints (v1/endpoints/)"]
        DB["PostgreSQL / pgvector (Repositories)"]
        GeminiAdapter["GeminiAdapter (google-genai SDK)"]
        AuthSec["Security (JWT, Passlib)"]
    end

    subgraph Application ["Capa de Aplicación (Use Cases & Ports)"]
        ChatUC["ChatUseCase / SessionUseCase"]
        AuthUC["AuthUseCase / StreakUseCase"]
        LLMPort["LLMPort (Interface)"]
        ChatRepoPort["ChatRepositoryPort (Interface)"]
        CorpusRepoPort["CorpusRepositoryPort (Interface)"]
    end

    subgraph Domain ["Capa de Dominio (Core Business Logic)"]
        Entities["Entidades de Dominio (User, Session, Message, etc.)"]
        Exceptions["Excepciones de Dominio (DomainExceptions)"]
    end

    API --> ChatUC
    API --> AuthUC
    ChatUC --> LLMPort
    ChatUC --> ChatRepoPort
    ChatUC --> CorpusRepoPort
    GeminiAdapter -.->|Implementa| LLMPort
    DB -.->|Implementa| ChatRepoPort
    DB -.->|Implementa| CorpusRepoPort
    ChatUC --> Entities
    AuthUC --> Entities
    Entities --> Exceptions
```

- **Dominio (`app/domain/`)**: Contiene las entidades puras en dataclasses (`User`, `Session`, `Message`, `TutorAssignment`, etc.) libres de frameworks o dependencias de ORM.
- **Aplicación (`app/application/`)**: Define las interfaces o puertos (`LLMPort`, `ChatRepositoryPort`, `CorpusRepositoryPort`) y los casos de uso (`ChatUseCase`, `AuthUseCase`, `SessionUseCase`) que coordinan la lógica de negocio.
- **Infraestructura (`app/infrastructure/`)**: Implementa los adaptadores concretos para la API de Gemini (`GeminiAdapter`), la base de datos PostgreSQL con SQLAlchemy y `pgvector` (`ChatRepository`, `CorpusRepository`), la seguridad JWT y los controladores FastAPI.

---

## 4. Flujo de Datos Extremo a Extremo (Pipeline RAG + Tool Calling)

El flujo de procesamiento de una consulta de usuario desde la app móvil hasta la respuesta del chatbot inteligente se describe en el siguiente diagrama Mermaid:

```mermaid
sequenceDiagram
    autonumber
    actor User as Estudiante / Tutor (App Móvil)
    participant Client as Axios API Client (React Native)
    participant API as FastAPI Endpoint (/api/v1/chat/message)
    participant UC as ChatUseCase (Application)
    participant Embed as LLMPort / GeminiAdapter (gemini-embedding-2)
    participant VectorDB as CorpusRepository (pgvector / Coseno)
    participant Tools as Runtime DB Tools (get_assigned_tutors/events)
    participant Gemini as Gemini 3.5 Flash Lite (LLM)
    participant DB as PostgreSQL (Chat History)

    User->>Client: Escribe mensaje ("¿Quién es mi tutor y cuál es el trámite de tutoría?")
    Client->>API: POST /api/v1/chat/message (Bearer JWT)
    API->>UC: send_chat_message(user, content, db)
    UC->>DB: Guarda mensaje del usuario en tabla `messages`
    UC->>UC: Reescribe consulta si es corta usando historial previo (Query Expansion)
    UC->>Embed: compute_embedding(rag_query)
    Embed-->>UC: Vector de 768 dimensiones
    UC->>VectorDB: search_similar(query_embedding, limit=6)
    VectorDB-->>UC: Retorna 6 fragmentos relevantes del corpus normativo
    UC->>Gemini: generate_response(prompt_con_contexto, historial, herramientas)
    
    opt Si Gemini requiere datos dinámicos del usuario (Function Calling)
        Gemini-->>UC: Solicita ejecutar herramienta (ej: get_assigned_tutors)
        UC->>Tools: Ejecuta consulta SQL asíncrona sobre la BD
        Tools-->>UC: Retorna JSON con tutores del usuario
        UC->>Gemini: Envía respuesta de la herramienta
    end

    Gemini-->>UC: Genera respuesta final anclada al contexto y datos del usuario
    UC->>DB: Guarda mensaje del asistente en tabla `messages`
    UC-->>API: Retorna objeto Message
    API-->>Client: HTTP 200 OK (JSON)
    Client-->>User: Renderiza respuesta animada en el Chat UI
```

---

## 5. Roles del Sistema

| Rol | Permisos y Capacidades en la App |
|---|---|
| **Estudiante** | Consultar al chatbot TutorIA sobre reglamentos y trámites; visualizar tutor asignado; programar y ver sesiones de tutoría; consultar calendario académico; registrar avance de racha (*streaks*); recibir notificaciones. |
| **Docente Tutor** | Visualizar lista de estudiantes asignados (tutorados); gestionar y agendar sesiones de tutoría individual o grupal; crear eventos en el calendario; recibir notificaciones de solicitudes de atención. |
| **Administrador** | Visualizar métricas globales del sistema (usuarios, sesiones, racha promedio); gestionar catálogo de usuarios (estudiantes y tutores); consultar citas motivacionales y corpus del sistema. |

---

## 6. Módulos Principales

### 6.1 Backend (FastAPI)
1. **Módulo de Autenticación (`auth.py` / `auth_use_cases.py`)**: Gestión de login, tokens JWT de acceso, hash seguro de contraseñas (bcrypt) y perfil de usuario activo (`/me`).
2. **Módulo Chat & RAG (`chat.py` / `chat_use_cases.py` / `gemini_adapter.py`)**: Gestión de conversaciones, persistencia de mensajes, expansión de consultas, embeddings con `pgvector` e inyección de contexto normativo en Gemini.
3. **Módulo de Sesiones de Tutoría (`sessions.py` / `session_service.py`)**: Programación, confirmación, cancelación y registro de bitácoras de tutoría entre docentes y estudiantes.
4. **Módulo de Calendario y Eventos (`events.py`)**: Registro y consulta de fechas importantes y sesiones agendadas.
5. **Módulo de Notificaciones y Rachas (`notifications.py`, `streaks.py`)**: Recordatorios automáticos y sistema de fidelización (*streak*) por uso activo de la tutoría.
6. **Módulo de Administración (`admin.py`)**: Estadísticas del sistema, gestión de usuarios, visualización de corpus y fraseología motivacional.

### 6.2 Frontend Móvil (React Native + Expo)
1. **Navegación File-Based (`app/`)**: Enrutamiento por carpetas y grupos con Expo Router (`(auth)`, `(tabs)`, `(estudiante)`, `(tutor)`, `(admin)`).
2. **Cliente API Adaptativo (`src/api/client.ts`)**: Inyección automática de cabeceras de autorización JWT y autodetección dinámica del puerto e IP del host en redes locales.
3. **Manejadores de Estado Global (`src/store/`)**: Tiendas React/Zustand independientes para `auth`, `chat`, `session`, `activity`, `notification`, `streak` y `preferences`.
4. **Interfaz Multilingüe (`src/i18n/`)**: Soporte nativo para cambio de idioma entre Español e Inglés.
