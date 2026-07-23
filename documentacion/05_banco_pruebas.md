# Banco de Pruebas y Suite de Evaluación RAG — TutorIA (Fase 5)

Este documento describe la metodología de evaluación, la migración desde el banco histórico de 32 casos hacia el **Golden Dataset Oficial de 15 casos estratificados**, el manifiesto de trazabilidad, la especificación de métricas (**Precisión, Cobertura y Pertinencia**), y las salvaguardas de integridad de la **Fase 5C**.

> ⚠️ **ADVERTENCIA DE LÍNEA BASE HISTÓRICA E INTEGRIDAD DE DATOS:**
> Los 32 casos originales han sido migrados formalmente al banco histórico `backend/tests/dataset/golden_set_32_historico.json` y sus resultados anteriores han sido archivados en `backend/tests/resultados/historico_32/` preservando sus hashes SHA-256 históricos obligatorios. El **benchmark oficial definitivo de la Fase 5C utiliza 15 casos estratificados** en `backend/tests/dataset/golden_set.json` evaluados con el modelo generativo activo **`gemini-3.5-flash-lite`** y el modelo de embedding **`gemini-embedding-2`**. Las métricas históricas de 32 casos no son directamente comparables con las métricas del nuevo benchmark de 15 casos.

---

## 1. Metodología de Evaluación y Redefinición de Alcance

El suite de pruebas evalúa el desempeño del sistema RAG en dos etapas consecutivas:

1. **Evaluación de Recuperación Vectorial (*Retrieval*):** Mide la capacidad de `pgvector` y del modelo de embedding activo (`gemini-embedding-2`, 768 dim) para recuperar los fragmentos relevantes del corpus normativo de la UNSAAC.
2. **Evaluación de Generación y Grounding (*Generation & LLM*):** Mide la capacidad del modelo generativo activo `gemini-3.5-flash-lite` (modelo anterior: `gemini-2.5-flash`) para generar respuestas precisas, fundamentadas en el reglamento, sin alucinaciones y respetando la política de abstención en preguntas fuera de dominio.

```mermaid
graph LR
    Manifest["Manifiesto Trazabilidad (golden_set_manifest.json)"] --> GoldenSet["Golden Dataset Oficial (15 Casos)"]
    GoldenSet --> TestRetrieval["test_retrieval.py (pgvector Search)"]
    GoldenSet --> TestGeneration["test_generation.py (ChatUseCase + Gemini 3.5 Flash Lite)"]
    TestRetrieval --> RunEval["run_eval.py (Rate-Limiter 15s + Atomic Pair Write)"]
    TestGeneration --> RunEval
    RunEval --> ExportJSON["resultados/eval_results.json (Formato Atómico)"]
    RunEval --> ExportCSV["resultados/eval_results.csv (Formato Atómico)"]
```

---

## 2. Composición del Golden Set Oficial (15 Casos) y Trazabilidad

El benchmark oficial definitivo utiliza un muestreo sistemático estratificado determinista sobre el banco histórico original, conservando los IDs originales de cada caso:

- **Distribución Oficial por Categorías (15 Casos):**
  - **Casos Fáciles (7 casos):** IDs `{1, 3, 6, 8, 10, 13, 15}`. Consultas directas sobre el Reglamento de Tutoría, cronogramas y mallas curriculares.
  - **Casos Ambiguos (5 casos):** IDs `{16, 18, 20, 23, 25}`. Consultas complejas con múltiples condiciones (cambio de tutor, convalidaciones, faltas).
  - **Casos Fuera de Alcance (3 casos):** IDs `{26, 29, 32}`. Consultas ajenas a la universidad donde el bot debe abstenerse.

- **Manifiesto de Trazabilidad (`golden_set_manifest.json`):**
  - **`official_case_count`:** 15
  - **`historical_case_count`:** 32
  - **`selection_method`:** `"muestreo_sistematico_estratificado_determinista"`
  - **`historical_golden_set_sha256`:** `e58db793eb82e26d7f0a84e32b9369b725131b2d9513dbcd3fa13fdf036438b1`
  - **`official_golden_set_sha256`:** `736ee36115717130945a3f8902eba4aec93c556a8b14da129c071bdde8b84a75`
  - **`models`:** `{"generation": "gemini-3.5-flash-lite", "embedding": "gemini-embedding-2"}`

---

## 3. Estado de Incidencias y Mitigación

- **Hallazgo `F5-001` (Trazabilidad y Robustez):** **`RESUELTO_TECNICAMENTE_EN_FASE_5C / PENDIENTE_CIERRE_CUANTITATIVO_EN_FASE_5D`**. La infraestructura técnica está preparada (modo estricto sin fallbacks silenciosos, retries de capa única, rate-limiter de 15s por solicitud real de generación, sanitización de logs técnicos, escritura conjuntamente atómica de JSON y CSV, y aislamiento atómico por usuario temporal determinista). La ejecución oficial del benchmark de 15 casos pertenece a la Fase 5C; mientras que el análisis cuantitativo y el cierre definitivo pertenecerán a la Fase 5D.
- **Incidencia `F5-002` (Interrupción por Cuota Externa 429):** **`MITIGADA_POR_REDEFINICION_FORMAL_DEL_ALCANCE`**. Sirve como evidencia histórica de la interrupción de la corrida masiva previa por errores HTTP 429 `RESOURCE_EXHAUSTED`. No se determinó un límite diario fijo mediante pruebas locales y los resultados parciales de 32 fueron descartados. La nueva ejecución oficial comenzará desde cero sobre el dataset estratificado de 15 casos. La política de reintentos utiliza backoff exponencial acotado.
- **Incidencia `F5-003` (Indisponibilidad del Modelo Generativo Anterior):** **`RESUELTO_TECNICAMENTE_POR_MIGRACION_A_GEMINI_3_5_FLASH_LITE / PENDIENTE_VALIDACION_EN_BENCHMARK_5C`**. La primera ejecución del benchmark oficial de 15 casos no pudo completarse porque el proyecto nuevo recibió HTTP 404 `NOT_FOUND` indicando que `gemini-2.5-flash` ya no estaba disponible para usuarios nuevos. La corrida fue interrumpida inmediatamente, no generó métricas oficiales, los resultados activos fueron retirados, los hashes protegidos permanecieron intactos y no quedaron usuarios temporales residuales. Se migró el modelo generativo activo a `gemini-3.5-flash-lite`, disponiendo de mayor margen operativo para el benchmark. La corrida oficial comenzará desde cero en la Fase 5C y la Fase 5D aún no ha comenzado.

---

## 4. Clasificación de Resultados y Distinción de Fallos

Para prevenir que un fallo técnico contamine las métricas del sistema, la **Fase 5C** formaliza cuatro estados deterministas de ejecución por caso:

- **`success`:** El caso fue procesado exitosamente y la respuesta o recuperación cumplió los criterios de evaluación.
- **`model_failure`:** El caso fue procesado sin errores de infraestructura y el modelo respondió, pero la respuesta incumplió el criterio normativo (cobertura cero y pertinencia $\le 0.3$ en dentro de alcance, o falta de mensaje de abstención en fuera de alcance).
- **`infrastructure_error`:** Ocurrió un fallo técnico no recuperable (red, base de datos, agotamiento de cuotas HTTP 429, timeout o error 5xx). **Los errores de infraestructura no se convierten en precisión/cobertura/pertinencia cero**; se excluyen del cálculo de promedios globales.
- **`skipped`:** El caso fue omitido explícitamente debido a un filtro de prueba (`EVAL_CASE_LIMIT` o `EVAL_CASE_IDS`).

---

## 5. Definición y Fórmulas de las Métricas

| Métrica | Qué Mide | Definición Matemática / Heurística Léxica |
|---|---|---|
| **Precisión** | De los fragmentos recuperados en el Top-K ($K=6$), qué proporción contiene palabras clave o referencias esperadas. En consultas fuera de alcance, es 1.0. | $$\text{Precisión} = \frac{\text{Fragmentos Relevantes Recuperados}}{K_{\text{totales}}}$$ |
| **Cobertura** | De los artículos o temas del reglamento esperados (`expected_refs`), qué porcentaje fue efectivamente extraído por la búsqueda de `pgvector`. | $$\text{Cobertura} = \frac{\text{Artículos de Referencia Recuperados}}{\text{Total de Artículos Esperados}}$$ |
| **Pertinencia (*Grounding Léxico*)** | Heurística léxica que mide la presencia de palabras clave esperadas ($70\%$) y validez del tamaño del texto ($30\%$). En consultas fuera de alcance, evalúa la presencia de frases de abstención ($1.0$ si se abstiene, $0.2$ si alucina). | $$\text{Pertinencia} = 0.7 \times \text{Match}_{\text{kw}} + 0.3 \times \text{ValidezTexto}$$ |

> **Nota:** Las métricas globales se calculan promediando **exclusivamente** los casos evaluables con estado `success` o `model_failure`.

---

## 6. Reintentos Controlados, Filtros, Escritura Atómica y Verificación

- **Definición de Ejecución Parcial:** Cualquier presencia de los filtros `EVAL_CASE_LIMIT` o `EVAL_CASE_IDS` define automáticamente una ejecución parcial (`is_partial = True`), **incluso si el filtro contiene los 15 IDs oficiales**. Toda ejecución parcial exige `EVAL_OUTPUT_DIR` y finaliza con `is_complete = False`.
- **Escritura Atómica Paritaria (`atomic_write_artifact_pair`):** Escribe conjuntamente JSON y CSV usando temporales `.tmp` y respaldos `.bak`. Si ocurre un fallo en cualquier etapa o reemplazo, **ambos archivos originales se restauran conjuntamente**.
- **Verificador de Integridad (`verify_evaluation_integrity.py`):** Valida el manifiesto, los archivos históricos archivados en `historico_32/`, el Golden Set oficial de 15 casos, la coincidencia de métricas dentro de la tolerancia 0.0001, la presencia del modelo activo `gemini-3.5-flash-lite` y distingue el estado pendiente previo a la corrida oficial.

---

## 7. Instrucciones para la Ejecución del Benchmark Oficial (15 Casos)

- **Fase 5A:** Completada (Infraestructura, retries y verificadores estáticos).
- **Fase 5B:** Completada (Ejecución parcial controlada completada sobre los casos 1, 16 y 26, con tres casos procesados, cero errores de infraestructura, artefactos temporales y cero usuarios temporales residuales).
- **Fase 5C:** Infraestructura técnica preparada y validada localmente con `gemini-3.5-flash-lite`, con el benchmark oficial de 15 casos pendiente de ejecución en la Fase 5C.
- **Fase 5D:** Análisis cuantitativo, actualización documental y cierre pendientes de la Fase 5D (la Fase 5D comenzará después de obtener los resultados oficiales de 5C).

Para ejecutar la verificación y el benchmark cuando esté disponible el entorno:

```bash
# 1. Ejecutar el verificador estático de integridad (sin Gemini ni DB):
PYTHONPATH=backend backend/venv/bin/python backend/tests/verify_evaluation_integrity.py

# 2. Ejecutar la suite de pruebas unitarias del evaluador (al menos 127 pruebas locales aprobadas):
PYTHONPATH=backend backend/venv/bin/python -m pytest -q backend/tests/unit/test_evaluation_integrity.py backend/tests/unit/test_rag_quality.py backend/tests/unit/test_chat_use_cases.py

# 3. Ejecutar el benchmark oficial de 15 casos (cuando el entorno lo autorice):
PYTHONPATH=backend backend/venv/bin/python backend/tests/run_eval.py
```
