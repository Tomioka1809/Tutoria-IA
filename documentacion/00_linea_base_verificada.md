# Línea Base Verificada — TutorIA

## 1. Fecha y alcance de la auditoría

- **Fecha de ejecución:** 21 de Julio de 2026.
- **Entorno de ejecución:** Linux (x86_64).
- **Modo de auditoría:** Inspección estática de código y verificación de línea base en tiempo de ejecución de solo lectura (Fase 0 y Fase 5).
- **Alcance:** Verificación de la estructura real del repositorio, comparación de las afirmaciones documentales en la carpeta `/documentacion/` frente al código fuente en `/backend` y `/frontend`, comprobación del estado de Git y validación con `verificar_tutoria.py --fase 0 --verbose` y `verificar_tutoria.py --fase 5 --verbose`.

---

## 2. Estado de Git

- **Rama actual:** `test/fase-5-banco-pruebas-rag` (HEAD `0372c9b`).
- **Estado del árbol de trabajo (*working tree*):** Cambios locales de refactorización de prueba no comprometidos.
- **Configuración de remotos:** Sin upstream configurado para la rama actual de trabajo.
- **Último commit registrado:** `0372c9b` - *"docs: formalizar alcance y subfases del benchmark RAG"*.
- **Commits locales de la Fase 5:** Nueve commits acumulados desde el commit base `b0d339b`.

---

## 3. Estructura real del repositorio

Se constata la presencia física de la siguiente jerarquía de directorios y componentes principales:

```text
React-Native/
├── .env.example                         # Plantilla de configuración de entorno
├── docker-compose.yml                   # Orquestación de PostgreSQL pgvector y FastAPI
├── README.md                            # Documentación general de inicio rápido (Modelo activo: gemini-3.5-flash-lite)
├── verificar_tutoria.py                 # Runner automatizado de verificación de fases
├── backend/                             # API Backend en FastAPI (Python 3.14 / 3.12)
│   ├── alembic/                         # Migraciones de base de datos SQLAlchemy
│   ├── alembic.ini                      # Configuración de Alembic
│   ├── Dockerfile                       # Definición de contenedor backend
│   ├── requirements.txt                 # Lista de dependencias Python
│   ├── corpus/                          # Material documental del RAG
│   │   ├── heredado/                    # 9 JSON de normativa en el formato original
│   │   ├── fuentes/                     # 4 JSON transcritos de fuentes que no son PDF
│   │   └── estructurado/                # 20 JSON: la salida que se indexa
│   ├── app/                             # Código fuente estructurado en capas
│   │   ├── main.py                      # Punto de entrada ASGI
│   │   ├── domain/                      # Entidades, excepciones y esquemas de dominio
│   │   ├── application/                 # Servicios de aplicación, casos de uso y puertos
│   │   └── infrastructure/              # API FastAPI, adaptadores Gemini (gemini-3.5-flash-lite), DB y seguridad
│   └── tests/                           # Suite de evaluación RAG (Golden dataset + evaluadores)
│       ├── dataset/golden_set.json      # Golden Set Oficial de 15 casos estratificados
│       ├── dataset/golden_set_32_historico.json # Banco histórico de 32 casos (Hash e58db793...)
│       ├── dataset/golden_set_manifest.json # Manifiesto de trazabilidad formal (models: gemini-3.5-flash-lite / gemini-embedding-2)
│       ├── resultados/                  # Directorio de resultados activos oficiales (eval_results.json, eval_results.csv)
│       │   └── historico_32/            # Resultados históricos archivados (eval_results_32.json, eval_results_32.csv)
│       ├── evaluation_support.py        # Soporte técnico de retries, rate-limiter, hash e identidades
│       ├── test_retrieval.py            # Evaluador de la etapa de recuperación RAG
│       ├── test_generation.py           # Evaluador de la etapa de generación LLM
│       ├── run_eval.py                  # Runner de evaluación de benchmark
│       ├── verify_evaluation_integrity.py # Verificador estático de integridad de artefactos
│       └── unit/                        # Suite unitaria (108+ tests en test_evaluation_integrity.py, 130 tests totales)
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
- **Google GenAI SDK:** `google-genai`
- **Modelo Generativo Activo:** `gemini-3.5-flash-lite`
- **Modelo de Embedding Activo:** `gemini-embedding-2` (768 dimensiones)
- **Modelo Generativo Anterior:** `gemini-2.5-flash`

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
| Google Gemini API utiliza `gemini-embedding-2` para embeddings de 768 dim y `gemini-3.5-flash-lite` para generación. | `README.md`, `00_inventario.md`, `03_pipeline_rag.md` | `GeminiAdapter` utiliza `gemini-3.5-flash-lite` para respuestas y Tool Calling, y `gemini-embedding-2` para vectores de 768 dim. | `RESOLVIDO_EN_FASE_5C` | Se actualizó `gemini-3.5-flash-lite` como modelo generativo activo y `gemini-embedding-2` como embedding. |
| CorpusRepository realiza búsquedas por distancia L2 (`<->`). | `00_inventario.md`, `03_pipeline_rag.md` | En `corpus_repository.py` se invoca `cosine_distance` (`<=>`) e inyecta búsqueda por texto. | `CONTRADICTORIO` | El código fue modificado para usar distancia Coseno, pero la doc previa citaba L2. |
| La carpeta `domain/schemas/` está vacía. | `00_inventario.md`, `02_backend_arquitectura.md` | Existe `backend/app/domain/schemas/__init__.py` que exporta todos los DTOs de Pydantic. | `CONTRADICTORIO` | El directorio fue poblado en refactorizaciones previas. |
| `QuizAPI.generateQuiz` usa `fetch` sin cabecera `Authorization`. | `04_frontend.md` | En `frontend/src/api/services.ts` se inyecta `Authorization: Bearer <token>` desde Zustand. | `CONTRADICTORIO` | El servicio frontend ya adjunta el Bearer token si el usuario está autenticado. |
| El cliente Axios incluye la IP `192.168.18.27` como fallback duro. | `04_frontend.md` | En `frontend/src/api/api-config.ts` y `client.ts` se eliminó la IP fija. Se prioriza `EXPO_PUBLIC_API_URL`, seguido de autodetección `hostUri`. | `RESUELTO_EN_FASE_4A` | Se eliminó la IP fija hardcodeada y se centralizó la resolución dinámica. |
| Existe un Golden Set con scripts de evaluación RAG. | `05_banco_pruebas.md` | Banco oficial migrado a 15 casos estratificados deterministas (`golden_set.json`), banco histórico de 32 preservado (`golden_set_32_historico.json`) y manifiesto `golden_set_manifest.json`. | `CONFIRMADO_EN_EJECUCION` | Banco RAG refactorizado con control de cuota 15s, aislamientos por usuario temporal y suite de integridad. |
| El RAG no posee umbral de similitud (*score threshold*). | `03_pipeline_rag.md`, `06_reporte_final.md` | Implementado `max_cosine_distance=0.45` en `CorpusRepository` y `RAGRetrievalPolicy`. | `RESUELTO_EN_CODIGO` | Filtro por distancia coseno activado en código para descartar fragmentos irrelevantes. |
| La tabla `corpus_chunks` incluye un índice vectorial `HNSW`. | `03_pipeline_rag.md` | Creada migración Alembic `6f892a019e42_add_hnsw_index_to_corpus_chunks.py` con `vector_cosine_ops`. | `PENDIENTE_DE_DESPLIEGUE` | Migración HNSW preparada en código, pendiente de aplicación en base de datos PostgreSQL real. |
| ChatUseCase ejecuta consultas SQL directas de infraestructura. | `02_backend_arquitectura.md` | En `chat_use_cases.py` se desacoplaron las herramientas usando puertos abstractos. | `RESUELTO_EN_FASE_2` | Resuelto en la Fase 2C2B. |
| El sistema está totalmente operativo sin restricciones. | `06_reporte_final.md` | Al hacer solicitudes masivas se pueden experimentar errores HTTP 429 (`RESOURCE_EXHAUSTED`) o indisponibilidad de modelo previo. | `RESTRICCION_EXTERNA_DOCUMENTADA` | El sistema es funcional en su arquitectura principal, pero la ejecución masiva del benchmark está condicionada por las cuotas externas de Gemini. Mitigado mediante el benchmark oficial de 15 casos, rate-limiter de 15s, migración a `gemini-3.5-flash-lite`, control estricto de errores y protección de resultados incompletos. |

---

## 8. Problemas detectados

| ID | Componente | Problema | Severidad | Estado |
|---|---|---|---|---|
| `BASE-001` | Git / Entorno | Repositorio posicionado en la rama `chore/fase-0-linea-base` para la auditoría de línea base. | Baja | Resuelto en Fase 5 (`test/fase-5-banco-pruebas-rag`) |
| `BACK-001` | Backend / Dominio | `auth_use_cases.py` lanza `fastapi.HTTPException` directamente en lugar de usar excepciones de dominio. | Media | Resuelto Fase 2 |
| `BACK-002` | Backend / Aplicación | `ChatUseCase` ejecuta consultas SQL directas de SQLAlchemy para las herramientas de *Tool Calling*. | Alta | Resuelto Fase 2 |
| `RAG-001` | RAG / Embeddings | Discrepancia de modelo resuelta unificando a `gemini-embedding-2` en código y documentación. | Media | Resuelto en Código (Fase 3) |
| `RAG-002` | RAG / Recuperación | Ausencia de umbral resuelta con `max_cosine_distance=0.45` y fallback léxico controlado. | Alta | Resuelto en Código (Fase 3) |
| `RAG-003` | RAG / Base de Datos | Ausencia de índice vectorial resuelta con migración HNSW (`vector_cosine_ops`). | Media | Pendiente de Despliegue (Fase 3) |
| `FRONT-001` | Frontend / API | IP LAN hardcodeada (`192.168.18.27`) eliminada; resuelto con `EXPO_PUBLIC_API_URL` y autodetección por Expo `hostUri`. | Baja | Resuelto Fase 4A |
| `FRONT-002` | Frontend / UX | Manejo de errores centralizado con normalización pura (`api-error.ts`), filtrado de secretos/trazas, retroalimentación i18n y deduplicación por mapa. | Media | RESUELTO_EN_FASE_4B |
| `FRONT-003` | Frontend / Calendario | Separación formalizada entre actividades personales locales (`useActivityStore`) y tutorías persistidas (`useSessionStore`). | Media | RESUELTO_EN_FASE_4C |
| `FRONT-004` | Frontend / Datos Reales | Eliminación de datos ficticios visibles y resolución determinista de tutor. | Media | RESUELTO_EN_FASE_4D |
| `FRONT-005` | Frontend / Calidad Estática | Cierre de advertencias ESLint (36 a 0), corrección semántica de dependencias de hooks y script `verify:quality`. | Baja | RESUELTO_EN_FASE_4E |
| `F5-001` | Banco de Pruebas RAG | Trazabilidad y robustez del banco RAG de 15 casos. Modo estricto sin fallback, reintentos de capa única, rate-limiter de 15s, sanitización de logs, escritura atómica de artefactos JSON/CSV y aislamiento transaccional por usuario temporal. **RESUELTO_TECNICAMENTE_EN_FASE_5C**. | Alta | **CERRADO_CON_RESULTADOS_OFICIALES_Y_ANALISIS_CUANTITATIVO_EN_FASE_5D** |
| `F5-002` | Banco de Pruebas RAG | Interrupción de la corrida masiva previa de 32 casos por HTTP 429 `RESOURCE_EXHAUSTED`. Se determinó redefinir formalmente el alcance del benchmark a 15 casos estratificados deterministas. La corrida previa fue interrumpida manualmente y sus resultados parciales no serán reutilizados. | Alta | **MITIGADA_POR_REDEFINICION_FORMAL_DEL_ALCANCE** |
| `F5-003` | Banco de Pruebas RAG | Migración del modelo generativo activo a `gemini-3.5-flash-lite` para reemplazar el modelo previo discontinuado. Ejecución oficial completada sin errores de infraestructura. | Alta | **CERRADO_TRAS_VALIDACION_EXITOSA_CON_GEMINI_3_5_FLASH_LITE_EN_FASE_5C** |
| `F5D-001` | Banco de Pruebas RAG | Baja recuperación vectorial en consultas internas (10 de los 12 casos obtuvieron precisión y cobertura 0.0; las causas se presentan como hipótesis para diagnóstico posterior). | Alta | **REGISTRADO_COMO_RECOMENDACION_FASE_POSTERIOR** |
| `F5D-002` | Banco de Pruebas RAG | Abstención inconsistente en consultas fuera de dominio (alucinación en 2 de 3 casos). | Media | **REGISTRADO_COMO_RECOMENDACION_FASE_POSTERIOR** |
| `F5D-003` | Banco de Pruebas RAG | Limitaciones conocidas en clasificación agregada (`success` en ID 8 con texto de abstención) y detección de frases léxicas de abstención (ID 29). | Media | **REGISTRADO_COMO_RECOMENDACION_FASE_POSTERIOR** |
| `TEST-001` | Banco de Pruebas | Vulnerabilidad a cuotas gratuitas de la API de Gemini (HTTP 429) en ejecuciones masivas del benchmark. | Media | Mitigado con `GeminiRateLimiter` (15s) y redefinición a 15 casos con `gemini-3.5-flash-lite` |
| `F6A-001` | Auditoría Fase 6A | Advertencias de deprecación por sintaxis `class Config:` de Pydantic V1 en modelos y DTOs del backend. | Media | **CERRADO_EN_FASE_6B_1** |
| `F6A-002` | Auditoría Fase 6A | Warning documental `MODULE_TYPELESS_PACKAGE_JSON` en validación de empaquetado del frontend. | Baja | **ACEPTADO_COMO_OBSERVACION_INFORMATIVA** |
| `F6A-003` | Auditoría Fase 6A | Banner provisional y estados pendientes documentados en `06_reporte_final.md`. | Media | **CERRADO_EN_FASE_6C** |
| `F6A-004` | Auditoría Fase 6A | Ausencia de validación explícita de `APP_ENV` y protección contra claves `SECRET_KEY` débiles o por defecto en producción. | Alta | **CERRADO_EN_FASE_6B_2** |
| `F6A-005` | Auditoría Fase 6A | Ausencia de canal automatizado de integración continua (CI/CD). | Baja | **REGISTRADO_COMO_MEJORA_FUTURA** |
| `F6A-006` | Auditoría Fase 6A | Permisividad con contraseñas por defecto de PostgreSQL (`DB_PASSWORD=postgres`) en entornos de producción. | Alta | **CERRADO_EN_FASE_6B_2** |

---

## 9. Riesgos antes de modificar el proyecto

1. **Cuotas de API (Google AI Studio):** El nuevo alcance oficial de 15 casos con `gemini-3.5-flash-lite` minimiza el riesgo de agotamiento de cuota durante el benchmark. Se debe mantener el rate-limiter de 15s por solicitud.
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
  # Se ejecuta desde la raiz del repositorio: --root sale del directorio actual.
  python3 backend/tests/verificar_tutoria.py --fase 0 --verbose
  python3 backend/tests/verificar_tutoria.py --fase 5 --verbose --salida /tmp/reporte_tutoria_fase5c_gate_definitivo.json
  ```
- **Ejecución del suite de evaluación del Chatbot RAG (Paper IEEE):**
  ```bash
  # Pruebas unitarias de integridad y aislamiento (164 pruebas locales aprobadas)
  PYTHONPATH=backend backend/venv/bin/python -m pytest -q --durations=15 backend/tests/unit/test_runtime_security.py backend/tests/unit/test_evaluation_integrity.py backend/tests/unit/test_rag_quality.py backend/tests/unit/test_chat_use_cases.py

  # Verificador estático de integridad de artefactos (24 verificaciones aprobadas)
  PYTHONPATH=backend backend/venv/bin/python backend/tests/verify_evaluation_integrity.py
  ```

---

## 12. Criterio de cierre y estado consolidado de la Fase 6

### Commits Registrados en la Fase 6:
- `cfd78b8`: *"refactor: migrar modelos a configuración Pydantic V2"* (Fase 6B-1)
- `bafa79e`: *"fix: endurecer configuración de seguridad en producción"* (Fase 6B-2)

### Resultados Técnicos Consolidados:
- 15 clases migradas mediante `ConfigDict` (Pydantic V2).
- 164 pruebas unitarias aprobadas al cerrar la Fase 6C (0 fallidas; 162 al cerrar la Fase 6B tras incorporar 18 pruebas de seguridad, y 2 pruebas documentales añadidas en la Fase 6C).
- 1 warning externo de `google-genai` (cero warnings en código del proyecto).
- 24 verificaciones de integridad RAG aprobadas (0 fallidas).
- Cinco verificadores frontend finalizados con exit code 0 (`verify:quality`, `lint`, `type-check`, etc.).
- Cero secretos reales expuestos en la base de código.
- `APP_ENV` admite los entornos `development`, `test` y `production`.
- Bloqueo estricto de `SECRET_KEY` insegura en entorno `production`.
- Bloqueo estricto de `DB_PASSWORD` por defecto en entorno `production`.

### Estado Final de las Fases:
- **Fase 0 (Auditoría Inicial):** **COMPLETADA**
- **Fase 5 (Benchmark RAG y Análisis Cuantitativo):** **CERRADA**
- **Fase 6A (Auditoría Integral y Definición del Estado Final):** **COMPLETADA**
- **Fase 6B (Migración Pydantic V2 y Seguridad por Entorno):** **COMPLETADA**
- **Fase 6C (Cierre Documental Definitivo):** **COMPLETADA**
- **Fase 6 (Cierre Técnico del Proyecto):** **CIERRE_TECNICO_COMPLETADO**
- **Fase 6D:** **ENTREGA_E_INTEGRACION_GIT**

---

## 13. Conclusión

La auditoría de la **Fase 0**, el cierre del benchmark de la **Fase 5** y el desarrollo técnico de la **Fase 6** (Subfases 6A, 6B y 6C) confirman que **TutorIA** satisface de manera verificable los estándares de arquitectura hexagonal, integridad de datos, seguridad por entorno y calidad de pruebas automatizadas. Todos los hallazgos críticos de auditoría han sido remediados o integrados como recomendaciones posteriores, declarando la **Fase 6** en estado **CIERRE_TECNICO_COMPLETADO**.
