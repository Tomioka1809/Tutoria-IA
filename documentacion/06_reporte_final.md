# Reporte Final y Correcciones Consolidadas — Proyecto TutorIA (Fase 6)

> ⚠️ **Estado: BORRADOR PROVISIONAL.**
> Este documento no constituye el cierre de la Fase 5 ni de la Fase 6. El benchmark oficial de 15 casos se encuentra pendiente de ejecución en la Fase 5C. El análisis cuantitativo, la actualización documental y el cierre definitivo pertenecen a la Fase 5D, la cual comenzará después de obtener los resultados oficiales de 5C.

Este documento representa el informe consolidado en progreso del proceso de auditoría, documentación, refactorización y evaluación del sistema **TutorIA**, desarrollado para la gestión de tutorías académicas y asistencia conversacional RAG en el curso de Inteligencia Artificial (IF651, UNSAAC).

---

## 1. Resumen Ejecutivo del Proyecto

- **Estado General:** El sistema cuenta con una arquitectura Hexagonal sólida en el Backend (FastAPI, PostgreSQL `pgvector`) y una aplicación móvil Expo SDK 54 en el Frontend.
- **RAG & LLM:** Integración con Google Gemini (modelo generativo activo `gemini-3.5-flash-lite`, modelo de embedding activo `gemini-embedding-2` de 768 dim, modelo generativo anterior `gemini-2.5-flash`) combinando recuperación vectorial semántica con ejecución de herramientas en tiempo real (*Tool Calling*). Modo estricto sin fallbacks silenciosos activado en la suite de evaluación.
- **Evaluación Experimental (Paper IEEE):** Redefinición formal del alcance experimental del proyecto hacia un **Golden Set oficial estratificado de 15 casos** (`facil: 7, ambiguo: 5, fuera_de_alcance: 3`). Fase 5A completada (Integridad y robustez del evaluador); Fase 5B completada (Ejecución parcial controlada completada sobre los casos 1, 16 y 26, con tres casos procesados, cero errores de infraestructura, artefactos temporales y cero usuarios temporales residuales); infraestructura técnica de 5C preparada y validada localmente con suite unitaria (130 pruebas locales aprobadas) y verificadores de integridad estáticos, con la corrida oficial de 15 casos pendiente de ejecución en la Fase 5C usando `gemini-3.5-flash-lite`. Los 32 casos históricos fueron preservados en `dataset/golden_set_32_historico.json` (Hash `e58db793...`) y sus resultados anteriores archivados en `resultados/historico_32/`. El hallazgo `F5-001` registra el estado **`RESUELTO_TECNICAMENTE_EN_FASE_5C / PENDIENTE_CIERRE_CUANTITATIVO_EN_FASE_5D`**, la incidencia `F5-002` fue registrada como **`MITIGADA_POR_REDEFINICION_FORMAL_DEL_ALCANCE`**, y la incidencia `F5-003` fue registrada como **`RESUELTO_TECNICAMENTE_POR_MIGRACION_A_GEMINI_3_5_FLASH_LITE / PENDIENTE_VALIDACION_EN_BENCHMARK_5C`**. El análisis cuantitativo y el cierre pertenecerán a la Fase 5D (la cual comenzará después de obtener los resultados oficiales de 5C).

---

## 2. Matriz Consolidada de Hallazgos y Priorización

| Componente | Hallazgo | Severidad | Estado | Acción Realizada / Recomendada |
|---|---|---|---|---|
| **Banco de Pruebas** | Inconsistencia entre cifras históricas documentadas y artefactos de evaluación. | **Alto** | **RESUELTO_TECNICAMENTE_EN_FASE_5C / PENDIENTE_CIERRE_CUANTITATIVO_EN_FASE_5D** | Implementados reintentos de capa única, modo estricto, rate-limiter 15s, sanitización de logs, escritura atómica JSON/CSV y usuario temporal determinista. Medición cuantitativa oficial **pendiente de la finalización de la Fase 5C; análisis cuantitativo, actualización documental y cierre pendientes de la Fase 5D**. |
| **Banco de Pruebas** | Interrupción de la corrida masiva previa de 32 casos por error HTTP 429 `RESOURCE_EXHAUSTED`. | **Alto** | **MITIGADA_POR_REDEFINICION_FORMAL_DEL_ALCANCE** | Redefinición formal del benchmark a 15 casos estratificados deterministas. Corrida previa de 32 interrumpida manualmente; resultados no reutilizados. Medición oficial **pendiente de ejecución de 15 casos en la Fase 5C**. |
| **Banco de Pruebas** | Interrupción de la primera ejecución de 15 casos por error HTTP 404 `NOT_FOUND` al estar `gemini-2.5-flash` no disponible para proyectos nuevos. | **Alto** | **RESUELTO_TECNICAMENTE_POR_MIGRACION_A_GEMINI_3_5_FLASH_LITE / PENDIENTE_VALIDACION_EN_BENCHMARK_5C** | Migrado el modelo generativo activo a `gemini-3.5-flash-lite` para todas las llamadas reales de generación. La corrida fue interrumpida, no generó métricas oficiales, los resultados activos fueron retirados y no quedaron usuarios temporales residuales. La ejecución comenzará desde cero en la Fase 5C. |
| **Pipeline RAG** | `CorpusRepository` utilizaba distancia euclidiana L2 (`<->`) en lugar de distancia Coseno (`<=>`). | **Alto** | **Resuelto** | Actualizado `corpus_repository.py` utilizando `cosine_distance()` para alineación vectorial semántica. |
| **Arquitectura Backend** | `ChatUseCase` ejecuta consultas SQL directas sobre SQLAlchemy para las herramientas de *Tool Calling*. | **Alto** | **Resuelto** | Desacopladas las herramientas en `ChatUseCase` hacia repositorios y puertos abstractos. |
| **Frontend API** | `QuizAPI.generateQuiz` realizaba peticiones `fetch` sin inyectar la cabecera `Authorization: Bearer <token>`. | **Medio** | **Resuelto** | Migrado a cliente Axios inyectando dinámicamente el token JWT desde `useAuthStore`. |
| **Arquitectura Backend** | El paquete `app/domain/schemas/` estaba vacío; los DTOs estaban dispersos en `entities/`. | **Medio** | **Resuelto** | Creado `domain/schemas/__init__.py` re-exportando formalmente todos los esquemas Pydantic. |
| **Arquitectura Backend** | Catálogo insuficiente de excepciones puras de dominio para desacoplar respuestas de FastAPI. | **Medio** | **Resuelto** | Ampliado `domain/exceptions.py` con clases de error para autenticación y gestión de usuarios. |
| **Pipeline RAG** | Ausencia de *Score Threshold* (umbral mínimo de similitud). Siempre se inyectan 6 fragmentos. | **Medio** | **Resuelto en Código** | Implementado `max_cosine_distance=0.45` con fallback léxico `AND` y política de abstención. |
| **Base de Datos** | La tabla `corpus_chunks` en `pgvector` no incluye un índice vectorial `HNSW`. | **Bajo** | **Pendiente Despliegue** | Migración Alembic `6f892a019e42` creada en código; pendiente de ejecución operativa en PostgreSQL real. |
| **Frontend App** | La IP `192.168.18.27` estaba hardcodeada en el *fallback* del cliente Axios (`client.ts`). | **Bajo** | **Resuelto (Fase 4A)** | Eliminada la IP fija; resuelto mediante `resolveApiUrl()` con soporte para `EXPO_PUBLIC_API_URL` y `hostUri`. |

---

## 3. Changelog Consolidado de Cambios Aplicados

### Fase 0 — Reconocimiento y Estructura
- Creadas las carpetas `/documentacion/` y `/backend/tests/`.
- Elaborado [00_inventario.md](00_inventario.md) con el árbol completo del repositorio.

### Fase 1 — Descripción General del Proyecto
- Elaborado el documento maestro [01_descripcion_proyecto.md](01_descripcion_proyecto.md).

### Fase 2 — Backend y Arquitectura Hexagonal
- Poblado `backend/app/domain/schemas/__init__.py` consolidando los DTOs.
- Ampliado `backend/app/domain/exceptions.py` con excepciones puras de dominio.

### Fase 3 — Pipeline RAG
- Modificado `backend/app/infrastructure/database/repositories/corpus_repository.py` usando `cosine_distance()`.

### Fase 4 — Frontend React Native (Expo)
- Solucionada la URL dinámica, manejo centralizado de errores, modelo puro del calendario, integridad de datos reales y 0 warnings en ESLint.

### Fase 5 — Robustez, Control de Cuota, Aislamiento y Redefinición del Benchmark RAG (15 Casos)

#### 3.1 Correcciones Técnicas Implementadas
- **Modelo Generativo Activo `gemini-3.5-flash-lite`:** Reemplazado `gemini-2.5-flash` en `GeminiAdapter` para respuestas conversacionales, pasos de Tool Calling y evaluación.
- **Modelo de Embedding Preservado:** Mantenido `gemini-embedding-2` con dimensión 768.
- **Modo Estricto Sin Fallback:** Activado `allow_embedding_fallback=False` y `allow_generation_fallback=False` en los evaluadores para evitar degradaciones no detectadas.
- **Una Sola Capa de Reintentos:** `GeminiAdapter` se configura con `api_max_attempts=1` y la política de reintentos con backoff exponencial acotado se centraliza en `execute_with_retry`.
- **Clasificación Estricta de Errores:** Diferenciación entre errores no transitorios (`NonRetryableError`) y errores transitorios (`InfrastructureError`).
- **Respeto de `RetryInfo`:** Extracción del tiempo recomendado de espera (`retryDelay`) retornado por Gemini SDK.
- **Limitador de Frecuencia (Rate-Limiter):** Implementado `GeminiRateLimiter` con intervalo mínimo de 15 segundos entre solicitudes reales de generación LLM.
- **Limitación en Pasos Internos de Herramientas:** Callback `before_generate_request` en `GeminiAdapter` para aplicar el limitador de 15s a los pasos de *Tool Calling* en llamadas conversacionales.
- **Métricas Reales de Solicitudes API:** Conteo independiente de `embedding_requests` y `generation_requests`.
- **Sanitización y Truncado de Logs:** Funciones puras `sanitize_secret_message` y `truncate_technical_error`.
- **Escritura Atómica de Artefactos:** Método `atomic_write_artifact_pair` para escribir simultáneamente `eval_results.json` y `eval_results.csv` con respaldo y reversión automática.
- **Separación de Ejecuciones Parciales y Oficiales:** `validate_output_directory` y `is_official_complete_run` garantizan que cualquier filtro escriba fuera del directorio oficial.
- **Aislamiento Atómico por Usuario Temporal:** Derivación determinista de identidad por caso mediante SHA-256 de `run_id` y `case_id` (`token` de 12 chars, email `eval_temp_{token}_{case_id}@eval.unsaac.edu.pe`, `student_code` `EV{token}{case_id:04d}`).
- **Limpieza Transaccional Segura:** Método `cleanup_case_eval_user` con verificación previa estricta. Ante discrepancias, rechaza la limpieza con 0 `DELETE`, 0 `commit` y 1 `rollback`.

#### 3.2 Migración al Benchmark Oficial de 15 Casos y Trazabilidad
- **Golden Set Oficial de 15 Casos:** Selección determinista por muestreo sistemático estratificado (`facil: 7, ambiguo: 5, fuera_de_alcance: 3`) sobre los IDs originales `{1, 3, 6, 8, 10, 13, 15, 16, 18, 20, 23, 25, 26, 29, 32}`.
- **Preservación del Banco Histórico:** El dataset original de 32 casos fue guardado en `backend/tests/dataset/golden_set_32_historico.json` con hash SHA-256 obligatorio `e58db793eb82e26d7f0a84e32b9369b725131b2d9513dbcd3fa13fdf036438b1`.
- **Manifiesto de Trazabilidad:** Creado `backend/tests/dataset/golden_set_manifest.json` documentando el mapeo formal, hashes, modelos (`gemini-3.5-flash-lite` y `gemini-embedding-2`) y criterios de completitud oficial (`15/15/15/0/0`).
- **Archivado Histórico de Resultados:** Los resultados anteriores de 32 casos fueron trasladados a `backend/tests/resultados/historico_32/` preservando sus hashes `5e3c6837...` y `4f0bf77f...`.
- **Estado de `F5-001`, `F5-002` y `F5-003`:** `F5-001` registrado como **`RESUELTO_TECNICAMENTE_EN_FASE_5C / PENDIENTE_CIERRE_CUANTITATIVO_EN_FASE_5D`**, `F5-002` registrado como **`MITIGADA_POR_REDEFINICION_FORMAL_DEL_ALCANCE`**, y `F5-003` registrado como **`RESUELTO_TECNICAMENTE_POR_MIGRACION_A_GEMINI_3_5_FLASH_LITE / PENDIENTE_VALIDACION_EN_BENCHMARK_5C`**.

#### 3.3 Validaciones de Infraestructura Comprobadas
- **Suite Unitaria:** 130 pruebas unitarias aprobadas (con 2 warnings de dependencias externas Pydantic V2 / Python 3.17).
- **Verificador de Integridad Estática:** `verify_evaluation_integrity.py` en estado **PASS** (exit code 0).
- **Verificador Automatizado:** `python3 verificar_tutoria.py --fase 5 --verbose` en estado **PASS=4, WARN=0, FAIL=0, SKIP=1** (Resultado general: APROBADO).

---

## 4. Estado de los Resultados Oficiales y Protección de Hashes

Los resultados del nuevo benchmark de 15 casos se generarán en `backend/tests/resultados/eval_results.json` y `eval_results.csv` una vez ejecutado el benchmark oficial en la Fase 5C.

Los datos históricos permanecen archivados y protegidos en `backend/tests/resultados/historico_32/` bajo los hashes verificados:
- **Golden Set 32 Histórico (`golden_set_32_historico.json`):** `e58db793eb82e26d7f0a84e32b9369b725131b2d9513dbcd3fa13fdf036438b1`
- **JSON Histórico 32 (`eval_results_32.json`):** `5e3c6837f8e3afabaf73bdce2f730a9615f837a67d6ce7e45bd11ac20195e34f`
- **CSV Histórico 32 (`eval_results_32.csv`):** `4f0bf77f5647e6c730cb7ece159386bfdaec34f1c7fdd2e0adf6989a653add3c`
- **Golden Set 15 Oficial (`golden_set.json`):** `736ee36115717130945a3f8902eba4aec93c556a8b14da129c071bdde8b84a75`

La publicación oficial requerirá los 5 criterios de completitud: `total_cases=15`, `selected_cases=15`, `completed_cases=15`, `infrastructure_errors=0`, `skipped_cases=0`, `is_complete=true`.

---

## 5. Recomendaciones Destacadas para el Paper IEEE

Para la redacción del **Paper IEEE**, se sugiere resaltar los siguientes elementos respaldados empíricamente por la Fase 5:

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. SECCIÓN DE ARQUITECTURA DEL SISTEMA                                     │
│    - Destacar el diseño en Arquitectura Hexagonal que aísla la lógica de   │
│      tutoría de los adaptadores de Gemini y PostgreSQL.                     │
│    - Citar la combinación de RAG con Function Calling en tiempo real usando │
│      el modelo generativo activo Gemini 3.5 Flash Lite.                     │
├─────────────────────────────────────────────────────────────────────────────┤
│ 2. SECCIÓN DE EXPERIMENTOS Y METODOLOGÍA DE EVALUACIÓN (EXPERIMENTAL SETUP) │
│    - Presentar la metodología de evaluación sobre el Golden Set estratificado│
│      de 15 casos con aislamiento transaccional atómico por usuario temporal.│
│    - Destacar el rate-limiter serializado de 15s, la clasificación estricta │
│      de errores de infraestructura y la escritura atómica de artefactos.   │
├─────────────────────────────────────────────────────────────────────────────┤
│ 3. SECCIÓN DE RESULTADOS Y TRABAJO FUTURO                                  │
│    - Reportar las métricas de Precisión, Cobertura y Pertinencia una vez    │
│      obtenidos los resultados del benchmark oficial de 15 casos en la      │
│      Fase 5C y realizado el análisis en la Fase 5D.                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Índice Final de Documentación Técnica Generada

Toda la documentación técnica se encuentra organizada en la carpeta `/documentacion/`:

1. [00_linea_base_verificada.md](00_linea_base_verificada.md)
2. [00_inventario.md](00_inventario.md)
3. [01_descripcion_proyecto.md](01_descripcion_proyecto.md)
4. [02_backend_arquitectura.md](02_backend_arquitectura.md)
5. [03_pipeline_rag.md](03_pipeline_rag.md)
6. [04_frontend.md](04_frontend.md)
7. [05_banco_pruebas.md](05_banco_pruebas.md)
8. [06_reporte_final.md](06_reporte_final.md)
