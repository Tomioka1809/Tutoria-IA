# Inventario de Proyecto — TutorIA (Fase 0)

Este documento contiene la radiografía completa del repositorio **TutorIA**, mapeando la estructura física, el stack tecnológico detectado, la configuración del entorno y el análisis de componentes ("Qué existe vs. Qué falta").

---

## 1. Árbol de Directorios del Proyecto

```text
React-Native/
├── .env.example                         # Plantilla de variables de entorno
├── docker-compose.yml                   # Orquestación Docker (PostgreSQL pgvector + FastAPI)
├── README.md                            # Guía principal del proyecto
├── Distribucion_Tutoria_2026-I.txt     # Datos institucionales / asignaciones
├── backend/
│   ├── alembic/                         # Migraciones de BD con Alembic
│   ├── alembic.ini                      # Configuración de Alembic
│   ├── Dockerfile                       # Dockerfile del servicio FastAPI
│   ├── requirements.txt                 # Dependencias Python
│   ├── corpus/                          # Archivos de la normativa y servicios (JSON)
│   │   ├── cronograma_academico.json
│   │   ├── glosario.json
│   │   ├── malla_curricular_2017.json
│   │   ├── malla_curricular_2025.json
│   │   ├── preguntas_frecuentes.json
│   │   ├── reglamento_intercambio_estudiantil.json
│   │   ├── reglamento_tutoria.json
│   │   ├── servicios_biblioteca.json
│   │   └── servicios_bienestar.json
│   ├── app/                             # Código fuente del Backend FastAPI (Arquitectura Hexagonal)
│   │   ├── main.py                      # Punto de entrada de la aplicación FastAPI
│   │   ├── create_superuser.py          # Script CLI para crear usuario administrador
│   │   ├── domain/                      # Capa de Dominio (Entidades y Excepciones)
│   │   │   ├── exceptions.py
│   │   │   ├── entities/                # Dataclasses / Modelos puros de dominio
│   │   │   └── schemas/                 # [VACÍO] Esquemas Pydantic / DTOs de dominio
│   │   ├── application/                 # Capa de Aplicación (Puertos y Casos de Uso)
│   │   │   ├── ports/                   # Interfaces abstractas (LLM, Repositorios)
│   │   │   └── use_cases/               # Servicios de aplicación / Casos de uso
│   │   └── infrastructure/              # Capa de Infraestructura (Adaptadores, DB, API)
│   │       ├── adapters/                # Adaptador de Gemini AI (google-genai)
│   │       ├── api/                     # Routers y Endpoints de FastAPI (v1)
│   │       ├── config/                  # Ajustes de configuración pydantic-settings
│   │       ├── database/                # Modelos SQLAlchemy, Repositorios pgvector, Seeds
│   │       └── security/                # Utilidades de hash de contraseñas y JWT
│   └── tests/                           # [NUEVO] Directorio reservado para banco de pruebas RAG y backend
├── frontend/                            # Aplicación Móvil React Native (Expo)
│   ├── app/                             # Rutas de Expo Router (File-based routing)
│   │   ├── _layout.tsx                  # Layout raíz y proveedores de contexto
│   │   ├── modal.tsx                    # Modal global
│   │   ├── auth/                        # Pantallas de Login / Registro
│   │   ├── (tabs)/                      # Navegación principal por pestañas
│   │   ├── (estudiante)/                # Pantallas del rol Estudiante
│   │   ├── (tutor)/                     # Pantallas del rol Docente-Tutor
│   │   └── (admin)/                     # Pantallas del rol Administrador
│   ├── src/                             # Código de soporte frontend
│   │   ├── api/                         # Cliente Axios con autodetección de IP local y servicios
│   │   ├── components/                  # Componentes reutilizables de interfaz
│   │   ├── store/                       # Tiendas de estado global con Zustand
│   │   ├── i18n/                        # Internacionalización (Español e Inglés)
│   │   ├── theme/                       # Configuración de colores y tokens de diseño
│   │   ├── data/                        # Datos estáticos y mocks
│   │   └── types/                       # Definiciones de TypeScript
│   ├── app.json                         # Configuración del proyecto Expo (SDK 54)
│   ├── package.json                     # Dependencias Node.js
│   ├── tailwind.config.js               # Configuración de NativeWind / Tailwind CSS
│   ├── tsconfig.json                    # Configuración de TypeScript
│   └── metro.config.js                  # Configuración del bundler Metro
└── documentacion/                       # [NUEVO] Documentación técnica y reportes del proyecto
    └── 00_inventario.md                 # Este documento
```

---

## 2. Stack Tecnológico Detectado

| Componente | Tecnología | Versión / Detalle |
|---|---|---|
| **Lenguaje Backend** | Python | `3.12+` |
| **Framework Backend** | FastAPI | `0.136.3` (ASGI Uvicorn `0.49.0`) |
| **Base de Datos** | PostgreSQL + pgvector | Imagen Docker `pgvector/pgvector:pg16` (Puerto host: 5433 / contenedor: 5432) |
| **ORM & Migraciones** | SQLAlchemy (Async) + Alembic | SQLAlchemy `2.0.50`, asyncpg `0.31.0`, Alembic `1.18.4` |
| **Integración RAG / LLM** | Google Gemini API (`google-genai`) | Modelo Generativo activo: `gemini-3.5-flash-lite` (modelo anterior: `gemini-2.5-flash`) <br> Embeddings activos: `gemini-embedding-2` |
| **Seguridad Backend** | OAuth2 + JWT | `python-jose 3.5.0`, `passlib 1.7.4` (bcrypt) |
| **Framework Frontend** | React Native + Expo | Expo SDK `54.0.36`, React Native `0.81.5`, React `19.1.0` |
| **Enrutamiento Frontend** | Expo Router | `^6.0.23` (File-based routing) |
| **Estilos Frontend** | NativeWind / Tailwind CSS | `nativewind ^4.2.5`, `tailwindcss ^3.4.19` |
| **Estado Global Frontend** | Zustand | `^5.0.14` |
| **Cliente HTTP** | Axios | `^1.17.0` (Con autodetección dinámica de IP host local) |
| **Internacionalización** | i18next + react-i18next | `i18next ^26.3.2`, `react-i18next ^17.0.8` |
| **Orquestación local** | Docker Compose | Definición de servicios `db` y `backend` con volumen persitente `postgres_data` |

---

## 3. Variables de Entorno Detectadas

Identificadas en `.env.example` y `.env`:

| Variable | Tipo | Descripción / Valor por defecto |
|---|---|---|
| `DB_USER` | Config BD | Usuario de PostgreSQL (`postgres`) |
| `DB_PASSWORD` | Config BD | Contraseña de PostgreSQL (`postgres`) |
| `DB_NAME` | Config BD | Nombre de la base de datos (`tutoria_db`) |
| `DB_HOST` | Config BD | Host de PostgreSQL (`db` para Docker, `localhost` para ejecuciones nativas) |
| `DB_PORT` | Config BD | Puerto de PostgreSQL (`5433` expuesto en Docker Compose) |
| `SECRET_KEY` | Seguridad | Clave secreta para firma de tokens JWT |
| `ALGORITHM` | Seguridad | Algoritmo de cifrado JWT (`HS256`) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Seguridad | Duración del token de acceso (`60` minutos) |
| `GEMINI_API_KEY` | API Key | Clave de acceso a Google AI Studio |

---

## 4. Matriz "Qué Existe vs. Qué Falta" por Componente

| Componente | Estado Actual (Qué Existe) | Brecha Detectada (Qué Falta) |
|---|---|---|
| **Backend (Arquitectura)** | Estructura en 3 capas (`domain`, `application`, `infrastructure`). Modelos de dominio (`entities`), casos de uso (`use_cases`), endpoints FastAPI (`v1/endpoints/`) y repositorios con SQLAlchemy async. | La carpeta `domain/schemas/` está vacía. Los esquemas Pydantic/DTOs están declarados dentro de la infraestructura/entidades o importados de manera no estrictamente segregada. |
| **Pipeline RAG** | Ingesta de 9 documentos JSON en `backend/corpus/`. Adaptador `GeminiAdapter` implementando `gemini-embedding-2` (768 dim) y `gemini-3.5-flash-lite` (modelo anterior: `gemini-2.5-flash`). Búsqueda por coseno con umbral `max_cosine_distance=0.45`, fallback léxico controlado (`AND` con normalización Unicode), política de abstención y script de regeneración estricto (`allow_embedding_fallback=False`). | Migración HNSW preparada (`6f892a019e42`); pendiente de aplicación en el entorno desplegado. Script de regeneración listo en código, pendiente de ejecución operativa. Pendiente calibración fina con Golden Dataset (Fase 5). |
| **Frontend Móvil** | Estructura por roles (`(estudiante)`, `(tutor)`, `(admin)`). Autenticación JWT integrada, cliente Axios dinámico, tiendas Zustand (Auth, Chat, Session, Notifications, etc.), interfaz limpia y multilingüe. | Algunas vistas consumen mocks o carecen de manejo centralizado de errores ante fallas de red backend. |
| **Banco de Pruebas (Tests)** | Suite automatizado de pruebas unitarias en `backend/tests/unit/` (`test_rag_quality.py`, `test_chat_use_cases.py`, `test_quiz_gemini_client.py`, `test_auth_application.py`, `test_session_application.py`, `test_streak_application.py`, `test_notification_application.py`). | **Crítico para el paper IEEE:** No existía la carpeta `backend/tests/` ni el golden set de evaluación (preguntas de referencia, ground truth), scripts `test_retrieval.py`, `test_generation.py` ni `run_eval.py` para calcular métricas (Precisión, Cobertura, Pertinencia). |
| **Documentación** | `README.md` de instalación general y `frontend/README.md`. | No existía la carpeta `/documentacion/` con la especificación formal del proyecto, diagramas Mermaid RAG, análisis hexagonal, auditoría de RAG, evaluación de frontend ni reporte consolidado IEEE. |

---

## 5. Resumen de Creación de Carpetas (Fase 0)

Se han preparado y formalizado los siguientes directorios requeridos por el plan de auditoría:
- `/documentacion/` (Creado)
- `/backend/tests/` (Creado)
