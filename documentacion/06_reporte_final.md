# Reporte Final y Correcciones Consolidadas — Proyecto TutorIA (Fase 6)

> ⚠️ **Estado: BORRADOR PROVISIONAL.**
> Este documento no constituye el cierre definitivo de la Fase 6. **La Fase 5 ha sido formalmente CERRADA** tras completar la ejecución oficial del benchmark RAG de 15 casos (Fase 5C) y su correspondiente análisis cuantitativo, actualización documental y cierre (Fase 5D). La Fase 6 (Integración final y verificación global del reporte) permanece PENDIENTE.

Este documento representa el informe consolidado en progreso del proceso de auditoría, documentación, refactorización y evaluación del sistema **TutorIA**, desarrollado para la gestión de tutorías académicas y asistencia conversacional RAG en el curso de Inteligencia Artificial (IF651, UNSAAC).

---

## 1. Resumen Ejecutivo del Proyecto

- **Estado General:** El sistema cuenta con una arquitectura Hexagonal sólida en el Backend (FastAPI, PostgreSQL `pgvector`) y una aplicación móvil Expo SDK 54 en el Frontend.
- **RAG & LLM:** Integración con Google Gemini (modelo generativo activo `gemini-3.5-flash-lite`, modelo de embedding activo `gemini-embedding-2` de 768 dim) combinando recuperación vectorial semántica con ejecución de herramientas en tiempo real (*Tool Calling*). Modo estricto sin fallbacks silenciosos activado en la suite de evaluación.
- **Evaluación Experimental (Paper IEEE):** Benchmark RAG oficial de 15 casos completado exitosamente sin errores de infraestructura (`fase5c_official15_flashlite_20260723T033328Z`). Fase 5A completada (Integridad y robustez del evaluador); Fase 5B completada (Ejecución parcial controlada); Fase 5C completada (Ejecución oficial de 15 casos completada sin errores de infraestructura, red ni indisponibilidad del modelo generativo; sin embargo, 13 casos fueron clasificados como model_failure por criterios de calidad funcional); y Fase 5D completada (Análisis cuantitativo y cierre formal). **Fase 5 CERRADA**.
- **Incidencias del Banco de Pruebas:**
  - `F5-001`: **`CERRADO_CON_RESULTADOS_OFICIALES_Y_ANALISIS_CUANTITATIVO_EN_FASE_5D`**
  - `F5-002`: **`MITIGADA_POR_REDEFINICION_FORMAL_DEL_ALCANCE`**
  - `F5-003`: **`CERRADO_TRAS_VALIDACION_EXITOSA_CON_GEMINI_3_5_FLASH_LITE_EN_FASE_5C`**

---

## 2. Matriz Consolidada de Hallazgos y Priorización

| Componente | Hallazgo | Severidad | Estado | Acción Realizada / Recomendada |
|---|---|---|---|---|
| **Banco de Pruebas** | Inconsistencia entre cifras históricas documentadas y artefactos de evaluación. | **Alto** | **CERRADO_CON_RESULTADOS_OFICIALES_Y_ANALISIS_CUANTITATIVO_EN_FASE_5D** | Implementada infraestructura de robustez, ejecución oficial de 15 casos completada y análisis cuantitativo de la Fase 5D registrado formalmente. |
| **Banco de Pruebas** | Interrupción de la corrida masiva previa de 32 casos por error HTTP 429 `RESOURCE_EXHAUSTED`. | **Alto** | **MITIGADA_POR_REDEFINICION_FORMAL_DEL_ALCANCE** | Redefinición formal del benchmark a 15 casos estratificados deterministas. Corrida oficial de 15 casos ejecutada exitosamente con 0 errores de infraestructura (`infrastructure_errors = 0`). |
| **Banco de Pruebas** | Interrupción por error HTTP 404 `NOT_FOUND` debido a la discontinuidad del modelo previa en proyectos nuevos. | **Alto** | **CERRADO_TRAS_VALIDACION_EXITOSA_CON_GEMINI_3_5_FLASH_LITE_EN_FASE_5C** | Migrado el modelo generativo activo a `gemini-3.5-flash-lite` para todas las llamadas reales de generación. Benchmark de 15 casos completado al 100% sin errores de infraestructura. |
| **Banco de Pruebas** | Baja recuperación vectorial en consultas internas (10 de los 12 casos obtuvieron precisión y cobertura 0.0). | **Alto** | **F5D-001 (Recomendación Fase Posterior)** | Identificada debilidad en la etapa de recuperación semántica (`pgvector` / embeddings); causas presentadas como hipótesis para diagnóstico posterior. |
| **Banco de Pruebas** | Abstención inconsistente en consultas fuera de dominio (alucinación gastronómica y matemática). | **Medio** | **F5D-002 (Recomendación Fase Posterior)** | Detectados 2 casos fuera de dominio que generaron contenido ajeno al reglamento. |
| **Banco de Pruebas** | Limitaciones de clasificación agregada (`success` en ID 8 con texto de abstención) y léxica (ID 29). | **Medio** | **F5D-003 (Recomendación Fase Posterior)** | Documentadas limitaciones del marco evaluador en coincidencia estricta de frases de abstención. |
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

### Fase 5 — Benchmark RAG Oficial (15 Casos), Análisis Cuantitativo y Cierre (Fases 5A–5D)

#### 3.1 Correcciones Técnicas e Infraestructura (Fase 5A)
- **Modelo Generativo Activo `gemini-3.5-flash-lite`:** Reemplazado `gemini-2.5-flash` en `GeminiAdapter` para respuestas conversacionales, pasos de Tool Calling y evaluación.
- **Modelo de Embedding Preservado:** Mantenido `gemini-embedding-2` con dimensión 768.
- **Modo Estricto Sin Fallback:** Activado `allow_embedding_fallback=False` y `allow_generation_fallback=False` en los evaluadores.
- **Una Sola Capa de Reintentos:** Centralizada en `execute_with_retry` con backoff exponencial acotado.
- **Limitador de Frecuencia (Rate-Limiter):** Implementado `GeminiRateLimiter` con intervalo mínimo de 15 segundos entre solicitudes reales de generación LLM.
- **Escritura Atómica Paritaria:** Método `atomic_write_artifact_pair` para escribir simultáneamente `eval_results.json` y `eval_results.csv`.
- **Aislamiento Atómico por Usuario Temporal:** Derivación determinista por SHA-256 de `run_id` y `case_id` con limpieza transaccional verificada.

#### 3.2 Ejecución Oficial del Benchmark de 15 Casos (Fase 5C)
- **Ejecución Completada:** `Run ID` oficial `fase5c_official15_flashlite_20260723T033328Z`.
- **Completitud:** `15/15/15/0/0` (`is_complete = true`, 0 errores de infraestructura, 0 casos omitidos).
- **Solicitudes Reales:** 15 solicitudes de embedding y 15 solicitudes de generación ejecutadas contra la API oficial.
- **Distribución de Estados:** 2 casos `success` (13.33%) y 13 casos `model_failure` (86.67%).

#### 3.3 Análisis Cuantitativo Oficial y Cierre de la Fase 5 (Fase 5D)
- **Métricas Globales Obtenidas:**
  - Precisión Global: `0.3333` (33.33%)
  - Cobertura Global: `0.3333` (33.33%)
  - Pertinencia Global: `0.3111` (31.11%)
- **Métricas por Categoría:**
  - **Fácil (7 casos):** Precisión `0.2857`, Cobertura `0.2857`, Pertinencia `0.3667` (1 `success`, 6 `model_failure`).
  - **Ambiguo (5 casos):** Precisión `0.0000`, Cobertura `0.0000`, Pertinencia `0.3000` (0 `success`, 5 `model_failure`).
  - **Fuera de Alcance (3 casos):** Precisión `1.0000`*, Cobertura `1.0000`*, Pertinencia `0.2000` (3 `model_failure`).
  - *\*Nota: Las métricas de 1.0 en fuera de alcance constituyen una convención formal del marco evaluador.*
- **Estado de Incidencias:** `F5-001` CERRADO, `F5-002` MITIGADA, `F5-003` CERRADO.
- **FASE 5 CERRADA FORMALMENTE.**

---

## 4. Estado de los Artefactos Oficiales y Hashes de Trazabilidad

Los resultados oficiales del benchmark de 15 casos se encuentran registrados en Git en el directorio `backend/tests/resultados/`:
- **`eval_results.json`:** `9d9c1b5f80f9cb807a38464f141bb9c01fba201ffae01a8f7eaed8c84be594b1`
- **`eval_results.csv` (normalizado):** `cedf76ded42261ba43d20d90ed4b9dfc87999b07917da6e0eb6072bf0cd88cd5`
- **`golden_set.json` (15 casos):** `736ee36115717130945a3f8902eba4aec93c556a8b14da129c071bdde8b84a75`
- **`golden_set_32_historico.json`:** `e58db793eb82e26d7f0a84e32b9369b725131b2d9513dbcd3fa13fdf036438b1`
- **`golden_set_manifest.json`:** Manifiesto formal de trazabilidad validado por `verify_evaluation_integrity.py`.

---

## 5. Recomendaciones Destacadas para el Paper IEEE

Para la redacción final del **Paper IEEE**, se destacan los siguientes elementos empíricos derivados de la Fase 5:

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. SECCIÓN DE ARQUITECTURA DEL SISTEMA                                     │
│    - Resaltar la separación estricta en Arquitectura Hexagonal entre la    │
│      lógica de tutoría, la capa de persistencia y los adaptadores Gemini.   │
│    - Citar la combinación de RAG con Function Calling en tiempo real con   │
│      el modelo generativo Gemini 3.5 Flash Lite.                            │
├─────────────────────────────────────────────────────────────────────────────┤
│ 2. EXPERIMENTACIÓN Y METODOLOGÍA (EXPERIMENTAL SETUP)                       │
│    - Detallar el marco de evaluación sobre 15 casos estratificados con      │
│      aislamiento transaccional atómico y rate-limiter de 15 segundos.       │
│    - Documentar la separación formal entre errores de infraestructura (0.0%)│
│      y fallos de calidad de modelo (86.67%).                                │
├─────────────────────────────────────────────────────────────────────────────┤
│ 3. RESULTADOS CUANTITATIVOS Y TRABAJO FUTURO                                │
│    - Reportar las métricas de Precisión (33.33%), Cobertura (33.33%) y      │
│      Pertinencia (31.11%), identificando la etapa de recuperación vectorial │
│      como el principal cuello de botella a optimizar en trabajos futuros.   │
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
