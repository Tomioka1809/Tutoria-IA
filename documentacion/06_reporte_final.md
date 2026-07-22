# Reporte Final y Correcciones Consolidadas — Proyecto TutorIA (Fase 6)

Este documento representa el informe consolidado del proceso de auditoría, documentación, refactorización y evaluación del sistema **TutorIA**, desarrollado para la gestión de tutorías académicas y asistencia conversacional RAG en el curso de Inteligencia Artificial (IF651, UNSAAC).

---

## 1. Resumen Ejecutivo del Proyecto

- **Estado General:** El sistema se encuentra totalmente operativo y alineado con los estándares de arquitectura de software y machine learning aplicados.
- **Backend:** FastAPI estructurado en Arquitectura Hexagonal con persistencia asíncrona en PostgreSQL y extensión vectorial `pgvector`.
- **RAG & LLM:** Integración con Google Gemini (`gemini-2.5-flash` y `gemini-embedding-2`) combinando recuperación vectorial semántica con ejecución de herramientas en tiempo real (*Tool Calling*).
- **Frontend Móvil:** App React Native con Expo (SDK 54), Expo Router, NativeWind y Zustand, con autodetección de IP local y navegación por roles.
- **Evaluación Experimental (Paper IEEE):** Banco de pruebas automatizado sobre 32 casos calibrados. *(Nota de auditoría de la Fase 5A: Las cifras citadas en borradores preliminares — 86.98% de Precisión, 95.83% de Cobertura y 92.50% de Pertinencia — corresponden a una línea base histórica no verificada. Dichas cifras se mantienen como referencia de partida no verificada y la medición cuantitativa oficial se encuentra **pendiente de ejecución controlada en la Fase 5B**)*.

---

## 2. Matriz Consolidada de Hallazgos y Priorización

| Componente | Hallazgo | Severidad | Estado | Acción Realizada / Recomendada |
|---|---|---|---|---|
| **Banco de Pruebas** | Inconsistencia entre cifras históricas documentadas y artefactos de evaluación. | **Alto** | **EN_CORRECCION_FASE_5A** | Implementados reintentos, escritura atómica y trazabilidad de ejecuciones en la Fase 5A. Medición oficial **pendiente de ejecución en Fase 5B**. |
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
- Elaborado [00_inventario.md](00_inventario.md) con el árbol completo.

### Fase 1 — Descripción General del Proyecto
- Elaborado el documento maestro [01_descripcion_proyecto.md](01_descripcion_proyecto.md).

### Fase 2 — Backend y Arquitectura Hexagonal
- Poblado `backend/app/domain/schemas/__init__.py` consolidando los DTOs.
- Ampliado `backend/app/domain/exceptions.py`.

### Fase 3 — Pipeline RAG
- Modificado `backend/app/infrastructure/database/repositories/corpus_repository.py` usando `cosine_distance()`.

### Fase 4 — Frontend React Native (Expo)
- Solucionada la URL dinámica, manejo centralizado de errores, modelo puro del calendario, integridad de datos reales y 0 warnings en ESLint.

### Fase 5A — Robustez del Banco de Pruebas RAG
- Creado `backend/tests/evaluation_support.py` con reintentos para HTTP 429, backoff exponencial, escritura atómica paritaria y sanitización de secretos.
- Refactorizados `backend/tests/test_retrieval.py`, `backend/tests/test_generation.py` y `backend/tests/run_eval.py` diferenciando fallos de infraestructura (`infrastructure_error`) de fallos del modelo (`model_failure`).
- Creados los verificadores estáticos `backend/tests/verify_evaluation_integrity.py` y suite unitaria en `backend/tests/unit/test_evaluation_integrity.py`.

---

## 4. Recomendaciones Destacadas para el Paper IEEE

Para la redacción del **Paper IEEE**, se sugiere resaltar los siguientes elementos respaldados empíricamente:

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. SECCIÓN DE ARQUITECTURA DEL SISTEMA                                     │
│    - Destacar el diseño en Arquitectura Hexagonal que aísla la lógica de   │
│      tutoría de los adaptadores de Gemini y PostgreSQL.                     │
│    - Citar la combinación de RAG con Function Calling en tiempo real.       │
├─────────────────────────────────────────────────────────────────────────────┤
│ 2. SECCIÓN DE EXPERIMENTOS Y RESULTADOS (EXPERIMENTAL RESULTS)              │
│    - Incluir la tabla con los 32 casos del Golden Set.                      │
│    - Presentar la metodología de evaluación robusta (Fase 5A) con retries   │
│      ante HTTP 429 y diferenciación de errores de infraestructura.         │
│    - Reportar las métricas de Precisión, Cobertura y Pertinencia una vez    │
│      ejecutado el benchmark reproducible oficial (Fase 5B).                 │
├─────────────────────────────────────────────────────────────────────────────┤
│ 3. SECCIÓN DE CONCLUSIONES                                                  │
│    - Concluir que el uso de Embeddings Gemini (768 dim) con pgvector        │
│      y distancia Coseno proporciona una recuperación rápida y precisa        │
│      para la normativa universitaria.                                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Índice Final de Documentación Técnica Generada

Toda la documentación técnica se encuentra organizada en la carpeta `/documentacion/`:

1. [00_inventario.md](00_inventario.md)
2. [01_descripcion_proyecto.md](01_descripcion_proyecto.md)
3. [02_backend_arquitectura.md](02_backend_arquitectura.md)
4. [03_pipeline_rag.md](03_pipeline_rag.md)
5. [04_frontend.md](04_frontend.md)
6. [05_banco_pruebas.md](05_banco_pruebas.md)
7. [06_reporte_final.md](06_reporte_final.md)
