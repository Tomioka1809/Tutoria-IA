# Línea Base Verificada — TutorIA

## 1. Fecha y alcance de la auditoría

- **Fecha de ejecución:** 21 de Julio de 2026.
- **Entorno de ejecución:** Linux (x86_64).
- **Modo de auditoría:** Inspección estática de código y verificación de línea base en tiempo de ejecución de solo lectura (Fase 0).
- **Alcance:** Verificación de la estructura real del repositorio, comparación de las afirmaciones documentales en la carpeta `/documentacion/` frente al código fuente en `/backend` y `/frontend`, comprobación del estado de Git y validación con `verificar_tutoria.py --fase 0 --verbose`.

---

## 2. Estado de Git

- **Rama actual:** `chore/fase-0-linea-base` (derivada del commit `13250c2` en `main`).
- **Estado del árbol de trabajo (*working tree*):** Limpio (`nothing to commit, working tree clean`).
- **Último commit registrado:** `13250c2` - *"feat: implement RAG retrieval evaluation system and documentation for the backend architecture"*.
- **Historial reciente (5 últimos commits):**
  - `13250c2`: feat: implement RAG retrieval evaluation system and documentation for the backend architecture
  - `3b11af9`: feat: implement i18n support, add QuickActionsPanel component, and integrate chatbot use cases and database seeding.
  - `79d5538`: Merge branch 'main' of https://github.com/Tomioka1809/Tutoria-IA
  - `e1505d8`: feat: implement core components, admin management modules, and user application routing for the Tutoria-IA platform
  - `2654f6d`: feat: implement modular architecture with new dashboard, profile, and settings components for tutor and student roles

---

## 3. Estructura real del repositorio

Se constata la presencia física de la siguiente jerarquía de directorios y componentes principales:

```text
React-Native/
├── .env.example                         # Plantilla de configuración de entorno
├── docker-compose.yml                   # Orquestación de PostgreSQL pgvector y FastAPI
├── README.md                            # Documentación general de inicio rápido
├── verificar_tutoria.py                 # Runner automatizado de verificación de fases
├── backend/                             # API Backend en FastAPI (Python 3.14 / 3.12)
│   ├── alembic/                         # Migraciones de base de datos SQLAlchemy
│   ├── alembic.ini                      # Configuración de Alembic
│   ├── Dockerfile                       # Definición de contenedor backend
│   ├── requirements.txt                 # Lista de dependencias Python
│   ├── corpus/                          # 9 Archivos de normativa universitaria en formato JSON
│   ├── app/                             # Código fuente estructurado en capas
│   │   ├── main.py                      # Punto de entrada ASGI
│   │   ├── domain/                      # Entidades, excepciones y esquemas de dominio
│   │   ├── application/                 # Servicios de aplicación, casos de uso y puertos
│   │   └── infrastructure/              # API FastAPI, adaptadores Gemini, DB y seguridad
│   └── tests/                           # Suite de evaluación RAG (Golden dataset + evaluadores)
├── frontend/                            # Aplicación Móvil React Native (Expo SDK 54)
│   ├── app/                             # Enrutamiento Expo Router por roles
│   ├── src/                             # Componentes, API clients, Zustand stores e i18n
│   ├── app.json                         # Manifiesto de Expo
│   ├── package.json                     # Dependencias Node.js
│   ├── tailwind.config.js               # Configuración NativeWind
│   └── tsconfig.json                    # Configuración TypeScript
└── documentacion/                       # Reportes y especificaciones técnicas de auditoría
    ├── 00_inventario.md
    ├── 01_descripcion_proyecto.md
    ├── 02_backend_arquitectura.md
    ├── 03_pipeline_rag.md
    ├── 04_frontend.md
    ├── 05_banco_pruebas.md
    └── 06_reporte_final.md
```

---

## 4. Stack y versiones verificadas

### 4.1 Entorno de Ejecución Local
- **Python:** `3.14.6`
- **Node.js:** `v26.5.0`
- **npm:** `11.17.0`
- **Docker Engine:** `29.6.2`
- **Docker Compose:** `v5.3.0`

### 4.2 Backend (`backend/requirements.txt`)
- **FastAPI:** `0.136.3`
- **Uvicorn:** `0.49.0`
- **SQLAlchemy:** `2.0.50`
- **asyncpg:** `0.31.0`
- **Alembic:** `1.18.4`
- **Pydantic:** `2.13.4`
- **pgvector:** Integración nativa (`pgvector.sqlalchemy`)
- **Google GenAI:** SDK oficial `google-genai`

### 4.3 Frontend (`frontend/package.json`)
- **Expo SDK:** `~54.0.36`
- **React Native:** `0.81.5`
- **React:** `19.1.0`
- **Expo Router:** `~6.0.23`
- **NativeWind / Tailwind:** `nativewind ^4.2.5`, `tailwindcss ^3.4.19`
- **Zustand:** `^5.0.14`
- **Axios:** `^1.17.0`
- **i18next:** `^26.3.2`

---

## 5. Configuración de backend, frontend y Docker

- **.env.example:** Define las claves `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `DB_HOST`, `DB_PORT`, `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES` y `GEMINI_API_KEY`.
- **Docker Compose (`docker-compose.yml`):**
  - Servicio `db`: Utiliza la imagen `pgvector/pgvector:pg16`. Mapea el puerto del host `5433` al puerto del contenedor `5432`. Define el volumen persistente `postgres_data`.
  - Servicio `backend`: Construye desde `./backend`, expone el puerto `8000:8000`, monta el volumen `./backend:/app` y depende del servicio `db`.
- **Alembic (`backend/alembic.ini`):** Configurado para migraciones asíncronas PostgreSQL mediante `asyncpg`.

---

## 6. Servicios y puertos detectados

| Servicio | Contenedor | Estado Actual | Puerto Host | Puerto Contenedor |
|---|---|---|---|---|
| **Base de Datos** | `tutoria_db` (`pgvector/pgvector:pg16`) | `Up (En ejecución)` | `5433` | `5432` |
| **Backend API** | `tutoria_backend` (`react-native-backend`) | `Exited (0)` | `8000` | `8000` |

---

## 7. Matriz documentación frente a código

| Afirmación | Documento de origen | Evidencia encontrada | Clasificación | Observación |
|---|---|---|---|---|
| Google Gemini API utiliza `gemini-embedding-2` para embeddings de 768 dim. | `README.md`, `00_inventario.md`, `03_pipeline_rag.md` | Modelos anteriores retirados (modelo anterior y modelo retirado) fueron unificados a `gemini-embedding-2` en la Fase 3. | `RESOLVIDO_EN_FASE_3` | Se unificó `gemini-embedding-2` en código y documentación técnica. |
| CorpusRepository realiza búsquedas por distancia L2 (`<->`). | `00_inventario.md`, `03_pipeline_rag.md` | En `corpus_repository.py` L15 se invoca `cosine_distance` (`<=>`) e inyecta búsqueda por texto. | `CONTRADICTORIO` | El código fue modificado para usar distancia Coseno, pero la doc previa citaba L2. |
| La carpeta `domain/schemas/` está vacía. | `00_inventario.md`, `02_backend_arquitectura.md` | Existe `backend/app/domain/schemas/__init__.py` que exporta todos los DTOs de Pydantic. | `CONTRADICTORIO` | El directorio fue poblado en refactorizaciones previas. |
| `QuizAPI.generateQuiz` usa `fetch` sin cabecera `Authorization`. | `04_frontend.md` | En `frontend/src/api/services.ts` L27-L34 se inyecta `Authorization: Bearer <token>` desde Zustand. | `CONTRADICTORIO` | El servicio frontend ya adjunta el Bearer token si el usuario está autenticado. |
| El cliente Axios incluye la IP `192.168.18.27` como fallback duro. | `04_frontend.md` | En `frontend/src/api/api-config.ts` y `client.ts` se eliminó la IP fija. Se prioriza `EXPO_PUBLIC_API_URL`, seguido de detección dinámica por Expo `hostUri` y fallback `localhost`. | `RESUELTO_EN_FASE_4A` | Se eliminó la IP fija hardcodeada y se centralizó la resolución dinámica por entorno/Expo. |
| Existe un Golden Set de 32 casos con scripts de evaluación. | `05_banco_pruebas.md` | Existen los archivos `backend/tests/dataset/golden_set.json` (32 casos), `test_retrieval.py`, `test_generation.py` y `run_eval.py`. | `CONFIRMADO_EN_EJECUCION` | El script `run_eval.py` y `verificar_tutoria.py` se ejecutan correctamente. |
| El RAG no posee umbral de similitud (*score threshold*). | `03_pipeline_rag.md`, `06_reporte_final.md` | Implementado `max_cosine_distance=0.45` en `CorpusRepository` y `RAGRetrievalPolicy`. | `RESUELTO_EN_CODIGO` | Filtro por distancia coseno activado en código para descartar fragmentos irrelevantes. |
| La tabla `corpus_chunks` incluye un índice vectorial `HNSW`. | `03_pipeline_rag.md` | Creada migración Alembic `6f892a019e42_add_hnsw_index_to_corpus_chunks.py` con `vector_cosine_ops`. | `PENDIENTE_DE_DESPLIEGUE` | Migración HNSW preparada en código, pendiente de aplicación en base de datos PostgreSQL real. |
| ChatUseCase ejecuta consultas SQL directas de infraestructura. | `02_backend_arquitectura.md` | En `chat_use_cases.py` se desacoplaron las herramientas usando puertos abstractos. | `RESUELTO_EN_FASE_2` | Resuelto en la Fase 2C2B. |
| El sistema está totalmente operativo sin restricciones. | `06_reporte_final.md` | Al hacer solicitudes masivas se pueden experimentar errores HTTP 429 (`RESOURCE_EXHAUSTED`) por cuotas de Gemini API. | `DOCUMENTADO_NO_COMPROBADO` | La operatividad continua depende de los límites de cuota de la API Key de Google AI Studio. |

---

## 8. Problemas detectados

| ID | Componente | Problema | Severidad | Fase sugerida |
|---|---|---|---|---|
| `BASE-001` | Git / Entorno | Repositorio posicionado en la rama `chore/fase-0-linea-base` para la auditoría de línea base. | Baja | Fase 0 |
| `BACK-001` | Backend / Dominio | `auth_use_cases.py` lanza `fastapi.HTTPException` directamente en lugar de usar excepciones de dominio. | Media | Resuelto Fase 2 |
| `BACK-002` | Backend / Aplicación | `ChatUseCase` ejecuta consultas SQL directas de SQLAlchemy para las herramientas de *Tool Calling*. | Alta | Resuelto Fase 2 |
| `RAG-001` | RAG / Embeddings | Discrepancia de modelo resuelta unificando a `gemini-embedding-2` en código y documentación. | Media | Resuelto en Código (Fase 3) |
| `RAG-002` | RAG / Recuperación | Ausencia de umbral resuelta con `max_cosine_distance=0.45` y fallback léxico controlado. | Alta | Resuelto en Código (Fase 3) |
| `RAG-003` | RAG / Base de Datos | Ausencia de índice vectorial resuelta con migración HNSW (`vector_cosine_ops`). | Media | Pendiente de Despliegue (Fase 3) |
| `FRONT-001` | Frontend / API | IP LAN hardcodeada (`192.168.18.27`) eliminada; resuelto con `EXPO_PUBLIC_API_URL` y detección dinámica por Expo `hostUri`. | Baja | Resuelto Fase 4A |
| `FRONT-002` | Frontend / UX | Manejo de errores centralizado con normalización pura (`api-error.ts`), filtrado de secretos/trazas, retroalimentación i18n, deduplicación por mapa (`error-feedback.ts`) y opción `notify: false` para evitar alertas duplicadas en consumidores visuales. | Media | RESUELTO_EN_FASE_4B |
| `FRONT-003` | Frontend / Calendario | Separación formalizada entre actividades personales locales (`useActivityStore`) y tutorías persistidas (`useSessionStore`) mediante el modelo puro `CalendarItem` (`calendar-items.ts`), prefijos de ID (`activity:`, `session:`) y sin consumir `/events/` para evitar duplicidad. | Media | RESUELTO_EN_FASE_4C |
| `FRONT-004` | Frontend / Datos Reales | Eliminación de datos y personas ficticias visibles. Implementación de la resolución determinista de tutor (ausencia, asignación disponible o ambigüedad), diferenciación de errores de carga en `useProfile`, eliminación del filtro ficticio en notificaciones y fecha real en recordatorios locales. | Media | RESUELTO_EN_FASE_4D |
| `FRONT-005` | Frontend / Calidad Estática | Cierre de advertencias ESLint (36 a 0), corrección semántica de dependencias de hooks sin supresiones, eliminación de imports y variables sin uso, ajuste compatible de i18next y script `verify:quality`. | Baja | RESUELTO_EN_FASE_4E |
| `F5-001` | Banco de Pruebas RAG | Inconsistencia de métricas históricas entre artefactos y documentación. La Fase 5A implementa trazabilidad, retries, escritura atómica y protección de ejecuciones incompletas; las métricas finales reproducibles requieren la Fase 5B. | Alta | EN_CORRECCION_FASE_5A |
| `TEST-001` | Banco de Pruebas | Vulnerabilidad a cuotas gratuitas de la API de Gemini (HTTP 429) en ejecuciones masivas del benchmark. | Media | EN_CORRECCION_FASE_5A |

---

## 9. Riesgos antes de modificar el proyecto

1. **Cuotas de API (Google AI Studio):** Ejecutar pruebas masivas repetidamente sobre la API gratuita de Gemini puede causar bloqueos temporales por error 429 `RESOURCE_EXHAUSTED`.
2. **Desincronización de Base de Datos:** Alterar modelos SQLAlchemy sin generar y aplicar la migración correspondiente en Alembic desincronizará la base de datos en Docker.
3. **Dirección IP en dispositivos físicos:** Modificar `client.ts` sin mantener la autodetección de `hostUri` puede romper la conexión de la app móvil en dispositivos reales Expo Go.

---

## 10. Comandos reales de instalación e inicio

### 10.1 Backend y Base de Datos (Docker Compose - Recomendado)
```bash
# 1. Copiar plantilla de entorno
cp .env.example .env

# 2. Levantar servicios PostgreSQL (pgvector) y FastAPI
docker compose up -d

# 3. Aplicar migraciones de Alembic
docker compose exec backend alembic upgrade head

# 4. Poblar datos iniciales (Corpus RAG)
docker compose exec backend python -m app.infrastructure.database.seed
```

### 10.2 Frontend Móvil (React Native / Expo)
```bash
# 1. Entrar al directorio frontend e instalar dependencias
cd frontend
npm install

# 2. Iniciar servidor de desarrollo Metro / Expo
npx expo start
```

---

## 11. Comandos de verificación disponibles

- **Verificador automatizado por fases del proyecto:**
  ```bash
  python3 verificar_tutoria.py --fase 0 --verbose
  ```
- **Ejecución del suite de evaluación del Chatbot RAG (Paper IEEE):**
  ```bash
  DB_HOST=localhost DB_PORT=5433 backend/venv/bin/python backend/tests/run_eval.py
  ```

---

## 12. Criterio de cierre de la Fase 0

Se han satisfecho los criterios obligatorios de la Fase 0:
- Inspección completa de código y documentación realizada.
- Verificación automatizada con `verificar_tutoria.py --fase 0 --verbose` en estado `PASS=5, FAIL=0`.
- Documento de línea base `documentacion/00_linea_base_verificada.md` generado sin alterar código ejecutable del backend, frontend ni base de datos.

---

## 13. Conclusión

La auditoría de la **Fase 0** confirma que el proyecto **TutorIA** posee una base funcional sólida, estructurada en Arquitectura Hexagonal y con un pipeline RAG operacional. Se han identificado con precisión las discrepancias entre la documentación existente y la implementación del código (modelo de embedding, índice HNSW, umbral de descarte y acoplamiento de *tool calling* en casos de uso), estableciendo la línea base verificable sobre la cual se procederá en las siguientes fases de refinamiento.
