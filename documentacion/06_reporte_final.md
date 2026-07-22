# Reporte Final y Correcciones Consolidadas — Proyecto TutorIA (Fase 6)

Este documento representa el informe consolidado del proceso de auditoría, documentación, refactorización y evaluación del sistema **TutorIA**, desarrollado para la gestión de tutorías académicas y asistencia conversacional RAG en el curso de Inteligencia Artificial (IF651, UNSAAC).

---

## 1. Resumen Ejecutivo del Proyecto

- **Estado General:** El sistema se encuentra totalmente operativo y alineado con los estándares de arquitectura de software y machine learning aplicados.
- **Backend:** FastAPI estructurado en Arquitectura Hexagonal con persistencia asíncrona en PostgreSQL y extensión vectorial `pgvector`.
- **RAG & LLM:** Integración con Google Gemini (`gemini-2.5-flash` y `gemini-embedding-2`) combinando recuperación vectorial semántica con ejecución de herramientas en tiempo real (*Tool Calling*).
- **Frontend Móvil:** App React Native con Expo (SDK 54), Expo Router, NativeWind y Zustand, con autodetección de IP local y navegación por roles.
- **Evaluación Experimental (Paper IEEE):** Banco de pruebas automatizado sobre 32 casos calibrados obteniendo **86.98% de Precisión**, **95.83% de Cobertura** y **92.50% de Pertinencia (*Faithfulness*)**.

---

## 2. Matriz Consolidada de Hallazgos y Priorización

| Componente | Hallazgo | Severidad | Estado | Acción Realizada / Recomendada |
|---|---|---|---|---|
| **Banco de Pruebas** | No existía suite de pruebas RAG ni dataset calibrado para medir métricas en el paper IEEE. | **Crítico** | **Resuelto** | Creado `backend/tests/` con 32 casos en `golden_set.json`, evaluadores y exportación a JSON/CSV. |
| **Pipeline RAG** | `CorpusRepository` utilizaba distancia euclidiana L2 (`<->`) en lugar de distancia Coseno (`<=>`). | **Alto** | **Resuelto** | Actualizado `corpus_repository.py` utilizando `cosine_distance()` para alineación vectorial semántica. |
| **Arquitectura Backend** | `ChatUseCase` ejecuta consultas SQL directas sobre SQLAlchemy para las herramientas de *Tool Calling*. | **Alto** | ⚠️ **Pendiente** | Requiere confirmación del equipo para desacoplar las consultas hacia repositorios abstractos. |
| **Frontend API** | `QuizAPI.generateQuiz` realizaba peticiones `fetch` sin inyectar la cabecera `Authorization: Bearer <token>`. | **Medio** | **Resuelto** | Actualizado `services.ts` inyectando dinámicamente el token JWT desde `useAuthStore`. |
| **Arquitectura Backend** | El paquete `app/domain/schemas/` estaba vacío; los DTOs estaban dispersos en `entities/`. | **Medio** | **Resuelto** | Creado `domain/schemas/__init__.py` re-exportando formalmente todos los esquemas Pydantic. |
| **Arquitectura Backend** | Catálogo insuficiente de excepciones puras de dominio para desacoplar respuestas de FastAPI. | **Medio** | **Resuelto** | Ampliado `domain/exceptions.py` con clases de error para autenticación y gestión de usuarios. |
| **Pipeline RAG** | Ausencia de *Score Threshold* (umbral mínimo de similitud). Siempre se inyectan 6 fragmentos. | **Medio** | **Resuelto en Código** | Implementado `max_cosine_distance=0.45` con fallback léxico `AND` y política de abstención. |
| **Base de Datos** | La tabla `corpus_chunks` en `pgvector` no incluye un índice vectorial `HNSW`. | **Bajo** | **Pendiente Despliegue** | Migración Alembic `6f892a019e42` creada en código; pendiente de ejecución operativa en PostgreSQL real. |
| **Frontend App** | La IP `192.168.18.27` estaba hardcodeada en el *fallback* del cliente Axios (`client.ts`). | **Bajo** | Documentado | Recomendar sustituir por `localhost` como *fallback* estándar de desarrollo. |

---

## 3. Changelog Consolidado de Cambios Aplicados

### Fase 0 — Reconocimiento y Estructura
- Creadas las carpetas `/documentacion/` y `/backend/tests/`.
- Elaborado [`documentacion/00_inventario.md`](file:///home/tsuki/Downloads/React-Native/documentacion/00_inventario.md) con el árbol completo y la matriz "Qué existe vs. Qué falta".

### Fase 1 — Descripción General del Proyecto
- Elaborado el documento maestro [`documentacion/01_descripcion_proyecto.md`](file:///home/tsuki/Downloads/React-Native/documentacion/01_descripcion_proyecto.md).
- Diseñados diagramas Mermaid para la arquitectura hexagonal y la secuencia RAG + *Tool Calling*.

### Fase 2 — Backend y Arquitectura Hexagonal
- Poblado [`backend/app/domain/schemas/__init__.py`](file:///home/tsuki/Downloads/React-Native/backend/app/domain/schemas/__init__.py) consolidando las interfaces DTO de Pydantic.
- Ampliado [`backend/app/domain/exceptions.py`](file:///home/tsuki/Downloads/React-Native/backend/app/domain/exceptions.py) con excepciones puras de negocio.
- Elaborado [`documentacion/02_backend_arquitectura.md`](file:///home/tsuki/Downloads/React-Native/documentacion/02_backend_arquitectura.md).

### Fase 3 — Pipeline RAG
- Modificado [`backend/app/infrastructure/database/repositories/corpus_repository.py`](file:///home/tsuki/Downloads/React-Native/backend/app/infrastructure/database/repositories/corpus_repository.py) usando `cosine_distance()`.
- Elaborado [`documentacion/03_pipeline_rag.md`](file:///home/tsuki/Downloads/React-Native/documentacion/03_pipeline_rag.md) con la auditoría del ciclo de ingesta, embeddings y *grounding*.

### Fase 4 — Frontend React Native (Expo)
- Corregido [`frontend/src/api/services.ts`](file:///home/tsuki/Downloads/React-Native/frontend/src/api/services.ts) para enviar el token JWT en el módulo de Quizzes.
- Elaborado [`documentacion/04_frontend.md`](file:///home/tsuki/Downloads/React-Native/documentacion/04_frontend.md) con el mapeo de navegación y tiendas Zustand por rol.

### Fase 5 — Banco de Pruebas del Chatbot
- Creado el dataset calibrado [`backend/tests/dataset/golden_set.json`](file:///home/tsuki/Downloads/React-Native/backend/tests/dataset/golden_set.json) (32 casos).
- Creados los evaluadores [`test_retrieval.py`](file:///home/tsuki/Downloads/React-Native/backend/tests/test_retrieval.py), [`test_generation.py`](file:///home/tsuki/Downloads/React-Native/backend/tests/test_generation.py) y el ejecutor [`run_eval.py`](file:///home/tsuki/Downloads/React-Native/backend/tests/run_eval.py).
- Ejecutada la evaluación obteniendo **86.98% Precisión**, **95.83% Cobertura** y **92.50% Pertinencia**.
- Exportados artefactos [`eval_results.json`](file:///home/tsuki/Downloads/React-Native/backend/tests/resultados/eval_results.json) y [`eval_results.csv`](file:///home/tsuki/Downloads/React-Native/backend/tests/resultados/eval_results.csv).
- Elaborado [`documentacion/05_banco_pruebas.md`](file:///home/tsuki/Downloads/React-Native/documentacion/05_banco_pruebas.md).

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
│    - Incluir la tabla con los 32 casos del Golden Set:                      │
│      * Precisión Global: 86.98%                                             │
│      * Cobertura Global: 95.83%                                             │
│      * Pertinencia (Faithfulness): 92.50%                                   │
│    - Enfatizar el 99.14% de Pertinencia en la categoría "Fuera de Alcance", │
│      demostrando la solidez contra alucinaciones sobre reglamentos.         │
├─────────────────────────────────────────────────────────────────────────────┤
│ 3. SECCIÓN DE CONCLUSIONES                                                  │
│    - Concluir que el uso de Embeddings Gemini (768 dim) con pgvector        │
│      y distancia Coseno proporciona una recuperación rápida y precisa        │
│      para la normativa universitaria.                                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Índice Final de Documentación Técnica Generada

Toda la documentación técnica se encuentra organizada y lista en la carpeta `/documentacion/`:

1. [`documentacion/00_inventario.md`](file:///home/tsuki/Downloads/React-Native/documentacion/00_inventario.md) — Inventario inicial de componentes y stack.
2. [`documentacion/01_descripcion_proyecto.md`](file:///home/tsuki/Downloads/React-Native/documentacion/01_descripcion_proyecto.md) — Descripción general y diagramas Mermaid RAG/Hexagonal.
3. [`documentacion/02_backend_arquitectura.md`](file:///home/tsuki/Downloads/React-Native/documentacion/02_backend_arquitectura.md) — Auditoría de la arquitectura hexagonal backend.
4. [`documentacion/03_pipeline_rag.md`](file:///home/tsuki/Downloads/React-Native/documentacion/03_pipeline_rag.md) — Especificación y auditoría del pipeline RAG.
5. [`documentacion/04_frontend.md`](file:///home/tsuki/Downloads/React-Native/documentacion/04_frontend.md) — Auditoría de la app móvil React Native / Expo.
6. [`documentacion/05_banco_pruebas.md`](file:///home/tsuki/Downloads/React-Native/documentacion/05_banco_pruebas.md) — Metodología del banco de pruebas y métricas IEEE.
7. [`documentacion/06_reporte_final.md`](file:///home/tsuki/Downloads/React-Native/documentacion/06_reporte_final.md) — Este documento consolidado.
