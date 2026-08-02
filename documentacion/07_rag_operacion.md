# Pipeline RAG — Operación, parámetros y verificación

> Reemplaza el diseño descrito en `03_pipeline_rag.md`, que documenta la versión
> anterior (chunking por estructura JSON, recuperación con heurísticas léxicas).

---

## 1. Cómo se inicia

El índice vive en la tabla `corpus_chunks` de PostgreSQL con la extensión
`pgvector`. Se construye desde `backend/corpus_estructurado/`, no desde los PDF
directamente.

### Arranque automático (Docker)

`backend/docker-entrypoint.sh` corre antes de uvicorn:

```sh
alembic upgrade head          # esquema
python -m app.bootstrap_data  # admin, roster e índice del RAG
exec uvicorn ...
```

`bootstrap_data.ensure_corpus()` llama a la ingesta incremental. Es seguro
ejecutarla en cada arranque: compara hashes y solo embebe lo que falta. Si la
cuota de Gemini se agota a mitad de camino, la interrupción se captura, lo
indexado queda intacto y el contenedor arranca igual.

Variables de entorno:

| Variable | Efecto |
|---|---|
| `GEMINI_API_KEY` | Sin ella no hay ingesta ni chat |
| `AUTO_BOOTSTRAP=0` | Desactiva toda la siembra (las migraciones igual corren) |
| `AUTO_SEED_CORPUS=0` | Aplica migraciones y usuarios, pero no toca el índice |

### Construcción manual

```bash
# 1. Extraer el articulado desde los PDF oficiales
python -m scripts.extract_pdf_corpus --pdf-dir /ruta/a/los/pdf
python -m scripts.extract_plan_estudios --md .../plan-estudios-2025.md
python -m scripts.extract_calendario  --md .../es_ocr/CRONOGRAMA-2026.md
python -m scripts.extract_malla       --json malla_2017_transcrita.json

# 2. Validar antes de indexar
python -m scripts.validate_corpus --estricto

# 3. Indexar (incremental: solo embebe lo nuevo o lo editado)
python -m scripts.ingest_corpus
python -m scripts.ingest_corpus --forzar   # reembebe todo
```

**Cambiar la API key es inocuo.** Los vectores viven en la base y no llevan
marca de la cuenta: se cambia `GEMINI_API_KEY`, se recrea el contenedor con
`docker compose up -d backend` (un `restart` no recarga variables de entorno) y
la ingesta retoma donde quedó.

**Cambiar el modelo de embeddings no lo es.** Dos modelos producen espacios
vectoriales distintos, así que una distancia entre un fragmento viejo y una
consulta nueva deja de significar algo y la búsqueda empeora sin que nada falle.
Cada chunk registra `modelo_embedding` y la ingesta se niega a continuar ante
una mezcla, indicando cómo reindexar.

---

## 2. Cómo funciona

### 2.1 Corpus

Un documento declara su procedencia y se descompone en **fragmentos**, que son
la unidad de recuperación. El esquema está en
`app/application/dtos/corpus_dtos.py`.

```json
{
  "procedencia": {
    "documento": "Reglamento de Tutoría Académica UNSAAC",
    "tipo": "reglamento",
    "resolucion": "Resolución Nro. CU-0220-2017-UNSAAC de 24.05.2017"
  },
  "fragmentos": [
    {
      "id": "reglamento_tutoria#art-14-1",
      "articulo": "Art. 14",
      "titulo": "Art. 14 - Asignación de Tutores",
      "seccion": ["Capítulo III", "asignacion-de-tutores"],
      "texto": "Reglamento de Tutoría... > Art. 14 - Asignación de Tutores\nEl número de tutorados..."
    }
  ]
}
```

Cada fragmento antepone su ruta jerárquica al texto para ser **autocontenido**:
aislado, `"veinticinco (25) estudiantes"` no se puede recuperar ni citar.

Estado actual: **1009 fragmentos, 14 documentos**.

### 2.2 Indexación

Cada fragmento se embebe con `task_type=RETRIEVAL_DOCUMENT` y se guarda con:

| Columna | Uso |
|---|---|
| `fragment_id` | Identidad estable → ingesta incremental |
| `content_hash` | Si no cambió, el embedding sigue valiendo |
| `documento`, `articulo` | Procedencia citable en la respuesta |
| `autoridad` | Jerarquía de fuente (ver 2.4) |
| `modelo_embedding` | Detección de mezcla de modelos |
| `busqueda_ts` | Columna generada, FTS en español con índice GIN |

### 2.3 Recuperación híbrida

Dos ramas independientes sobre el mismo pool:

- **Vectorial** — `cosine_distance` con índice HNSW. Captura similitud
  semántica aunque no compartan palabras.
- **Léxica** — `plainto_tsquery('spanish', ...)` con índice GIN. Captura
  códigos, números y nombres propios que el embedding diluye, y **lematiza**:
  `matricularse` encuentra `Matrícula`.

Se fusionan con **Reciprocal Rank Fusion**: cada rama aporta `1/(k + posición)`.
Al operar sobre posiciones y no sobre puntajes, no hace falta normalizar una
distancia coseno contra un `ts_rank`, que viven en escalas sin techo común.

La consulta se embebe con `task_type=RETRIEVAL_QUERY`. La búsqueda es
asimétrica: usar el mismo modo para pregunta y documento trata a una consulta
corta y un texto largo como si fueran comparables entre sí.

### 2.4 Reordenamiento por autoridad

La similitud semántica no distingue una norma citable de un resumen no
verificado que dice algo parecido. Medido: ante *"¿qué oficina se encarga del
bienestar?"*, el Art. 245 del Estatuto quedaba en la **posición 15 de 20**,
detrás de cinco fragmentos de paráfrasis, y con `limit=6` nunca llegaba al LLM.

| Nivel | Criterio |
|---|---|
| 3 | Citable por artículo |
| 2 | Documento con resolución declarada |
| 1 | Resto (glosario, FAQ, paráfrasis) |

El factor es multiplicativo sobre el puntaje RRF: reordena entre candidatos
comparables pero no rescata a uno claramente peor. Con el reordenamiento
activo, el Art. 245 pasa a la posición **4**.

### 2.5 Abstención

Dos cortes **en código**, antes de invocar al LLM, para no depender de que el
prompt lo convenza de callarse:

1. **Sin evidencia** — si ninguna rama devuelve fragmentos, se responde el
   mensaje de abstención sin llamar a Gemini.
2. **Institución externa** — si la consulta apunta a otra casa de estudios se
   corta antes de recuperar. Esto no lo resuelve el umbral: *"cuánto cuesta la
   matrícula en la UNSA"* queda a distancia 0.291, más cerca del corpus que
   varias preguntas legítimas, porque semánticamente **sí** es una consulta
   sobre matrícula universitaria. Lo que difiere es la institución.

   Se responde con una **aclaración**, no con una negativa, para que un falso
   positivo cueste un turno y no una consulta válida. Se excluyen los términos
   de vínculo (convenio, intercambio, movilidad, traslado, beca), porque
   movilidad es uno de los dominios del alcance.

---

## 3. Parámetros

Todos en `RAGRetrievalPolicy` (`app/application/dtos/rag_dtos.py`), inyectados
desde `app/infrastructure/api/dependencies.py`.

| Parámetro | Valor | Origen del valor |
|---|---|---|
| `limit` | 6 | Fragmentos entregados al LLM |
| `max_cosine_distance` | **0.34** | **Calibrado** — ver abajo |
| `candidatos_por_rama` | 20 | Candidatos por rama antes de fusionar |
| `rrf_k` | 60 | Constante habitual de RRF |
| `min_ts_rank` | 0.05 | Piso léxico; sin él, *"derivada de una función"* engancha el curso *Cálculo I* |
| `peso_autoridad` | **0.2** | **Calibrado** — ver abajo |
| `keyword_fallback_limit` | 2 | >0 habilita la rama léxica |
| `HISTORY_WINDOW_MESSAGES` | 20 | Tope de historial enviado al LLM |

Modelos: `gemini-embedding-2` a 768 dimensiones (embeddings),
`gemini-3.5-flash-lite` (generación).

### Calibración

Los dos parámetros marcados **no se eligieron a ojo**. Hay un script por cada
uno y sus informes quedan en `backend/tests/resultados/`.

```bash
python -m scripts.calibrar_umbral --set v2
python -m scripts.calibrar_peso_autoridad
```

**Umbral de distancia.** El valor anterior, 0.45, dejaba pasar **las tres**
consultas fuera de alcance y rompía la abstención.

| Umbral | Recall en alcance | Falsos positivos |
|---|---|---|
| 0.29 | 70% | 0 |
| **0.34** | **100%** | 1 |
| 0.45 (anterior) | 100% | 3 |

El único falso positivo a 0.34 es la consulta sobre otra universidad, que
resuelve la guarda institucional y no el umbral.

**Peso de autoridad.** El barrido embebe cada pregunta una sola vez y reutiliza
los vectores para los 11 pesos, así que cuesta lo mismo que una evaluación.

| Peso | Acierto de artículo | Acierto de documento |
|---|---|---|
| 0.0 | 12/16 | 20/20 |
| **0.2** | **15/16** | 20/20 |
| 0.5 → 2.0 | 15/16 | 20/20 |

Se toma 0.2 por ser el menor valor que alcanza el resultado: la menor
intervención sobre el orden que produce la fusión.

---

## 4. Pruebas que pasa

### 4.1 Suite automatizada

**387 pruebas.** Ejecutar desde la raíz del repositorio:

```bash
backend/venv/bin/python -m pytest -q
```

Archivos que cubren el RAG:

| Archivo | Qué protege |
|---|---|
| `test_corpus_schema.py` | Contrato del esquema; solo los reglamentos exigen articulado |
| `test_corpus_ingestion.py` | Conversión, descomposición de dicts grandes, auditoría de cobertura |
| `test_ingest_corpus.py` | Hash, clasificación incremental, orden intercalado, `task_type`, modo estricto, guarda de modelo |
| `test_pdf_extraction.py` | Parseo de articulado, jerarquía, corte de artículos largos |
| `test_plan_estudios.py`, `test_extract_malla.py`, `test_calendario.py` | Extractores tabulares y de OCR |
| `test_validate_malla.py` | Verificación de transcripciones contra invariantes |
| `test_golden_set_v2.py` | Integridad del golden set; artículos inexistentes |
| `test_rag_quality.py` | RRF, índice de texto completo, ponderación por autoridad |
| `test_institucion_externa.py` | Guarda institucional y sus excepciones |
| `test_chat_abstention.py` | Corte por falta de evidencia |
| `test_evaluation_integrity.py` | Hashes del golden set v1 congelado |

Varias pruebas son **regresiones de defectos reales encontrados durante el
trabajo**, no casos hipotéticos: el chunk de 3729 caracteres que diluía nueve
temas, el orden alfabético que dejó un reglamento entero sin indexar, la
palabra clave dispersa que inflaba la cobertura, el `convert_corpus` que pisaba
el articulado.

### 4.2 Evaluación del RAG

```bash
python -m tests.run_eval_v2 --json tests/resultados/fase4_eval_v2.json
```

Contra `golden_set_v2.json` (26 casos, 8 dominios), corpus completo:

```
Acierto de artículo   : 15/16  ( 94%)
Acierto de documento  : 20/20  (100%)
Cobertura de palabras :          93%
Abstención correcta   :  3/3   (100%)
```

| Dominio | artículo | documento |
|---|---|---|
| tutoria | 5/5 | 5/5 |
| apoyos | 3/3 | 3/3 |
| movilidad | 2/2 | 2/2 |
| trayectoria_academica | 4/4 | 5/5 |
| calendario, tramites | — | 3/3 |
| enrutamiento | 1/2 | 2/2 |

El acierto de artículo **era imposible de medir antes**: el golden set siempre
citó `"Art. 15 - Reglamento de Tutoría"`, pero el corpus era una paráfrasis sin
articulado y ninguna respuesta podía satisfacerlo.

El runner reproduce el pipeline completo, incluida la guarda institucional, y
**avisa si hay documentos sin indexar** para que las métricas no se lean fuera
de contexto.

### 4.3 Auditoría de cobertura

Responde si el texto necesario **existe** en el corpus, sin llamar a Gemini.
Define el techo alcanzable: ninguna mejora de recuperación puede superarlo.

```bash
python -m scripts.audit_corpus_coverage --set v2 --corpus corpus_estructurado
```

Mide co-ocurrencia dentro de una misma unidad, no presencia suelta: las
palabras de una consulta pueden aparecer en secciones sin relación entre sí y
dar un falso positivo.

### 4.4 Verificación extremo a extremo

```bash
TOK=$(curl -s -X POST localhost:8000/api/v1/auth/login \
  -d "username=<código>@unsaac.edu.pe&password=<código>" | jq -r .access_token)

curl -s -X POST localhost:8000/api/v1/chat/message \
  -H "Authorization: Bearer $TOK" -H "Content-Type: application/json" \
  -d '{"content":"¿Cuántos estudiantes como máximo puede tener un tutor?"}'
```

Respuesta verificada:

> Según el Reglamento de Tutoría Académica de la UNSAAC, el número de tutorados
> por cada profesor, en la medida de lo posible, no debe superar los
> **veinticinco (25) estudiantes**. Si en algún centro no fuese posible alcanzar
> esta cifra, el límite puede aumentarse o se puede recurrir a docentes becarios
> bajo la supervisión de un profesor ordinario.

Y fuera de alcance:

> No cuento con información suficiente en la base oficial de la UNSAAC para
> responder con certeza.

---

## 5. Limitaciones conocidas

1. **Cuatro casos del golden set esperan documentos** que no están publicados:
   requisitos de beca de comedor, procedimiento de reserva de cupo, bases de
   movilidad OCRI y directiva de subvenciones. Están marcados
   `pendiente_documento` y se excluyen de las métricas, porque contarlos como
   fallo confundiría una brecha documental con un problema de búsqueda.

2. **`servicios_bienestar` y `reglamento_intercambio_estudiantil` no tienen
   fuente verificable.** Su contenido no se pudo contrastar contra ningún
   documento oficial. El reordenamiento por autoridad hace que dejen de
   desplazar al articulado, pero no los vuelve confiables.

3. **`servicios_biblioteca` no tiene articulado.** El PDF está escaneado y el
   OCR corrompe la numeración (`Art 19` por `Art. 1°`, el `°` leído como `9`).
   Citar mal un artículo es peor que no citarlo. Además el documento cita la Ley
   23733, derogada por la Ley 30220 en 2014.

4. **El caso 122** (*"¿a qué oficina voy si tengo un problema económico?"*)
   responde correctamente, pero desde `preguntas_frecuentes` en lugar del ROF o
   el Estatuto: acierta el contenido y falla la cita.

5. **El calendario caduca.** El esquema no tiene ventana de vigencia, así que un
   calendario vencido seguiría respondiéndose como actual. Aplica igual a las
   convocatorias, si se incorporan.
