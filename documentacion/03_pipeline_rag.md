# Auditoría y Especificación del Pipeline RAG — TutorIA (Fase 3)

El pipeline de **Retrieval-Augmented Generation (RAG)** constituye el núcleo de inteligencia conversacional del proyecto **TutorIA**, responsable de fundamentar las respuestas del chatbot en la normativa oficial de la UNSAAC.

---

## 1. Mapeo Componente por Componente del Pipeline RAG

```mermaid
graph LR
    subgraph DataIngestion ["1. Ingesta y Chunking"]
        JSONs["9 Archivos JSON (normativa, mallas, servicios)"]
        Prefixer["Enriquecimiento con Prefijos Metadatos"]
        DictToText["Aplanado de JSON (dict_to_text)"]
    end

    subgraph EmbeddingStorage ["2. Embeddings y Almacenamiento"]
        GeminiEmbed["gemini-embedding-001 (768 dim)"]
        PGVector["PostgreSQL + pgvector (corpus_chunks)"]
    end

    subgraph Retrieval ["3. Recuperación"]
        UserQuery["Consulta Usuario (+ Expansión)"]
        QueryVector["Vector de Consulta (768 dim)"]
        TopK["Top-K Retrieval (limit=6)"]
    end

    subgraph Generation ["4. Generación Fundamentada"]
        SystemPrompt["System Prompt (Grounding & Formatting)"]
        FunctionCalling["Tool Calling (Tutores, Eventos)"]
        GeminiFlash["Gemini 2.5 Flash"]
    end

    JSONs --> Prefixer --> DictToText --> GeminiEmbed --> PGVector
    UserQuery --> QueryVector --> TopK --> PGVector
    PGVector --> TopK --> SystemPrompt
    FunctionCalling <--> GeminiFlash
    SystemPrompt --> GeminiFlash
```

---

## 2. Análisis Detallado por Etapas

### 2.1 Chunking (Segmentación de Documentos)
- **Implementación Actual:** En `backend/app/infrastructure/database/seed.py`, los 9 archivos JSON (`reglamento_tutoria.json`, `malla_curricular_2025.json`, etc.) son procesados asignándoles un prefijo descriptivo explícito (ej: `[Reglamento de Tutoría de Estudiantes UNSAAC]`).
- **Puntos Fuertes:** La inyección de metadatos mediante prefijos evita la pérdida de contexto del origen del documento durante la búsqueda vectorial.
- **Puntos Débiles:** No existe un algoritmo dinámico de *sliding window* (solapamiento/overlap) ni particionado estricto por tamaño de tokens. Los JSONs anidados se aplanan con `dict_to_text()`, lo que puede generar chunks de tamaño heterogéneo si una sección es muy extensa.

### 2.2 Embeddings (Representación Vectorial)
- **Implementación Actual:** Se utiliza el SDK `google-genai` en `GeminiAdapter.compute_embedding()`.
- **Modelo:** `gemini-embedding-001` configurado con `output_dimensionality=768`.
- **Observación:** El prompt general menciona `text-embedding-004`. Aunque ambos modelos de Google AI Studio operan nativamente a 768 dimensiones y son compatibles con la columna `Vector(768)` de `pgvector`, conviene unificar la nomenclatura en código y documentación.

### 2.3 Almacenamiento Vectorial (`pgvector` en PostgreSQL)
- **Esquema:** Tabla `corpus_chunks` con columna `embedding VECTOR(768)`.
- **Métrica de Búsqueda Actual:** En `CorpusRepository.search_similar()`, se consulta utilizando la distancia euclidiana L2 (`.l2_distance()` o operador `<->`).
- **Crítica Técnica:** Para modelos de embedding conversacionales como los de Gemini, la **distancia coseno (`cosine_distance` / `<=>`)** es matemáticamente superior para medir la similitud semántica.
- **Índice Vectorial:** La migración Alembic `f9995a19c833_add_pgvector_and_corpuschunk.py` no crea un índice vectorial (`HNSW` o `IVFFlat`). Actualmente se realiza una búsqueda secuencial exacta (Exact Nearest Neighbors).

### 2.4 Recuperación (*Retrieval*)
- **Top-K:** Fijado en `limit = 6` en `ChatUseCase.send_chat_message()`.
- **Umbral de Similitud (*Score Threshold*):** **Inexistente**. La consulta siempre recupera los 6 fragmentos más cercanos sin verificar si la distancia supera un valor de corte (ej: cosine similarity >= 0.65).
- **Riesgo:** Cuando el usuario realiza una pregunta ajena a la normativa (ej. sobre fútbol o recetas), el sistema inyecta 6 fragmentos irrelevantes al prompt en lugar de pasar un contexto vacío.

### 2.5 Generación y Grounding (*Gemini 2.5 Flash*)
- **Inyección de Contexto:** Los 6 fragmentos se unen con salto de línea doble y se inyectan en `system_instruction`.
- **Directivas de Grounding:** El prompt incluye reglas de concisión y uso de emojis (máximo 2), así como directivas de fecha para semestres (2026-I / 2026-II).
- **Política de Fallback:** La Regla 6 del prompt autoriza al modelo a responder "según internet..." si no encuentra la respuesta en el corpus. Esto relaja el *grounding* y puede propiciar alucinaciones fuera del reglamento.

---

## 3. Tabla de Hallazgos y Acciones Recomendadas

| Componente | Hallazgo | Severidad | Acción / Corrección Propuesta |
|---|---|---|---|
| **Almacenamiento (Métrica)** | Se usa distancia L2 (`l2_distance`) en lugar de distancia Coseno (`cosine_distance`) para la búsqueda vectorial. | Media | Cambiar `.l2_distance()` a `.cosine_distance()` en `CorpusRepository.search_similar()`. |
| **Almacenamiento (Índice)** | No existe índice `HNSW` en PostgreSQL `pgvector`, provocando búsquedas por escaneo secuencial. | Media | Crear migración de Alembic o script SQL ejecutando `CREATE INDEX ON corpus_chunks USING hnsw (embedding vector_cosine_ops)`. |
| **Recuperación (Umbral)** | Ausencia de *Score Threshold*. Siempre se inyectan 6 fragmentos independientemente de su relevancia. | Alta | Implementar filtro por distancia/similitud mínima (ej. `distance <= 0.45`) antes de inyectar contexto. |
| **Generación (Grounding)** | La regla 6 del prompt permite usar "conocimientos generales e internet", aumentando el riesgo de alucinaciones normativas. | Media | Ajustar la regla 6 para forzar un mensaje de abstención estricto cuando la consulta sea sobre reglamentos pero no esté en la base oficial. |
| **Chunking** | Falta de segmentación por límites semánticos estándar (artículos/incisos) y tamaño de tokens uniforme. | Media | Refactorizar el parser de `seed.py` para crear chunks estructurados por Artículos con solapamiento (*overlap*) de 100 tokens. |

---

## 4. Plan de Optimización Inmediata para el Paper IEEE

Para garantizar que el banco de pruebas (Fase 5) mida la máxima precisión del RAG:
1. **Ajuste de Métrica:** Modificar `CorpusRepository` para usar distancia coseno.
2. **Filtrado por Umbral:** Establecer un umbral de similitud en la recuperación para descartar ruido.
3. **Refuerzo del Grounding:** Modificar la instrucción del sistema para que Gemini no invente normativas no documentadas.
