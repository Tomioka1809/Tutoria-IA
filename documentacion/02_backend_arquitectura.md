# Evaluación de Arquitectura Hexagonal — Backend TutorIA (Fase 2)

## 1. Diagnóstico General de Separación de Capas

Se auditó la arquitectura del backend en Python / FastAPI comprobando la regla fundamental de la **Arquitectura Hexagonal**: las dependencias deben apuntar siempre hacia el centro (`infrastructure` → `application` → `domain`).

```text
  [ Infrastructure ] ───► [ Application ] ───► [ Domain ]
  (FastAPI, SQLAlchemy,       (Use Cases,         (Entities,
   Gemini Adapter, JWT)        Ports/Interfaces)   Exceptions, Schemas)
```

### Resumen del Cumplimiento por Capas:
- **Capa de Dominio (`app/domain/`)**: Contiene las entidades dataclass y excepciones de negocio. **Correcto:** No depende de bases de datos ni de frameworks web.
- **Capa de Aplicación (`app/application/`)**: Define los casos de uso (`AuthUseCase`, `ChatUseCase`, etc.) y los puertos abstractos (`LLMPort`, `UserRepositoryPort`). **Infracción parcial:** Existen dependencias directas de `HTTPException` (FastAPI) y consultas SQL directas mediante SQLAlchemy dentro de `ChatUseCase`.
- **Capa de Infraestructura (`app/infrastructure/`)**: Implementa los routers de FastAPI, los repositorios con SQLAlchemy async y el adaptador de Google Gemini. **Correcto:** Consume la capa de aplicación e inyecta dependencias de manera limpia en `api/dependencies.py`.

---

## 2. Tabla de Hallazgos Arquitectónicos

| Archivo | Problema | Severidad | Corrección Propuesta | Estado |
|---|---|---|---|---|
| `app/domain/schemas/` | Directorio completamente vacío. Los esquemas Pydantic (DTOs) estaban dispersos únicamente dentro de `entities/`. | Baja | Crear `app/domain/schemas/__init__.py` re-exportando formalmente todos los DTOs de entrada/salida. | **Aplicado** |
| `app/domain/exceptions.py` | Faltaban excepciones de dominio específicas para conflictos de usuario, estados inactivos y recuperación de credenciales. | Media | Ampliar las excepciones de dominio (`UserAlreadyExistsError`, `AccountInactiveError`, `InvalidTokenError`, etc.). | **Aplicado** |
| `app/application/use_cases/auth_use_cases.py` | La capa de aplicación lanza `fastapi.HTTPException` directamente en lugar de usar excepciones de dominio. | Media | Sustituir `HTTPException` por excepciones puras de `DomainException` y capturarlas en el router de FastAPI. | **Corregido / Pendiente de unificación en endpoints** |
| `app/application/use_cases/chat_use_cases.py` | `ChatUseCase` importa `sqlalchemy` y los modelos ORM de infraestructura para ejecutar herramientas (*Tool Calling*) directamente sobre la BD. | Alta | ⚠️ **Requiere confirmación**: Extraer la lógica de consulta SQL de `get_assigned_tutors`, `get_assigned_students` y `get_calendar_events` a métodos abstractos dentro de `UserRepositoryPort` y `SessionRepositoryPort`. | **Marcado para confirmación** |
| `app/infrastructure/adapters/gemini_adapter.py` | El adaptador de Gemini invoca `gemini-embedding-001` con dimensión 768, discrepando con la especificación de `text-embedding-004`. | Media | ⚠️ **Requiere confirmación**: Unificar el modelo de embedding en `GeminiAdapter` y verificar compatibilidad dimensional con el índice `pgvector` de la base de datos en la Fase 3. | **Marcado para confirmación** |

---

## 3. Correcciones Aplicadas en la Fase 2

1. **Población del módulo `app/domain/schemas/`**: Se creó [`backend/app/domain/schemas/__init__.py`](file:///home/tsuki/Downloads/React-Native/backend/app/domain/schemas/__init__.py) consolidando y exponiendo todos los esquemas Pydantic (`UserCreate`, `UserOut`, `MessageOut`, `Token`, etc.).
2. **Ampliación de Excepciones de Dominio**: Se actualizaron las clases de error en [`backend/app/domain/exceptions.py`](file:///home/tsuki/Downloads/React-Native/backend/app/domain/exceptions.py) para ofrecer un desacoplamiento limpio frente a los códigos HTTP de FastAPI.

---

## 4. Cambios Mayores que Requieren Confirmación (`⚠️ requiere confirmación`)

### ⚠️ Propuesta 1: Refactorización de *Tool Calling* en `ChatUseCase`
- **Motivo:** Actualmente, `ChatUseCase` rompe el aislamiento hexagonal al ejecutar directamente queries `select(TutorAssignment)` y `select(Event)` con `AsyncSession` de SQLAlchemy.
- **Acción sugerida:** Delegar la construcción de los datos de tutores, estudiantes y calendario a los repositorios de infraestructura `UserRepository` y `SessionRepository`, manteniendo `ChatUseCase` 100% agnóstico a la persistencia.

### ⚠️ Propuesta 2: Unificación de Excepciones en Controladores API
- **Motivo:** Homogeneizar las respuestas de error en la API mediante decoradores/middleware de FastAPI que traduzcan `UserAlreadyExistsError` -> `HTTP 409`, `InvalidCredentialsError` -> `HTTP 401`, etc.
